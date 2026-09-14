"""Compare TrendFoll long-history signals using EMA(close_raw) vs EMA(close_adj).

Observational only. R2 readiness defines the universe; long-history OHLCV provides
feature context. All non-EMA logic is held constant. No production migration is
authorized by this script.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import feature_engine as fe
from hard_filter import compute_hard_filter
from decision_layer import compute_decision_layer
from r2_ready import load_ready_dataset
from signal_path_diagnostic import build_signal_path_events

SAMPLE_SIZE = 100
WARMUP_BARS = 500
PERIODS = (20, 50, 150, 200)
OUT_JSON = Path("ema_price_basis_audit_summary.json")
OUT_EVENTS = Path("ema_price_basis_audit_events.csv")
OUT_ROWS = Path("ema_price_basis_audit_rows.csv")


def deterministic_sample(symbols, n=SAMPLE_SIZE):
    return sorted(symbols, key=lambda s: hashlib.sha256(s.encode()).hexdigest())[:n]


def eligible_after_warmup(df: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for _, g in df.sort_values(["symbol", "date"]).groupby("symbol", sort=False):
        g = g.copy().reset_index(drop=True)
        g["bar_age"] = np.arange(1, len(g) + 1)
        parts.append(g[g["bar_age"] > WARMUP_BARS])
    return pd.concat(parts, ignore_index=True) if parts else df.iloc[0:0].copy()


def with_ema_basis(features: pd.DataFrame, price_col: str) -> pd.DataFrame:
    out = features.copy().sort_values(["symbol", "date"]).reset_index(drop=True)
    for p in PERIODS:
        out[f"ema{p}"] = out.groupby("symbol", sort=False)[price_col].transform(
            lambda s, span=p: s.ewm(span=span, adjust=False).mean()
        )
    out["ema_stack_aligned"] = (
        (out[price_col] > out["ema20"])
        & (out["ema20"] > out["ema50"])
        & (out["ema50"] > out["ema150"])
        & (out["ema150"] > out["ema200"])
    )
    return out


def event_summary(events: pd.DataFrame) -> dict:
    def med(col):
        s = pd.to_numeric(events[col], errors="coerce").dropna() if col in events else pd.Series(dtype=float)
        return None if s.empty else float(s.median())
    def pos(col):
        s = pd.to_numeric(events[col], errors="coerce").dropna() if col in events else pd.Series(dtype=float)
        return None if s.empty else float((s > 0).mean())
    return {
        "events": int(len(events)),
        "symbols": int(events["symbol"].nunique()) if not events.empty else 0,
        "median_tminus1_t0_pct": None if med("ret_tminus1_t0") is None else med("ret_tminus1_t0") * 100,
        "median_t1open_t1close_pct": None if med("ret_t1open_t1close") is None else med("ret_t1open_t1close") * 100,
        "median_t1open_t3close_pct": None if med("ret_t1open_t3close") is None else med("ret_t1open_t3close") * 100,
        "median_t1open_t5close_pct": None if med("ret_t1open_t5close") is None else med("ret_t1open_t5close") * 100,
        "positive_t1": pos("ret_t1open_t1close"),
        "positive_t3": pos("ret_t1open_t3close"),
        "positive_t5": pos("ret_t1open_t5close"),
        "median_mfe5_pct": None if med("mfe_high_t5") is None else med("mfe_high_t5") * 100,
        "median_mae5_pct": None if med("mae_low_t5") is None else med("mae_low_t5") * 100,
    }


def main():
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    sample = deterministic_sample(universe)
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
    raw_features = with_ema_basis(features, "close_raw")
    adj_features = with_ema_basis(features, "close_adj")

    raw = eligible_after_warmup(compute_decision_layer(compute_hard_filter(raw_features)))
    adj = eligible_after_warmup(compute_decision_layer(compute_hard_filter(adj_features)))

    raw_events = build_signal_path_events(raw)
    adj_events = build_signal_path_events(adj)
    raw_events["arm"] = "EMA_CLOSE_RAW"
    adj_events["arm"] = "EMA_ADJ_CLOSE"

    rkeys = set(zip(raw_events["symbol"], pd.to_datetime(raw_events["t0_date"]))) if not raw_events.empty else set()
    akeys = set(zip(adj_events["symbol"], pd.to_datetime(adj_events["t0_date"]))) if not adj_events.empty else set()

    key_cols = ["symbol", "date", "ema_stack_aligned", "trend_status", "hard_filter_status", "investability_status"]
    raw_rows = raw[key_cols].rename(columns={c: f"raw_{c}" for c in key_cols if c not in ("symbol", "date")})
    adj_rows = adj[key_cols].rename(columns={c: f"adj_{c}" for c in key_cols if c not in ("symbol", "date")})
    rows = raw_rows.merge(adj_rows, on=["symbol", "date"], how="inner", validate="one_to_one")
    rows["stack_changed"] = rows["raw_ema_stack_aligned"].ne(rows["adj_ema_stack_aligned"])
    rows["trend_changed"] = rows["raw_trend_status"].ne(rows["adj_trend_status"])
    rows["hard_filter_changed"] = rows["raw_hard_filter_status"].ne(rows["adj_hard_filter_status"])
    rows["investability_changed"] = rows["raw_investability_status"].ne(rows["adj_investability_status"])

    summary = {
        "status": "OBSERVATIONAL_ONLY_NO_PRODUCTION_CHANGE",
        "universe_authority": "R2 readiness",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic sample",
        "sample_size_requested": SAMPLE_SIZE,
        "symbols_downloaded": int(features["symbol"].nunique()),
        "warmup_bars_excluded_per_symbol": WARMUP_BARS,
        "treatment": "EMA price basis only; all non-EMA logic held constant",
        "baseline": "EMA(close_raw)",
        "candidate": "EMA(close_adj)",
        "comparable_rows": int(len(rows)),
        "stack_change_rows": int(rows["stack_changed"].sum()),
        "stack_change_rate": float(rows["stack_changed"].mean()) if len(rows) else None,
        "trend_status_change_rows": int(rows["trend_changed"].sum()),
        "hard_filter_change_rows": int(rows["hard_filter_changed"].sum()),
        "investability_change_rows": int(rows["investability_changed"].sum()),
        "event_overlap": {
            "both": len(rkeys & akeys),
            "raw_only": len(rkeys - akeys),
            "adj_only": len(akeys - rkeys),
            "union": len(rkeys | akeys),
            "jaccard": (len(rkeys & akeys) / len(rkeys | akeys)) if (rkeys | akeys) else None,
        },
        "raw_close": event_summary(raw_events),
        "adj_close": event_summary(adj_events),
        "governance": "Audit first. Canonical adj_close is not frozen until materiality is reviewed.",
    }

    rows.to_csv(OUT_ROWS, index=False)
    pd.concat([raw_events, adj_events], ignore_index=True).to_csv(OUT_EVENTS, index=False)
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
