"""Research-only corporate-action semantics audit for current R2 READY.

Focuses on securities where raw_close / adj_close ratio changes by >5% day over day.
Diagnostic only: no R2, Supabase, or production mutation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from r2_ready import load_ready_dataset

OUT = Path("audit_artifacts/corporate_action_semantics")
OUT.mkdir(parents=True, exist_ok=True)


def _ret(s: pd.Series, n: int = 63) -> pd.Series:
    return s / s.shift(n) - 1.0


def main() -> None:
    df, manifest = load_ready_dataset()
    df = df.copy().sort_values(["security_id", "date"])
    for c in ["close", "adj_close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    g = df.groupby("security_id", sort=False, group_keys=False)
    valid = (df["close"] > 0) & (df["adj_close"] > 0)
    df["raw_adj_ratio"] = np.where(valid, df["close"] / df["adj_close"], np.nan)
    df["ratio_change"] = g["raw_adj_ratio"].pct_change().abs()
    df["raw_ret_1d"] = g["close"].pct_change()
    df["adj_ret_1d"] = g["adj_close"].pct_change()
    df["raw_ret_63d"] = g["close"].transform(_ret)
    df["adj_ret_63d"] = g["adj_close"].transform(_ret)
    df["avg_volume_50d_raw"] = g["volume"].transform(lambda s: s.rolling(50, min_periods=20).mean())

    event_idx = df.index[df["ratio_change"] > 0.05].tolist()
    events = df.loc[event_idx, [
        "security_id", "ticker", "date", "close", "adj_close", "volume",
        "raw_adj_ratio", "ratio_change", "raw_ret_1d", "adj_ret_1d",
        "raw_ret_63d", "adj_ret_63d", "avg_volume_50d_raw",
    ]].copy()
    events["return_1d_abs_gap"] = (events["raw_ret_1d"] - events["adj_ret_1d"]).abs()
    events["return_63d_abs_gap"] = (events["raw_ret_63d"] - events["adj_ret_63d"]).abs()

    # Context rows around each event expose whether raw price/volume features jump
    # while adjusted-return semantics remain continuous.
    context_parts = []
    for idx in event_idx:
        pos = df.index.get_loc(idx)
        lo, hi = max(0, pos - 2), min(len(df), pos + 3)
        part = df.iloc[lo:hi].copy()
        sid = df.at[idx, "security_id"]
        part = part[part["security_id"] == sid].copy()
        part["event_date"] = df.at[idx, "date"]
        context_parts.append(part[[
            "security_id", "ticker", "event_date", "date", "close", "adj_close", "volume",
            "raw_adj_ratio", "ratio_change", "raw_ret_1d", "adj_ret_1d",
            "raw_ret_63d", "adj_ret_63d", "avg_volume_50d_raw",
        ]])
    context = pd.concat(context_parts, ignore_index=True) if context_parts else pd.DataFrame()

    summary = {
        "manifest_schema_version": manifest.get("schema_version"),
        "rows": int(len(df)),
        "event_rows": int(len(events)),
        "event_securities": int(events["security_id"].nunique()),
        "event_tickers": sorted(events["ticker"].dropna().astype(str).unique().tolist()),
        "raw_vs_adjusted_1d_gap_gt_5pct_events": int((events["return_1d_abs_gap"] > 0.05).sum()),
        "raw_vs_adjusted_63d_gap_gt_5pct_events": int((events["return_63d_abs_gap"] > 0.05).sum()),
        "max_1d_return_abs_gap": float(events["return_1d_abs_gap"].max()) if len(events) else None,
        "max_63d_return_abs_gap": float(events["return_63d_abs_gap"].max()) if len(events) else None,
        "interpretation": {
            "rs_stock_basis": "adj_close 63-session return is corporate-action-adjusted by design",
            "price_floor_basis": "raw close is nominal-price sensitive by design",
            "liquidity_basis": "raw share volume rolling mean can be structurally discontinuous around share-count-changing actions",
            "event_proxy": "raw/adj ratio change >5% is a diagnostic proxy, not itself a data-quality error",
        },
    }

    events.to_csv(OUT / "corporate_action_events.csv", index=False)
    context.to_csv(OUT / "corporate_action_event_context.csv", index=False)
    (OUT / "corporate_action_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
