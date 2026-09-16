"""Research-only empirical QC for the current R2 READY dataset.

Diagnostic only. Does not mutate R2, Supabase, or production state.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from r2_ready import load_ready_dataset

OUT = Path("audit_artifacts/r2_ready_qc")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df, manifest = load_ready_dataset()
    df = df.copy().sort_values(["security_id", "date"])
    numeric = ["open", "high", "low", "close", "adj_close", "volume"]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    groups = df.groupby("security_id", sort=False)
    depth = groups.agg(
        ticker=("ticker", "last"),
        bars=("date", "size"),
        first_date=("date", "min"),
        last_date=("date", "max"),
    ).reset_index()

    thresholds = [20, 50, 60, 63, 150, 200, 252]
    depth_counts = {f"lt_{n}": int((depth["bars"] < n).sum()) for n in thresholds}

    missing = {c: int(df[c].isna().sum()) for c in ["date", "security_id", "ticker", *numeric]}
    invalid = {
        "nonpositive_open": int((df["open"] <= 0).sum()),
        "nonpositive_high": int((df["high"] <= 0).sum()),
        "nonpositive_low": int((df["low"] <= 0).sum()),
        "nonpositive_close": int((df["close"] <= 0).sum()),
        "nonpositive_adj_close": int((df["adj_close"] <= 0).sum()),
        "negative_volume": int((df["volume"] < 0).sum()),
        "ohlc_high_below_low": int((df["high"] < df["low"]).sum()),
        "open_outside_low_high": int(((df["open"] < df["low"]) | (df["open"] > df["high"])).sum()),
        "close_outside_low_high": int(((df["close"] < df["low"]) | (df["close"] > df["high"])).sum()),
    }

    duplicate_keys = int(df.duplicated(["security_id", "date"]).sum())
    ticker_per_id = groups["ticker"].nunique(dropna=False)
    id_per_ticker = df.groupby("ticker")["security_id"].nunique(dropna=False)

    # Raw/adjusted ratio jumps are a diagnostic corporate-action proxy, not an error by themselves.
    valid_ratio = (df["close"] > 0) & (df["adj_close"] > 0)
    df["raw_adj_ratio"] = np.where(valid_ratio, df["close"] / df["adj_close"], np.nan)
    df["ratio_change"] = groups["raw_adj_ratio"].pct_change().abs()
    ratio_events = df.loc[df["ratio_change"] > 0.05, [
        "security_id", "ticker", "date", "close", "adj_close", "raw_adj_ratio", "ratio_change"
    ]].copy()

    latest = pd.Timestamp(df["date"].max())
    first_dist = depth["first_date"].value_counts().sort_index().rename_axis("date").reset_index(name="security_count")
    last_dist = depth["last_date"].value_counts().sort_index().rename_axis("date").reset_index(name="security_count")

    summary = {
        "manifest_schema_version": manifest.get("schema_version"),
        "manifest_rows": manifest.get("rows"),
        "manifest_security_ids": len(manifest.get("security_ids", [])),
        "rows": int(len(df)),
        "securities": int(depth["security_id"].nunique()),
        "tickers": int(df["ticker"].nunique()),
        "latest_date": str(latest.date()),
        "bar_depth": {
            "min": int(depth["bars"].min()),
            "median": float(depth["bars"].median()),
            "max": int(depth["bars"].max()),
            **depth_counts,
        },
        "duplicate_security_date_rows": duplicate_keys,
        "security_ids_with_multiple_tickers": int((ticker_per_id > 1).sum()),
        "tickers_with_multiple_security_ids": int((id_per_ticker > 1).sum()),
        "missing": missing,
        "invalid": invalid,
        "securities_not_on_global_latest_date": int((depth["last_date"] != latest).sum()),
        "raw_adj_ratio_jump_gt_5pct_rows": int(len(ratio_events)),
        "raw_adj_ratio_jump_gt_5pct_securities": int(ratio_events["security_id"].nunique()),
    }

    (OUT / "r2_ready_qc_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    depth.to_csv(OUT / "r2_ready_qc_depth.csv", index=False)
    first_dist.to_csv(OUT / "r2_ready_qc_first_dates.csv", index=False)
    last_dist.to_csv(OUT / "r2_ready_qc_last_dates.csv", index=False)
    ratio_events.to_csv(OUT / "r2_ready_qc_raw_adj_events.csv", index=False)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
