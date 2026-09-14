"""PROB-018 — audit R2 finite-history trend features against long-history reference.

Observational only. This script does not change production thresholds or signals.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from hard_filter import _trend_status
from r2_ready import load_ready_dataset, to_feature_contract

SAMPLE_SIZE = 100
REFERENCE_PERIOD = "5y"
SOURCE_CLOSE_TOLERANCE_PCT = 0.25
AGE_BINS = [0, 50, 100, 150, 200, 250, 10_000]
AGE_LABELS = ["1-50", "51-100", "101-150", "151-200", "201-250", "251+"]
EMA_SPANS = (20, 50, 150, 200)


def stable_sample(symbols: list[str], n: int = SAMPLE_SIZE) -> list[str]:
    ranked = sorted(symbols, key=lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())
    return ranked[: min(n, len(ranked))]


def compute_trend_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Mirror the current production trend contract only."""
    df = raw[["date", "symbol", "close_raw"]].copy().sort_values("date").reset_index(drop=True)
    for span in EMA_SPANS:
        df[f"ema{span}"] = df["close_raw"].ewm(span=span, adjust=False).mean()
    df["ema_stack_aligned"] = (
        (df["close_raw"] > df["ema20"])
        & (df["ema20"] > df["ema50"])
        & (df["ema50"] > df["ema150"])
        & (df["ema150"] > df["ema200"])
    )

    daily = df.set_index("date")
    weekly_close = daily["close_raw"].resample("W-FRI").last()
    ma30w = weekly_close.rolling(30).mean()
    slope = pd.Series(index=ma30w.index, dtype=object)
    for i in range(2, len(ma30w)):
        a, b, c = ma30w.iloc[i - 2], ma30w.iloc[i - 1], ma30w.iloc[i]
        if pd.isna(a) or pd.isna(b) or pd.isna(c):
            slope.iloc[i] = None
        elif c > b > a:
            slope.iloc[i] = "Up"
        elif c < b < a:
            slope.iloc[i] = "Down"
        else:
            slope.iloc[i] = "Flat"

    weekly = pd.DataFrame({"week_date": weekly_close.index, "weekly_close": weekly_close.values,
                           "ma30w": ma30w.values, "ma30w_slope": slope.values})

    def stage_of(row):
        price, ma, sl = row["weekly_close"], row["ma30w"], row["ma30w_slope"]
        if pd.isna(ma) or sl is None or pd.isna(sl):
            return None
        if price > ma and sl == "Up":
            return "Stage2"
        if price < ma and sl == "Down":
            return "Stage4"
        if price > ma and sl in ("Flat", "Down"):
            return "Stage3"
        return "Stage1"

    weekly["stage"] = weekly.apply(stage_of, axis=1)

    # Production weekly state becomes observable after Friday's weekly close.
    # merge_asof backward therefore prevents look-ahead on earlier weekdays.
    left = df.sort_values("date").copy()
    right = weekly[["week_date", "ma30w", "ma30w_slope", "stage"]].sort_values("week_date")
    out = pd.merge_asof(left, right, left_on="date", right_on="week_date", direction="backward")
    out["trend_status"] = out.apply(_trend_status, axis=1)
    return out


def _yf_reference(symbol: str) -> pd.DataFrame:
    raw = yf.Ticker(symbol).history(period=REFERENCE_PERIOD, auto_adjust=False, timeout=20)
    if raw.empty:
        return pd.DataFrame()
    idx = raw.index.tz_localize(None) if getattr(raw.index, "tz", None) is not None else raw.index
    return pd.DataFrame({
        "date": pd.to_datetime(idx).astype("datetime64[ns]"),
        "symbol": symbol,
        "close_raw": pd.to_numeric(raw["Close"], errors="coerce").to_numpy(),
    }).dropna(subset=["close_raw"]).reset_index(drop=True)


def compare_symbol(r2_raw: pd.DataFrame, reference_raw: pd.DataFrame) -> pd.DataFrame:
    r2_feat = compute_trend_features(r2_raw)
    ref_feat = compute_trend_features(reference_raw)

    r2_feat["r2_bar_age"] = np.arange(1, len(r2_feat) + 1)
    cols = ["date", "symbol", "close_raw", "r2_bar_age", "ema20", "ema50", "ema150", "ema200",
            "ema_stack_aligned", "ma30w", "stage", "trend_status"]
    a = r2_feat[cols].rename(columns={c: f"r2_{c}" for c in cols if c not in ("date", "symbol")})
    b = ref_feat[["date", "symbol", "close_raw", "ema20", "ema50", "ema150", "ema200",
                  "ema_stack_aligned", "ma30w", "stage", "trend_status"]].rename(
        columns={c: f"ref_{c}" for c in ["close_raw", "ema20", "ema50", "ema150", "ema200",
                                              "ema_stack_aligned", "ma30w", "stage", "trend_status"]}
    )
    m = a.merge(b, on=["date", "symbol"], how="inner")
    if m.empty:
        return m

    m["source_close_diff_pct"] = (m["r2_close_raw"] / m["ref_close_raw"] - 1.0).abs() * 100.0
    m["source_match"] = m["source_close_diff_pct"] <= SOURCE_CLOSE_TOLERANCE_PCT
    for span in EMA_SPANS:
        m[f"ema{span}_abs_error_pct"] = (m[f"r2_ema{span}"] / m[f"ref_ema{span}"] - 1.0).abs() * 100.0
    m["ema_stack_disagree"] = m["r2_ema_stack_aligned"] != m["ref_ema_stack_aligned"]
    m["stage_disagree"] = m["r2_stage"].fillna("<NA>") != m["ref_stage"].fillna("<NA>")
    m["trend_status_disagree"] = m["r2_trend_status"].fillna("<NA>") != m["ref_trend_status"].fillna("<NA>")
    m["age_bin"] = pd.cut(m["r2_r2_bar_age"], bins=AGE_BINS, labels=AGE_LABELS, include_lowest=True)
    return m


def summarize(obs: pd.DataFrame, manifest: dict, requested: int, successful: int) -> tuple[dict, pd.DataFrame]:
    matched = obs[obs["source_match"]].copy()
    grouped_rows = []
    for age, g in matched.groupby("age_bin", observed=True):
        row = {
            "age_bin": str(age),
            "observations": int(len(g)),
            "symbols": int(g["symbol"].nunique()),
            "ema_stack_disagreement_rate": float(g["ema_stack_disagree"].mean()),
            "stage_disagreement_rate": float(g["stage_disagree"].mean()),
            "trend_status_disagreement_rate": float(g["trend_status_disagree"].mean()),
        }
        for span in EMA_SPANS:
            row[f"ema{span}_median_abs_error_pct"] = float(g[f"ema{span}_abs_error_pct"].median())
            row[f"ema{span}_p95_abs_error_pct"] = float(g[f"ema{span}_abs_error_pct"].quantile(0.95))
        grouped_rows.append(row)
    by_age = pd.DataFrame(grouped_rows)

    latest = matched.sort_values(["symbol", "date"]).groupby("symbol", as_index=False).tail(1)
    summary = {
        "status": "OBSERVATIONAL / NO PRODUCTION CHANGE",
        "problem": "PROB-018",
        "r2_snapshot_date": manifest.get("snapshot_date"),
        "reference_source": "yfinance",
        "reference_period": REFERENCE_PERIOD,
        "sample_requested": requested,
        "sample_successful": successful,
        "overlap_observations": int(len(obs)),
        "source_matched_observations": int(len(matched)),
        "source_mismatch_observations": int((~obs["source_match"]).sum()) if len(obs) else 0,
        "source_close_tolerance_pct": SOURCE_CLOSE_TOLERANCE_PCT,
        "latest_symbols": int(len(latest)),
        "latest_ema_stack_disagreement_rate": float(latest["ema_stack_disagree"].mean()) if len(latest) else None,
        "latest_stage_disagreement_rate": float(latest["stage_disagree"].mean()) if len(latest) else None,
        "latest_trend_status_disagreement_rate": float(latest["trend_status_disagree"].mean()) if len(latest) else None,
    }
    for span in EMA_SPANS:
        summary[f"latest_ema{span}_median_abs_error_pct"] = (
            float(latest[f"ema{span}_abs_error_pct"].median()) if len(latest) else None
        )
        summary[f"latest_ema{span}_p95_abs_error_pct"] = (
            float(latest[f"ema{span}_abs_error_pct"].quantile(0.95)) if len(latest) else None
        )
    return summary, by_age


def main() -> None:
    ready, manifest = load_ready_dataset()
    raw = to_feature_contract(ready)
    raw["date"] = pd.to_datetime(raw["date"]).astype("datetime64[ns]")
    symbols = sorted(raw["symbol"].dropna().astype(str).unique())
    sample = stable_sample(symbols)
    print(f"[PROB-018] R2 snapshot={manifest.get('snapshot_date')} universe={len(symbols)} sample={len(sample)}")

    frames = []
    failures = []
    for i, symbol in enumerate(sample, 1):
        print(f"[{i}/{len(sample)}] {symbol}", end=" ... ", flush=True)
        try:
            ref = _yf_reference(symbol)
            if ref.empty:
                failures.append({"symbol": symbol, "reason": "reference_empty"})
                print("reference empty")
                continue
            stock = raw[raw["symbol"] == symbol][["date", "symbol", "close_raw"]].copy()
            comp = compare_symbol(stock, ref)
            if comp.empty:
                failures.append({"symbol": symbol, "reason": "no_overlap"})
                print("no overlap")
                continue
            frames.append(comp)
            print(f"OK overlap={len(comp)} source_match={comp['source_match'].mean():.1%}")
        except Exception as exc:
            failures.append({"symbol": symbol, "reason": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {type(exc).__name__}: {exc}")

    if not frames:
        raise RuntimeError("PROB-018 audit produced no comparable observations")

    obs = pd.concat(frames, ignore_index=True)
    summary, by_age = summarize(obs, manifest, len(sample), len(frames))
    obs.to_csv("trend_warmup_audit_observations.csv", index=False)
    by_age.to_csv("trend_warmup_audit_by_age.csv", index=False)
    pd.DataFrame(failures).to_csv("trend_warmup_audit_failures.csv", index=False)
    Path("trend_warmup_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n[PROB-018 summary]")
    print(json.dumps(summary, indent=2))
    print("\n[by age]")
    print(by_age.to_string(index=False))


if __name__ == "__main__":
    main()
