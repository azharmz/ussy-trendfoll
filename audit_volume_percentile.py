"""Diagnostic-only audit of breakout_volume_percentile on the current R2 READY snapshot.

No production state is written. Recomputes the exact frozen feature formula directly
from R2 OHLCV and reports the latest breakout names plus distribution/invariants.
"""
from __future__ import annotations

import json
import pandas as pd

from r2_ready import load_ready_dataset, to_feature_contract

TARGETS = {"BBY", "CHRD", "COKE", "OKTA", "OXY", "PR", "SU"}
WINDOW = 50
MIN_PERIODS = 20


def percentile_last(x: pd.Series) -> float:
    return float((x <= x.iloc[-1]).mean() * 100)


def main():
    ready, manifest = load_ready_dataset()
    raw = to_feature_contract(ready)
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values(["symbol", "date"]).reset_index(drop=True)
    raw["breakout_volume_percentile_recomputed"] = raw.groupby("symbol", group_keys=False)["volume_raw"].transform(
        lambda s: s.rolling(WINDOW, min_periods=MIN_PERIODS).apply(percentile_last, raw=False)
    )

    latest_date = raw["date"].max()
    target_rows = []
    for symbol in sorted(TARGETS):
        s = raw[raw["symbol"] == symbol].sort_values("date")
        row = s[s["date"] == latest_date]
        if row.empty:
            target_rows.append({"symbol": symbol, "latest_date": str(latest_date.date()), "available": False})
            continue
        r = row.iloc[-1]
        trailing = s[s["date"] <= latest_date].tail(WINDOW)
        current = float(r["volume_raw"])
        less = int((trailing["volume_raw"] < current).sum())
        equal = int((trailing["volume_raw"] == current).sum())
        leq = int((trailing["volume_raw"] <= current).sum())
        target_rows.append({
            "symbol": symbol,
            "latest_date": str(latest_date.date()),
            "available": True,
            "window_n": int(len(trailing)),
            "volume_raw": current,
            "window_min": float(trailing["volume_raw"].min()),
            "window_median": float(trailing["volume_raw"].median()),
            "window_max": float(trailing["volume_raw"].max()),
            "count_lt_current": less,
            "count_eq_current": equal,
            "count_le_current": leq,
            "percentile_recomputed": float(r["breakout_volume_percentile_recomputed"]),
            "expected_grid_step": 100.0 / len(trailing),
            "is_window_min": bool(current == float(trailing["volume_raw"].min())),
        })

    out = pd.DataFrame(target_rows)
    out.to_csv("volume_percentile_audit_targets.csv", index=False)

    latest = raw[raw["date"] == latest_date].copy()
    vals = latest["breakout_volume_percentile_recomputed"].dropna()
    summary = {
        "snapshot_date": manifest.get("snapshot_date"),
        "latest_market_date": str(latest_date.date()),
        "ready_securities": int(raw["symbol"].nunique()),
        "latest_rows": int(len(latest)),
        "formula": "rolling(50,min_periods=20): mean(x <= current)*100",
        "target_count": len(TARGETS),
        "target_available": int(out.get("available", pd.Series(dtype=bool)).fillna(False).sum()),
        "target_percentiles": {r["symbol"]: r.get("percentile_recomputed") for r in target_rows},
        "latest_percentile_distribution": {
            "min": float(vals.min()), "p25": float(vals.quantile(.25)),
            "median": float(vals.median()), "p75": float(vals.quantile(.75)), "max": float(vals.max()),
        } if len(vals) else {},
        "latest_count_pct_eq_2": int((vals == 2.0).sum()),
        "latest_count_pct_le_2": int((vals <= 2.0).sum()),
        "latest_count_pct_ge_80": int((vals >= 80.0).sum()),
    }
    with open("volume_percentile_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\nTARGET DETAIL")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
