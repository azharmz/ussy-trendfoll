"""Governed event-level comparison of production trend gate vs TF-SMA-STRUCT-01.

Research only. R2 readiness defines the universe. Long-history OHLCV provides
feature context. All non-trend logic is held constant; only trend qualification
is changed between arms. No parameter search or production change is authorized.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import feature_engine as fe
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer
from r2_ready import load_ready_dataset
from signal_path_diagnostic import build_signal_path_events
from trend_filter_candidate import add_sma_struct_features

SAMPLE_SIZE = 100
WARMUP_BARS = 500


def deterministic_sample(symbols, n=SAMPLE_SIZE):
    return sorted(symbols, key=lambda s: hashlib.sha256(s.encode()).hexdigest())[:n]


def _status_from_existing_nontrend(df: pd.DataFrame) -> pd.Series:
    cols = ["trend_status", "liquidity_status", "rs_status", "price_status", "regime_status"]
    def overall(row):
        ranks = [STATUS_RANK[row[c]] for c in cols]
        if min(ranks) == 0:
            return "FAIL"
        if min(ranks) == 1:
            return "NEAR_PASS"
        return "PASS"
    return df[cols].apply(lambda r: overall({c: r[c] for c in cols}), axis=1)


def _build_arm(features: pd.DataFrame, candidate: bool) -> pd.DataFrame:
    # Compute the production hard-filter components first so every non-trend
    # criterion is literally shared between arms.
    base = compute_hard_filter(features)
    if candidate:
        base = add_sma_struct_features(base)
        base["trend_status"] = np.where(base["tf_sma_struct_pass"], "PASS", "FAIL")
        base["hard_filter_status"] = _status_from_existing_nontrend(base)
    decided = compute_decision_layer(base)
    return decided


def _eligible_after_warmup(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for _, g in df.sort_values(["symbol", "date"]).groupby("symbol", sort=False):
        g = g.copy().reset_index(drop=True)
        g["bar_age"] = np.arange(1, len(g) + 1)
        parts.append(g[g["bar_age"] > WARMUP_BARS])
    return pd.concat(parts, ignore_index=True) if parts else df.iloc[0:0].copy()


def _event_summary(events: pd.DataFrame) -> dict:
    def med(col):
        s = pd.to_numeric(events[col], errors="coerce").dropna() if col in events else pd.Series(dtype=float)
        return None if s.empty else float(s.median())
    def pos(col):
        s = pd.to_numeric(events[col], errors="coerce").dropna() if col in events else pd.Series(dtype=float)
        return None if s.empty else float((s > 0).mean())
    return {
        "events": int(len(events)),
        "symbols": int(events["symbol"].nunique()) if not events.empty else 0,
        "t1_mature": int(events.get("t1_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "t3_mature": int(events.get("t3_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "t5_mature": int(events.get("t5_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "median_tminus1_t0_pct": None if med("ret_tminus1_t0") is None else med("ret_tminus1_t0") * 100,
        "median_pivot_extension_atr": med("pivot_extension_atr_t0"),
        "median_gap_t0close_t1open_pct": None if med("gap_t0close_t1open") is None else med("gap_t0close_t1open") * 100,
        "median_t1open_t1close_pct": None if med("ret_t1open_t1close") is None else med("ret_t1open_t1close") * 100,
        "median_t1open_t3close_pct": None if med("ret_t1open_t3close") is None else med("ret_t1open_t3close") * 100,
        "median_t1open_t5close_pct": None if med("ret_t1open_t5close") is None else med("ret_t1open_t5close") * 100,
        "positive_t1open_t1close": pos("ret_t1open_t1close"),
        "positive_t1open_t3close": pos("ret_t1open_t3close"),
        "positive_t1open_t5close": pos("ret_t1open_t5close"),
        "median_mfe5_pct": None if med("mfe_high_t5") is None else med("mfe_high_t5") * 100,
        "median_mae5_pct": None if med("mae_low_t5") is None else med("mae_low_t5") * 100,
    }


def main():
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    sample = deterministic_sample(universe)

    # Sector RS is not part of the current hard filter. Avoid slow .info calls;
    # preserve a neutral/unknown sector mapping while keeping RS-vs-SPY intact.
    sector_map = pd.DataFrame({
        "symbol": sample,
        "sector": [None] * len(sample),
        "industry": [None] * len(sample),
        "sector_benchmark": [None] * len(sample),
    })
    original_earnings = fe.compute_days_to_next_earnings
    fe.compute_days_to_next_earnings = lambda *args, **kwargs: None
    try:
        result = fe.build_feature_store(sample, sector_map=sector_map)
    finally:
        fe.compute_days_to_next_earnings = original_earnings

    features = result["features"].copy()
    baseline = _eligible_after_warmup(_build_arm(features, candidate=False))
    candidate = _eligible_after_warmup(_build_arm(features, candidate=True))

    baseline_events = build_signal_path_events(baseline)
    candidate_events = build_signal_path_events(candidate)
    baseline_events["arm"] = "BASELINE_EMA_STAGE2"
    candidate_events["arm"] = "TF-SMA-STRUCT-01"

    bkeys = set(zip(baseline_events["symbol"], pd.to_datetime(baseline_events["t0_date"]))) if not baseline_events.empty else set()
    ckeys = set(zip(candidate_events["symbol"], pd.to_datetime(candidate_events["t0_date"]))) if not candidate_events.empty else set()

    summary = {
        "status": "DEVELOPMENT EVENT EVIDENCE / NO PRODUCTION CHANGE",
        "universe_authority": "R2 readiness",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic sample",
        "sample_size_requested": SAMPLE_SIZE,
        "symbols_downloaded": int(features["symbol"].nunique()),
        "warmup_bars_excluded_per_symbol": WARMUP_BARS,
        "event_definition": "hard_filter PASS + breakout + volume confirmation, independent False->True onset",
        "treatment": "trend gate only",
        "baseline_trend": "close > EMA20 > EMA50 > EMA150 > EMA200 AND Stage2(30w SMA)",
        "candidate_trend": "TF-SMA-STRUCT-01: close > SMA50 > SMA200",
        "shared_nontrend": "liquidity, RS-vs-SPY, price, market regime, pivot/breakout, volume confirmation, structure features",
        "overlap": {
            "both_events": len(bkeys & ckeys),
            "baseline_only_events": len(bkeys - ckeys),
            "candidate_only_events": len(ckeys - bkeys),
            "union_events": len(bkeys | ckeys),
        },
        "baseline": _event_summary(baseline_events),
        "candidate": _event_summary(candidate_events),
        "governance": "descriptive development evidence only; frozen candidate unchanged; no production promotion",
    }

    pd.concat([baseline_events, candidate_events], ignore_index=True).to_csv(
        "trend_filter_event_comparison_events.csv", index=False
    )
    Path("trend_filter_event_comparison_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
