"""Audit whether governed shared EMA state can replace current TrendFoll EMA semantics.

Observational only. It never changes production decisions.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from r2_ready import load_ready_dataset
from shared_ema_state import PERIODS, load_shared_ema_state

OUT_JSON = Path("shared_ema_migration_audit.json")
OUT_CSV = Path("shared_ema_migration_rows.csv")


def _latest_finite_ema(ready: pd.DataFrame, price_col: str, label: str) -> pd.DataFrame:
    rows = []
    for sid, group in ready.groupby("security_id", sort=True):
        g = group.sort_values("date")
        prices = pd.to_numeric(g[price_col], errors="raise").astype(float)
        row = {
            "security_id": str(sid),
            "ticker": str(g["ticker"].iloc[-1]),
            "as_of_date": pd.Timestamp(g["date"].iloc[-1]),
            f"{label}_price": float(prices.iloc[-1]),
        }
        for p in PERIODS:
            row[f"{label}_ema{p}"] = float(prices.ewm(span=p, adjust=False).mean().iloc[-1])
        e20, e50, e150, e200 = (row[f"{label}_ema{p}"] for p in PERIODS)
        row[f"{label}_stack"] = bool(row[f"{label}_price"] > e20 > e50 > e150 > e200)
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    ready, ready_manifest = load_ready_dataset()
    state, ema_manifest = load_shared_ema_state()

    # Current TrendFoll semantics: feature_engine.compute_ema_features uses close_raw,
    # which maps from ready.close. This finite-window recreation matches the current
    # production stock-side calculation source and formula.
    legacy = _latest_finite_ema(ready, "close", "legacy_raw")
    adjusted = _latest_finite_ema(ready, "adj_close", "finite_adj")

    shared = state.rename(columns={
        "ticker": "shared_ticker",
        "as_of_date": "shared_as_of_date",
        "last_price": "shared_price",
        **{f"ema{p}": f"shared_ema{p}" for p in PERIODS},
    }).copy()
    e20, e50, e150, e200 = (shared[f"shared_ema{p}"] for p in PERIODS)
    shared["shared_stack"] = shared["shared_price"] > e20
    shared["shared_stack"] &= e20 > e50
    shared["shared_stack"] &= e50 > e150
    shared["shared_stack"] &= e150 > e200

    merged = legacy.merge(adjusted, on=["security_id", "ticker", "as_of_date"], how="outer", validate="one_to_one")
    merged = merged.merge(shared, on="security_id", how="outer", validate="one_to_one")
    merged["shared_as_of_date"] = pd.to_datetime(merged["shared_as_of_date"], errors="coerce")
    merged["date_match"] = merged["as_of_date"].eq(merged["shared_as_of_date"])
    merged["legacy_vs_shared_stack_mismatch"] = merged["legacy_raw_stack"].ne(merged["shared_stack"])
    merged["raw_vs_adj_finite_stack_mismatch"] = merged["legacy_raw_stack"].ne(merged["finite_adj_stack"])

    abs_errors = {}
    rel_errors = {}
    for p in PERIODS:
        diff = (merged[f"legacy_raw_ema{p}"] - merged[f"shared_ema{p}"]).abs()
        denom = merged[f"legacy_raw_ema{p}"].abs().replace(0, np.nan)
        abs_errors[f"ema{p}"] = float(diff.max(skipna=True))
        rel_errors[f"ema{p}"] = float((diff / denom).max(skipna=True))

    source_lineage_match = (
        ema_manifest.get("source_ready_parquet_key") == ready_manifest.get("parquet_key")
        and ema_manifest.get("source_ready_sha256") == ready_manifest.get("sha256")
    )
    shared_basis = ema_manifest.get("price_basis")
    current_basis = "close"
    basis_compatible = shared_basis == current_basis

    summary = {
        "status": "PASS" if basis_compatible and not merged["legacy_vs_shared_stack_mismatch"].any() else "BLOCKED",
        "reason": None if basis_compatible else "PRICE_BASIS_MISMATCH",
        "current_trendfoll_price_basis": current_basis,
        "shared_ema_price_basis": shared_basis,
        "ready_securities": int(ready["security_id"].nunique()),
        "shared_ema_securities": int(len(state)),
        "source_ready_lineage_match": bool(source_lineage_match),
        "as_of_date_mismatches": int((~merged["date_match"].fillna(False)).sum()),
        "legacy_vs_shared_stack_mismatches": int(merged["legacy_vs_shared_stack_mismatch"].fillna(True).sum()),
        "raw_vs_adj_finite_stack_mismatches": int(merged["raw_vs_adj_finite_stack_mismatch"].fillna(True).sum()),
        "max_abs_error_legacy_raw_vs_shared": abs_errors,
        "max_rel_error_legacy_raw_vs_shared": rel_errors,
        "governance": "OBSERVATIONAL_ONLY_NO_PRODUCTION_SWITCH",
    }

    merged.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
