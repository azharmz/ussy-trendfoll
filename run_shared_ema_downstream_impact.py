"""Measure latest-production decision impact of replacing finite-window EMA with governed shared EMA.

Observational only. No DB writes, alerts, positions, or production mutation.
Only symbols whose latest EMA-stack classification differs are recomputed downstream;
all other symbols are invariant for this migration by construction.
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


def _finite_stack(group: pd.DataFrame) -> bool:
    g = group.sort_values("date")
    price = pd.to_numeric(g["close"], errors="raise").astype(float)
    values = {p: float(price.ewm(span=p, adjust=False).mean().iloc[-1]) for p in PERIODS}
    return bool(float(price.iloc[-1]) > values[20] > values[50] > values[150] > values[200])


def _latest_view(decided: pd.DataFrame) -> pd.DataFrame:
    as_of = decided["date"].max()
    latest = decided.loc[decided["date"] == as_of].copy()
    latest["candidate"] = latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]
    latest["actionable"] = latest["investability_status"].eq("PASS") & latest["tradability_status"].eq("PASS")
    return latest


def main() -> None:
    ready, ready_manifest = load_ready_dataset()
    shared, shared_manifest = load_shared_ema_state()
    if (
        shared_manifest.get("source_ready_parquet_key") != ready_manifest.get("parquet_key")
        or shared_manifest.get("source_ready_sha256") != ready_manifest.get("sha256")
    ):
        raise RuntimeError("Shared EMA lineage does not match current ready dataset")

    state = shared.copy()
    state["as_of_date"] = pd.to_datetime(state["as_of_date"]).dt.tz_localize(None)
    state["shared_stack"] = (
        (state["last_price"] > state["ema20"])
        & (state["ema20"] > state["ema50"])
        & (state["ema50"] > state["ema150"])
        & (state["ema150"] > state["ema200"])
    )
    finite_rows = []
    for sid, group in ready.groupby("security_id", sort=True):
        finite_rows.append({
            "security_id": str(sid),
            "symbol": str(group.sort_values("date")["ticker"].iloc[-1]),
            "finite_stack": _finite_stack(group),
        })
    finite = pd.DataFrame(finite_rows)
    mismatch = finite.merge(state[["security_id", "shared_stack"]], on="security_id", validate="one_to_one")
    mismatch = mismatch.loc[mismatch["finite_stack"].ne(mismatch["shared_stack"])].copy()
    affected_symbols = sorted(mismatch["symbol"].tolist())
    if not affected_symbols:
        summary = {
            "status": "PASS", "governance": "OBSERVATIONAL_ONLY_NO_PRODUCTION_SWITCH",
            "affected_symbols_evaluated": 0, "ema_stack_changes": 0,
            "trend_status_changes": 0, "hard_filter_status_changes": 0,
            "investability_status_changes": 0, "tradability_status_changes": 0,
            "candidate_membership_changes": 0, "actionable_membership_changes": 0,
            "symbols_with_any_decision_change": [], "symbols_with_stack_change": [],
        }
        OUT_CSV.write_text("symbol\n", encoding="utf-8")
        OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2)); return

    subset_ready = ready.loc[ready["ticker"].astype(str).isin(affected_symbols)].copy()
    sector_map = pd.DataFrame({
        "symbol": affected_symbols,
        "sector": [None] * len(affected_symbols),
        "industry": [None] * len(affected_symbols),
        "sector_benchmark": [None] * len(affected_symbols),
    })
    built = build_feature_store_from_r2(sector_map=sector_map, ready=subset_ready, manifest=ready_manifest)
    features = built["features"].sort_values(["symbol", "date"]).reset_index(drop=True)

    baseline_decided = compute_decision_layer(compute_hard_filter(features))
    baseline = _latest_view(baseline_decided)
    as_of = baseline["date"].max()

    state = state.rename(columns={"ticker": "symbol", **{f"ema{p}": f"shared_ema{p}" for p in PERIODS}})
    state = state.loc[state["symbol"].isin(affected_symbols), ["symbol", "as_of_date", *(f"shared_ema{p}" for p in PERIODS)]]
    if state["symbol"].duplicated().any():
        raise RuntimeError("Shared EMA ticker is not unique")

    patched = features.copy()
    latest_mask = patched["date"].eq(as_of)
    latest_rows = patched.loc[latest_mask].copy().merge(state, on="symbol", how="left", validate="one_to_one")
    if latest_rows["shared_ema20"].isna().any():
        raise RuntimeError("Missing shared EMA for an affected latest symbol")
    if not latest_rows["date"].eq(latest_rows["as_of_date"]).all():
        bad = latest_rows.loc[~latest_rows["date"].eq(latest_rows["as_of_date"]), "symbol"].tolist()
        raise RuntimeError(f"Shared EMA/latest date mismatch: {bad}")
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

    migrated = _latest_view(compute_decision_layer(compute_hard_filter(patched)))
    cols = ["symbol", "ema_stack_aligned", "trend_status", "hard_filter_status", "investability_status", "tradability_status", "candidate", "actionable"]
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
        "affected_symbols_evaluated": int(len(comp)),
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
