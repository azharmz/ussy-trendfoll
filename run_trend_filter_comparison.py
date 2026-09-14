"""Governed development comparison: production trend gate vs TF-SMA-STRUCT-01.

Research only. R2 readiness supplies the universe; stock OHLCV is downloaded as
long history. The first 500 observations per symbol are context-only warm-up and
are excluded from evaluation. No parameter search is performed.
"""
from __future__ import annotations

import hashlib
import json
import pandas as pd

import feature_engine as fe
from r2_ready import load_ready_dataset
from trend_filter_candidate import add_sma_struct_features

SAMPLE_SIZE = 100
WARMUP_BARS = 500
HORIZONS = (1, 3, 5)


def deterministic_sample(symbols, n=SAMPLE_SIZE):
    return sorted(symbols, key=lambda s: hashlib.sha256(s.encode()).hexdigest())[:n]


def add_baseline_and_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for symbol, raw in df.groupby("symbol", sort=False):
        g = raw.sort_values("date").reset_index(drop=True).copy()
        g = fe.compute_ema_features(g)
        weekly = fe.compute_weekly_stage_features(g)
        weekly["date"] = pd.to_datetime(weekly["date"])
        g["date"] = pd.to_datetime(g["date"])
        g = pd.merge_asof(g.sort_values("date"), weekly.sort_values("date"), on="date", direction="backward")
        g["baseline_pass"] = g["ema_stack_aligned"].astype(bool) & g["stage"].eq("Stage2")
        g["bar_age"] = range(1, len(g) + 1)
        g["evaluation_eligible"] = g["bar_age"] > WARMUP_BARS
        for h in HORIZONS:
            future_close = g["close_raw"].shift(-h)
            g[f"ret_tplus{h}_pct"] = (future_close / g["close_raw"] - 1.0) * 100.0
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def summarize(frame: pd.DataFrame, gate: str) -> dict:
    rows = frame[frame["evaluation_eligible"] & frame[gate].fillna(False)].copy()
    out = {"pass_rows": int(len(rows)), "unique_symbols": int(rows["symbol"].nunique())}
    for h in HORIZONS:
        s = pd.to_numeric(rows[f"ret_tplus{h}_pct"], errors="coerce").dropna()
        out[f"tplus{h}_n"] = int(len(s))
        out[f"tplus{h}_median_pct"] = None if s.empty else float(s.median())
        out[f"tplus{h}_positive_rate"] = None if s.empty else float((s > 0).mean())
    return out


def main():
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    sample = deterministic_sample(universe)

    # Long history is research context; R2 remains the universe authority.
    raw = fe.download_universe(sample, pause_seconds=0.05)
    if raw.empty:
        raise RuntimeError("No long-history OHLCV downloaded")

    frame = add_baseline_and_outcomes(raw)
    frame = add_sma_struct_features(frame)
    evalf = frame[frame["evaluation_eligible"]].copy()
    both_eval = evalf[evalf["tf_sma_struct_evaluable"]].copy()

    b = both_eval["baseline_pass"].fillna(False).astype(bool)
    c = both_eval["tf_sma_struct_pass"].fillna(False).astype(bool)
    result = {
        "status": "DEVELOPMENT EVIDENCE / NO PRODUCTION CHANGE",
        "universe_authority": "R2 readiness",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic sample",
        "sample_size_requested": SAMPLE_SIZE,
        "symbols_downloaded": int(frame["symbol"].nunique()),
        "warmup_bars_excluded_per_symbol": WARMUP_BARS,
        "baseline": "close > EMA20 > EMA50 > EMA150 > EMA200 AND Stage2(30w SMA)",
        "candidate": "TF-SMA-STRUCT-01: close > SMA50 > SMA200",
        "comparable_rows": int(len(both_eval)),
        "baseline_pass_rate": float(b.mean()) if len(b) else None,
        "candidate_pass_rate": float(c.mean()) if len(c) else None,
        "agreement_rate": float((b == c).mean()) if len(b) else None,
        "both_pass": int((b & c).sum()),
        "baseline_only": int((b & ~c).sum()),
        "candidate_only": int((~b & c).sum()),
        "neither": int((~b & ~c).sum()),
        "baseline_outcomes": summarize(frame, "baseline_pass"),
        "candidate_outcomes": summarize(frame, "tf_sma_struct_pass"),
        "note": "Descriptive development comparison only; no threshold tuning or production promotion is authorized.",
    }

    both_eval[["symbol","date","close_raw","baseline_pass","sma50","sma200","tf_sma_struct_pass","ret_tplus1_pct","ret_tplus3_pct","ret_tplus5_pct"]].to_csv("trend_filter_comparison_rows.csv", index=False)
    with open("trend_filter_comparison_summary.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
