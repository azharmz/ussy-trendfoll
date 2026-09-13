"""Research-only evidence for a future NEAR_TRIGGER definition.

This script does not change production Investability/Tradability or alert-state
thresholds. It measures how far monitored setups were from the prior pivot in
the trading days before an observed breakout.
"""
from __future__ import annotations

import json
import math
import pandas as pd

from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer
from sector_cache import get_sector_map
from r2_ready import load_ready_dataset
from r2_feature_engine import build_feature_store_from_r2
import database

LAGS = (1, 2, 3, 5)


def _q(series: pd.Series, q: float):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return None
    return float(s.quantile(q))


def _summary(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"n": 0, "p10": None, "p25": None, "p50": None, "p75": None, "p90": None}
    return {
        "n": int(len(s)),
        "p10": _q(s, 0.10),
        "p25": _q(s, 0.25),
        "p50": _q(s, 0.50),
        "p75": _q(s, 0.75),
        "p90": _q(s, 0.90),
    }


def build_research_frame() -> tuple[pd.DataFrame, dict]:
    client = database.get_client()
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    sector_map = get_sector_map(client, universe)
    features = build_feature_store_from_r2(
        sector_map=sector_map,
        ready=ready,
        manifest=manifest,
    )["features"]
    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"]).copy()

    decided["distance_to_prev_pivot_pct"] = (
        (decided["prev_pivot_high"] - decided["close_raw"])
        / decided["prev_pivot_high"] * 100.0
    )
    decided["distance_to_prev_pivot_atr"] = (
        (decided["prev_pivot_high"] - decided["close_raw"])
        / decided["atr14"]
    )
    decided["is_monitored"] = (
        decided["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]
    )
    return decided, manifest


def analyze(decided: pd.DataFrame, manifest: dict) -> dict:
    rows = []
    event_count = 0

    for symbol, g in decided.groupby("symbol", sort=False):
        g = g.sort_values("date").reset_index(drop=True)
        breakout_indices = g.index[g["has_breakout"] == True].tolist()
        for idx in breakout_indices:
            event_count += 1
            for lag in LAGS:
                j = idx - lag
                if j < 0:
                    continue
                prior = g.iloc[j]
                if not bool(prior["is_monitored"]):
                    continue
                pct = prior["distance_to_prev_pivot_pct"]
                atr = prior["distance_to_prev_pivot_atr"]
                if pd.isna(pct) or pd.isna(atr):
                    continue
                rows.append({
                    "symbol": symbol,
                    "breakout_date": pd.Timestamp(g.iloc[idx]["date"]).date().isoformat(),
                    "lag": lag,
                    "prior_date": pd.Timestamp(prior["date"]).date().isoformat(),
                    "distance_pct": float(pct),
                    "distance_atr": float(atr),
                    "prior_investability": prior["investability_status"],
                })

    evidence = pd.DataFrame(rows)
    lag_stats = {}
    for lag in LAGS:
        sub = evidence[evidence["lag"] == lag] if not evidence.empty else pd.DataFrame()
        lag_stats[str(lag)] = {
            "distance_pct": _summary(sub["distance_pct"]) if not sub.empty else _summary(pd.Series(dtype=float)),
            "distance_atr": _summary(sub["distance_atr"]) if not sub.empty else _summary(pd.Series(dtype=float)),
        }

    eligible = decided[
        decided["is_monitored"]
        & (~decided["has_breakout"])
        & decided["distance_to_prev_pivot_pct"].notna()
        & (decided["distance_to_prev_pivot_pct"] >= 0)
    ].copy()

    quintiles = []
    if len(eligible) >= 5:
        eligible["distance_quintile"] = pd.qcut(
            eligible["distance_to_prev_pivot_pct"],
            q=5,
            duplicates="drop",
        )
        for interval, grp in eligible.groupby("distance_quintile", observed=True):
            quintiles.append({
                "interval": str(interval),
                "n": int(len(grp)),
                "median_distance_pct": float(grp["distance_to_prev_pivot_pct"].median()),
            })

    return {
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "ready_rows": int(manifest.get("rows", 0)),
        "breakout_events_all": int(event_count),
        "pre_breakout_observations": int(len(evidence)),
        "lag_stats": lag_stats,
        "monitored_non_breakout_distance_quintiles": quintiles,
    }


def main():
    decided, manifest = build_research_frame()
    result = analyze(decided, manifest)
    print("=== NEAR_TRIGGER EVIDENCE ===")
    print(json.dumps(result, indent=2, sort_keys=True))
    with open("near_trigger_evidence.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
