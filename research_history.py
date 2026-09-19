"""Governed research-history / pre-roll contract for TrendFoll.

R2 readiness remains the universe authority. Stock history is read from the
ussy-data full-history objects at ``history/ohlcv/{security_id}.parquet``.
Pre-roll rows initialize features only; research outcomes must be restricted to
``research_eligible == True``.

This module changes data/feature initialization only. It does not tune signal,
entry, exit, Investability, Tradability, or alert thresholds.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

import feature_engine as fe
from r2_ready import load_ready_dataset, make_r2_client

HISTORY_PREFIX = "history/ohlcv/"
HISTORY_COLUMNS = [
    "date", "security_id", "ticker", "open", "high", "low", "close",
    "adj_close", "volume",
]
CANONICAL_EMA_PERIODS = (20, 50, 150, 200)
CANONICAL_EMA_PRICE_BASIS = "adj_close"
# Conservative initialization boundary already used by governed long-history
# TrendFoll comparisons. This is an engineering warm-up, not an optimized rule.
DEFAULT_MIN_PREROLL_BARS = 500


@dataclass(frozen=True)
class ResearchHistoryReport:
    ready_snapshot_date: str | None
    requested_securities: int
    loaded_securities: int
    history_rows: int
    evaluation_start: str | None
    evaluation_end: str | None
    min_preroll_bars: int
    eligible_rows: int
    eligible_securities: int
    source_prefix: str = HISTORY_PREFIX
    universe_authority: str = "R2 production/ready/current.json"
    stock_history_source: str = "R2 history/ohlcv/{security_id}.parquet"
    ema_price_basis: str = CANONICAL_EMA_PRICE_BASIS


def _normalize_date(value) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts.normalize()


def _validate_history_frame(frame: pd.DataFrame, security_id: str, ticker: str) -> pd.DataFrame:
    missing = set(HISTORY_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Research history {security_id} missing columns: {sorted(missing)}")

    out = frame[HISTORY_COLUMNS].copy()
    out["security_id"] = out["security_id"].astype(str)
    out["ticker"] = out["ticker"].astype(str)
    if set(out["security_id"].dropna().unique()) != {str(security_id)}:
        raise ValueError(f"Research history security_id mismatch for {security_id}")
    if set(out["ticker"].dropna().unique()) != {str(ticker)}:
        raise ValueError(f"Research history ticker mismatch for {security_id}: expected {ticker}")

    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    if out["date"].isna().any() or out.duplicated(["security_id", "date"]).any():
        raise ValueError(f"Research history has null/duplicate dates for {security_id}")

    for column in ["open", "high", "low", "close", "adj_close"]:
        out[column] = pd.to_numeric(out[column], errors="raise").astype("float64")
    out["volume"] = pd.to_numeric(out["volume"], errors="raise")
    numeric = ["open", "high", "low", "close", "adj_close", "volume"]
    if not np.isfinite(out[numeric].to_numpy()).all():
        raise ValueError(f"Research history contains non-finite values for {security_id}")
    if (out[["open", "high", "low", "close", "adj_close"]] <= 0).any().any():
        raise ValueError(f"Research history contains non-positive prices for {security_id}")
    if (out["high"] < out["low"]).any():
        raise ValueError(f"Research history high < low for {security_id}")

    return out.sort_values("date").reset_index(drop=True)


def load_research_history(
    security_ids: Iterable[str] | None = None,
    *,
    evaluation_start=None,
    evaluation_end=None,
    min_preroll_bars: int = DEFAULT_MIN_PREROLL_BARS,
    ready: pd.DataFrame | None = None,
    ready_manifest: dict | None = None,
    s3=None,
    bucket: str | None = None,
) -> tuple[pd.DataFrame, ResearchHistoryReport]:
    """Load governed full stock history and mark evaluation-eligible rows.

    ``research_eligible`` is true only after ``min_preroll_bars`` prior rows are
    available for that security and the row falls inside the requested
    evaluation window. Consumers must filter on this flag *after* computing
    features on the full preceding history.
    """
    if min_preroll_bars < max(CANONICAL_EMA_PERIODS):
        raise ValueError("min_preroll_bars must be >= 200")

    if ready is None or ready_manifest is None:
        ready, ready_manifest = load_ready_dataset(s3=s3, bucket=bucket)
    ready = ready.copy()
    ready["security_id"] = ready["security_id"].astype(str)

    authority = ready[["security_id", "ticker"]].drop_duplicates().sort_values(["security_id", "ticker"])
    if authority["security_id"].duplicated().any():
        raise ValueError("Ready universe maps one security_id to multiple tickers")

    allowed = dict(zip(authority["security_id"], authority["ticker"].astype(str)))
    requested = list(allowed) if security_ids is None else [str(x) for x in security_ids]
    if len(set(requested)) != len(requested):
        raise ValueError("Duplicate security_id requested")
    unknown = sorted(set(requested) - set(allowed))
    if unknown:
        raise ValueError(f"Requested securities are outside R2 readiness universe: {unknown[:10]}")

    start = _normalize_date(evaluation_start)
    end = _normalize_date(evaluation_end)
    if start is not None and end is not None and start > end:
        raise ValueError("evaluation_start must be <= evaluation_end")

    s3 = s3 or make_r2_client()
    if bucket is None:
        import os
        bucket = os.environ.get("R2_BUCKET_NAME", "ussy-data")

    frames: list[pd.DataFrame] = []
    for sid in requested:
        key = f"{HISTORY_PREFIX}{sid}.parquet"
        body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        history = _validate_history_frame(pd.read_parquet(io.BytesIO(body)), sid, allowed[sid])
        if end is not None:
            history = history.loc[history["date"] <= end].copy()
        if history.empty:
            raise ValueError(f"No history remains inside evaluation horizon for {sid}")
        history["bar_age"] = np.arange(1, len(history) + 1, dtype="int64")
        eligible = history["bar_age"] > int(min_preroll_bars)
        if start is not None:
            eligible &= history["date"] >= start
        if end is not None:
            eligible &= history["date"] <= end
        history["research_eligible"] = eligible.astype(bool)
        frames.append(history)

    combined = pd.concat(frames, ignore_index=True).sort_values(["security_id", "date"]).reset_index(drop=True)
    eligible_frame = combined.loc[combined["research_eligible"]]
    report = ResearchHistoryReport(
        ready_snapshot_date=ready_manifest.get("snapshot_date"),
        requested_securities=len(requested),
        loaded_securities=int(combined["security_id"].nunique()),
        history_rows=len(combined),
        evaluation_start=None if start is None else str(start.date()),
        evaluation_end=None if end is None else str(end.date()),
        min_preroll_bars=int(min_preroll_bars),
        eligible_rows=len(eligible_frame),
        eligible_securities=int(eligible_frame["security_id"].nunique()),
    )
    return combined, report


def to_feature_contract(history: pd.DataFrame) -> pd.DataFrame:
    out = history.rename(columns={
        "ticker": "symbol",
        "open": "open_raw",
        "high": "high_raw",
        "low": "low_raw",
        "close": "close_raw",
        "adj_close": "close_adj",
        "volume": "volume_raw",
    }).copy()
    out["dividends"] = 0.0
    out["stock_splits"] = 0.0
    return out[
        ["date", "security_id", "symbol", "open_raw", "high_raw", "low_raw",
         "close_raw", "close_adj", "volume_raw", "dividends", "stock_splits",
         "bar_age", "research_eligible"]
    ].sort_values(["symbol", "date"]).reset_index(drop=True)


def apply_canonical_research_ema(features: pd.DataFrame) -> pd.DataFrame:
    """Replace only EMA semantics with the canonical production basis."""
    out = features.sort_values(["symbol", "date"]).copy()
    for period in CANONICAL_EMA_PERIODS:
        out[f"ema{period}"] = out.groupby("symbol", sort=False)["close_adj"].transform(
            lambda s, p=period: s.ewm(span=p, adjust=False).mean()
        )
    out["ema_stack_aligned"] = (
        (out["close_adj"] > out["ema20"])
        & (out["ema20"] > out["ema50"])
        & (out["ema50"] > out["ema150"])
        & (out["ema150"] > out["ema200"])
    )
    return out


def build_research_feature_store(history: pd.DataFrame, *, sector_map: pd.DataFrame | None = None) -> dict:
    """Build features on full preceding history, then retain eligibility mask."""
    raw = to_feature_contract(history)
    raw["date"] = pd.to_datetime(raw["date"]).astype("datetime64[ns]")
    universe = sorted(raw["symbol"].unique().tolist())
    if sector_map is None:
        sector_map = pd.DataFrame({
            "symbol": universe,
            "sector": [None] * len(universe),
            "industry": [None] * len(universe),
            "sector_benchmark": [None] * len(universe),
        })

    engine_raw = raw.drop(columns=["security_id", "bar_age", "research_eligible"])
    eligibility = raw[["symbol", "date", "security_id", "bar_age", "research_eligible"]].copy()

    original_download_universe = fe.download_universe
    original_download_raw_ohlcv = fe.download_raw_ohlcv
    original_earnings = fe.compute_days_to_next_earnings

    def _download_raw_ohlcv_ns(*args, **kwargs):
        df = original_download_raw_ohlcv(*args, **kwargs)
        if not df.empty and "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
        return df

    try:
        fe.download_universe = lambda symbols: engine_raw.copy()
        fe.download_raw_ohlcv = _download_raw_ohlcv_ns
        fe.compute_days_to_next_earnings = lambda *args, **kwargs: None
        built = fe.build_feature_store(universe, sector_map=sector_map)
    finally:
        fe.download_universe = original_download_universe
        fe.download_raw_ohlcv = original_download_raw_ohlcv
        fe.compute_days_to_next_earnings = original_earnings

    features = built["features"].copy()
    features["date"] = pd.to_datetime(features["date"]).dt.tz_localize(None).dt.normalize()
    eligibility["date"] = pd.to_datetime(eligibility["date"]).dt.tz_localize(None).dt.normalize()
    features = features.merge(eligibility, on=["symbol", "date"], how="left", validate="one_to_one")
    if features["research_eligible"].isna().any():
        raise ValueError("Research eligibility lineage was lost during feature build")
    features = apply_canonical_research_ema(features)
    built["features"] = features
    built["research_universe"] = universe
    return built


def evaluation_rows(features: pd.DataFrame) -> pd.DataFrame:
    """The only rows permitted for signals/outcomes under this contract."""
    if "research_eligible" not in features:
        raise ValueError("Feature frame lacks research_eligible contract column")
    return features.loc[features["research_eligible"].astype(bool)].copy()
