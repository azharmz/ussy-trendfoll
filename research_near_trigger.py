"""Research-only evidence for a future NEAR_TRIGGER definition.

This script does not change production Investability/Tradability or alert-state
thresholds. It measures distance to the prior pivot before independent breakout
onsets, and estimates forward breakout-onset rates by distance bucket.
"""
from __future__ import annotations

import json
import pandas as pd

import feature_engine as fe
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer
from sector_cache import get_sector_map
from r2_ready import load_ready_dataset
from r2_integration import build_feature_store_from_r2
import database

LAGS = (1, 2, 3, 5)
HORIZONS = (1, 2, 3, 5)


def _q(series: pd.Series, q: float):
    s = pd.to_numeric(series, errors="coerce").dropna()
    return None if s.empty else float(s.quantile(q))


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

    # Earnings lookup is irrelevant to this research and very slow across the
    # full R2 universe. Disable it only inside this research run.
    original_earnings = fe.compute_days_to_next_earnings
    fe.compute_days_to_next_earnings = lambda *args, **kwargs: None
    try:
        features = build_feature_store_from_r2(
            sector_map=sector_map,
            ready=ready,
            manifest=manifest,
        )["features"]
    finally:
        fe.compute_days_to_next_earnings = original_earnings

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
    decided["prev_has_breakout"] = (
        decided.groupby("symbol")["has_breakout"].shift(1).fillna(False).astype(bool)
    )
    decided["breakout_onset"] = decided["has_breakout"].astype(bool) & (~decided["prev_has_breakout"])
    return decided, manifest


def _forward_onset_flags(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()
    onset = g["breakout_onset"].astype(bool)
    for horizon in HORIZONS:
        future = pd.Series(False, index=g.index)
        for k in range(1, horizon + 1):
            future = future | onset.shift(-k, fill_value=False)
        g[f"onset_within_{horizon}d"] = future
    return g


def _bucket_rates(df: pd.DataFrame, distance_col: str) -> list[dict]:
    work = df[df[distance_col].notna() & (df[distance_col] >= 0)].copy()
    if len(work) < 5:
        return []
    work["bucket"] = pd.qcut(work[distance_col], q=5, duplicates="drop")
    rows = []
    for interval, grp in work.groupby("bucket", observed=True):
        row = {
            "interval": str(interval),
            "n": int(len(grp)),
            "median_distance": float(grp[distance_col].median()),
        }
        for horizon in HORIZONS:
            row[f"onset_within_{horizon}d_rate"] = float(grp[f"onset_within_{horizon}d"].mean())
        rows.append(row)
    return rows


def analyze(decided: pd.DataFrame, manifest: dict) -> dict:
    rows = []
    onset_count = 0
    control_frames = []

    for symbol, g0 in decided.groupby("symbol", sort=False):
        g = _forward_onset_flags(g0.sort_values("date").reset_index(drop=True))
        onset_indices = g.index[g["breakout_onset"]].tolist()
        onset_count += len(onset_indices)

        for idx in onset_indices:
            for lag in LAGS:
                j = idx - lag
                if j < 0:
                    continue
                prior = g.iloc[j]
                if not bool(prior["is_monitored"]) or bool(prior["has_breakout"]):
                    continue
                pct = prior["distance_to_prev_pivot_pct"]
                atr = prior["distance_to_prev_pivot_atr"]
                if pd.isna(pct) or pd.isna(atr) or pct < 0 or atr < 0:
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

        eligible = g[
            g["is_monitored"]
            & (~g["has_breakout"])
            & g["distance_to_prev_pivot_pct"].notna()
            & g["distance_to_prev_pivot_atr"].notna()
            & (g["distance_to_prev_pivot_pct"] >= 0)
            & (g["distance_to_prev_pivot_atr"] >= 0)
        ].copy()
        if not eligible.empty:
            control_frames.append(eligible)

    evidence = pd.DataFrame(rows)
    control = pd.concat(control_frames, ignore_index=True) if control_frames else pd.DataFrame()

    lag_stats = {}
    for lag in LAGS:
        sub = evidence[evidence["lag"] == lag] if not evidence.empty else pd.DataFrame()
        lag_stats[str(lag)] = {
            "distance_pct": _summary(sub["distance_pct"]) if not sub.empty else _summary(pd.Series(dtype=float)),
            "distance_atr": _summary(sub["distance_atr"]) if not sub.empty else _summary(pd.Series(dtype=float)),
        }

    return {
        "methodology": {
            "event": "breakout_onset = has_breakout today AND not has_breakout yesterday",
            "pre_event_rows_require_no_breakout": True,
            "monitored": "investability >= NEAR_PASS",
        },
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "ready_rows": int(manifest.get("rows", 0)),
        "breakout_onsets": int(onset_count),
        "pre_breakout_observations": int(len(evidence)),
        "lag_stats": lag_stats,
        "distance_pct_quintile_forward_onset_rate": _bucket_rates(control, "distance_to_prev_pivot_pct") if not control.empty else [],
        "distance_atr_quintile_forward_onset_rate": _bucket_rates(control, "distance_to_prev_pivot_atr") if not control.empty else [],
    }


def main():
    decided, manifest = build_research_frame()
    result = analyze(decided, manifest)
    print("=== NEAR_TRIGGER REFINED EVIDENCE ===")
    print(json.dumps(result, indent=2, sort_keys=True))
    with open("near_trigger_evidence.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
