"""Shadow-gate production migration to canonical shared EMA(adj_close).

No database writes, Telegram messages, position mutations, or threshold tuning.
Build the R2 feature store once, then compare latest decisions between:
1) legacy finite-window EMA(close_raw), and
2) governed shared recursive EMA(adj_close).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from decision_layer import compute_decision_layer
from hard_filter import STATUS_RANK, compute_hard_filter
from r2_feature_engine import build_feature_store_from_r2
from r2_ready import load_ready_dataset

OUT = Path("canonical_ema_migration_shadow.json")
PERIODS = (20, 50, 150, 200)


def _legacy_terminal_state(ready: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in ready.groupby("security_id", sort=True):
        g = group.sort_values("date")
        prices = pd.to_numeric(g["close"], errors="raise").astype(float)
        row = {"symbol": str(g["ticker"].iloc[-1]), "date": pd.Timestamp(g["date"].iloc[-1])}
        for p in PERIODS:
            row[f"ema{p}"] = float(prices.ewm(span=p, adjust=False).mean().iloc[-1])
        row["ema_stack_aligned"] = bool(
            float(prices.iloc[-1]) > row["ema20"] > row["ema50"] > row["ema150"] > row["ema200"]
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _replace_terminal(features: pd.DataFrame, terminal: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    t = terminal.copy()
    t["date"] = pd.to_datetime(t["date"]).dt.tz_localize(None).dt.normalize()
    lookup = t.set_index(["symbol", "date"])
    idx = out.sort_values(["symbol", "date"]).groupby("symbol", sort=False).tail(1).index
    for i in idx:
        key = (str(out.at[i, "symbol"]), pd.Timestamp(out.at[i, "date"]))
        row = lookup.loc[key]
        for p in PERIODS:
            out.at[i, f"ema{p}"] = float(row[f"ema{p}"])
        out.at[i, "ema_stack_aligned"] = bool(row["ema_stack_aligned"])
    return out


def _latest_decision(features: pd.DataFrame) -> pd.DataFrame:
    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"])
    as_of = decided["date"].max()
    return decided[decided["date"] == as_of].copy()


def _candidate_set(df: pd.DataFrame) -> set[str]:
    return set(df.loc[df["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"], "symbol"])


def _actionable_set(df: pd.DataFrame) -> set[str]:
    return set(df.loc[(df["investability_status"] == "PASS") & (df["tradability_status"] == "PASS"), "symbol"])


def main() -> None:
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().astype(str).unique())
    sector_map = pd.DataFrame({
        "symbol": universe,
        "sector": [None] * len(universe),
        "industry": [None] * len(universe),
        "sector_benchmark": [None] * len(universe),
    })
    built = build_feature_store_from_r2(sector_map=sector_map, ready=ready, manifest=manifest)
    canonical_features = built["features"].copy()
    legacy_features = _replace_terminal(canonical_features, _legacy_terminal_state(ready))

    legacy = _latest_decision(legacy_features)
    canonical = _latest_decision(canonical_features)
    cols = ["symbol", "ema_stack_aligned", "trend_status", "hard_filter_status", "investability_status", "tradability_status"]
    merged = legacy[cols].merge(canonical[cols], on="symbol", suffixes=("_legacy", "_canonical"), validate="one_to_one")

    summary = {
        "status": "PASS",
        "governance": "MIGRATION_SHADOW_NO_PRODUCTION_WRITES",
        "as_of_date": str(pd.Timestamp(canonical["date"].max()).date()),
        "ready_securities": int(ready["security_id"].nunique()),
        "latest_symbols_compared": int(len(merged)),
        "canonical_price_basis": "adj_close",
        "legacy_price_basis": "close",
        "shared_ema_report": built["shared_ema_report"],
        "ema_stack_changes": int(merged["ema_stack_aligned_legacy"].ne(merged["ema_stack_aligned_canonical"]).sum()),
        "trend_status_changes": int(merged["trend_status_legacy"].ne(merged["trend_status_canonical"]).sum()),
        "hard_filter_status_changes": int(merged["hard_filter_status_legacy"].ne(merged["hard_filter_status_canonical"]).sum()),
        "investability_status_changes": int(merged["investability_status_legacy"].ne(merged["investability_status_canonical"]).sum()),
        "tradability_status_changes": int(merged["tradability_status_legacy"].ne(merged["tradability_status_canonical"]).sum()),
        "legacy_candidates": len(_candidate_set(legacy)),
        "canonical_candidates": len(_candidate_set(canonical)),
        "candidate_membership_changes": len(_candidate_set(legacy) ^ _candidate_set(canonical)),
        "legacy_actionable": len(_actionable_set(legacy)),
        "canonical_actionable": len(_actionable_set(canonical)),
        "actionable_membership_changes": len(_actionable_set(legacy) ^ _actionable_set(canonical)),
    }
    if summary["tradability_status_changes"] != 0:
        summary["status"] = "BLOCKED_UNEXPECTED_TRADABILITY_CHANGE"
        OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        raise RuntimeError("EMA-only migration unexpectedly changed Tradability")

    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
