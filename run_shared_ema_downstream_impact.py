"""Measure latest-production decision impact of replacing finite-window EMA with governed shared EMA.

Observational only. No DB writes, alerts, positions, or production mutation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from decision_layer import compute_decision_layer
from hard_filter import STATUS_RANK, compute_hard_filter
from r2_feature_engine import build_feature_store_from_r2
from r2_ready import load_ready_dataset
from shared_ema_state import PERIODS, load_shared_ema_state

OUT_JSON = Path("shared_ema_downstream_impact.json")
OUT_CSV = Path("shared_ema_downstream_impact_rows.csv")


def _latest_view(decided: pd.DataFrame) -> pd.DataFrame:
    as_of = decided["date"].max()
    latest = decided.loc[decided["date"] == as_of].copy()
    latest["candidate"] = latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]
    latest["actionable"] = (
        latest["investability_status"].eq("PASS")
        & latest["tradability_status"].eq("PASS")
    )
    return latest


def main() -> None:
    ready, ready_manifest = load_ready_dataset()
    shared, shared_manifest = load_shared_ema_state()
    if (
        shared_manifest.get("source_ready_parquet_key") != ready_manifest.get("parquet_key")
        or shared_manifest.get("source_ready_sha256") != ready_manifest.get("sha256")
    ):
        raise RuntimeError("Shared EMA lineage does not match current ready dataset")

    # Empty sector map is intentional: current hard filter / investability uses rs_spy,
    # not rs_sector. Benchmark/regime and all production formulas remain unchanged.
    built = build_feature_store_from_r2(sector_map={}, ready=ready, manifest=ready_manifest)
    features = built["features"].sort_values(["symbol", "date"]).reset_index(drop=True)

    baseline_decided = compute_decision_layer(compute_hard_filter(features))
    baseline = _latest_view(baseline_decided)
    as_of = baseline["date"].max()

    state = shared.copy()
    state["as_of_date"] = pd.to_datetime(state["as_of_date"]).dt.tz_localize(None)
    state = state.rename(columns={"ticker": "symbol", **{f"ema{p}": f"shared_ema{p}" for p in PERIODS}})
    shared_cols = ["security_id", "symbol", "as_of_date", "last_price", *(f"shared_ema{p}" for p in PERIODS)]
    state = state[shared_cols]

    patched = features.copy()
    latest_mask = patched["date"].eq(as_of)
    latest_rows = patched.loc[latest_mask].copy()
    # r2 feature contract does not retain security_id, so symbol is the join key here.
    # Guard one-to-one ticker uniqueness before patching.
    if state["symbol"].duplicated().any():
        raise RuntimeError("Shared EMA ticker is not unique")
    latest_rows = latest_rows.merge(state.drop(columns="security_id"), on="symbol", how="left", validate="one_to_one")
    missing = latest_rows["shared_ema20"].isna()
    if missing.any():
        raise RuntimeError(f"Missing shared EMA for latest symbols: {latest_rows.loc[missing, 'symbol'].tolist()[:20]}")
    if not latest_rows["date"].eq(latest_rows["as_of_date"]).all():
        bad = latest_rows.loc[~latest_rows["date"].eq(latest_rows["as_of_date"]), "symbol"].tolist()
        raise RuntimeError(f"Shared EMA/latest date mismatch: {bad[:20]}")

    for p in PERIODS:
        latest_rows[f"ema{p}"] = latest_rows[f"shared_ema{p}"]
    latest_rows["ema_stack_aligned"] = (
        (latest_rows["close_raw"] > latest_rows["ema20"])
        & (latest_rows["ema20"] > latest_rows["ema50"])
        & (latest_rows["ema50"] > latest_rows["ema150"])
        & (latest_rows["ema150"] > latest_rows["ema200"])
    )
    original_cols = features.columns
    patched.loc[latest_mask, original_cols] = latest_rows[original_cols].to_numpy()

    shared_decided = compute_decision_layer(compute_hard_filter(patched))
    migrated = _latest_view(shared_decided)

    cols = [
        "symbol", "ema_stack_aligned", "trend_status", "hard_filter_status",
        "investability_status", "tradability_status", "candidate", "actionable",
    ]
    left = baseline[cols].rename(columns={c: f"baseline_{c}" for c in cols if c != "symbol"})
    right = migrated[cols].rename(columns={c: f"shared_{c}" for c in cols if c != "symbol"})
    comp = left.merge(right, on="symbol", how="outer", validate="one_to_one")

    dimensions = ["ema_stack_aligned", "trend_status", "hard_filter_status", "investability_status", "tradability_status", "candidate", "actionable"]
    for dim in dimensions:
        comp[f"changed_{dim}"] = comp[f"baseline_{dim}"].ne(comp[f"shared_{dim}"])
    comp["any_decision_change"] = comp[[f"changed_{x}" for x in dimensions[1:]]].any(axis=1)
    comp.to_csv(OUT_CSV, index=False)

    summary = {
        "status": "PASS" if not comp["any_decision_change"].any() else "IMPACT_PRESENT",
        "governance": "OBSERVATIONAL_ONLY_NO_PRODUCTION_SWITCH",
        "as_of_date": pd.Timestamp(as_of).date().isoformat(),
        "latest_symbols": int(len(comp)),
        "ema_stack_changes": int(comp["changed_ema_stack_aligned"].sum()),
        "trend_status_changes": int(comp["changed_trend_status"].sum()),
        "hard_filter_status_changes": int(comp["changed_hard_filter_status"].sum()),
        "investability_status_changes": int(comp["changed_investability_status"].sum()),
        "tradability_status_changes": int(comp["changed_tradability_status"].sum()),
        "candidate_membership_changes": int(comp["changed_candidate"].sum()),
        "actionable_membership_changes": int(comp["changed_actionable"].sum()),
        "symbols_with_any_decision_change": comp.loc[comp["any_decision_change"], "symbol"].tolist(),
        "symbols_with_stack_change": comp.loc[comp["changed_ema_stack_aligned"], "symbol"].tolist(),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
