"""Shadow-gate production migration to canonical shared EMA(adj_close).

No database writes, Telegram messages, position mutations, or threshold tuning.
First identify terminal rows whose EMA-stack changes; only those symbols need a
full downstream decision comparison because all others are provably unchanged
by an EMA-only migration.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import feature_engine as fe
from decision_layer import compute_decision_layer
from hard_filter import STATUS_RANK, compute_hard_filter
from r2_ready import load_ready_dataset, to_feature_contract
from r2_shared_ema import apply_shared_ema_terminal, load_shared_ema_state

OUT = Path("canonical_ema_migration_shadow.json")
PERIODS = (20, 50, 150, 200)


def _legacy_terminal_state(ready: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in ready.groupby("security_id", sort=True):
        g = group.sort_values("date")
        prices = pd.to_numeric(g["close"], errors="raise").astype(float)
        row = {
            "security_id": str(g["security_id"].iloc[-1]),
            "symbol": str(g["ticker"].iloc[-1]),
            "date": pd.Timestamp(g["date"].iloc[-1]).tz_localize(None).normalize(),
        }
        for p in PERIODS:
            row[f"ema{p}"] = float(prices.ewm(span=p, adjust=False).mean().iloc[-1])
        row["ema_stack_aligned"] = bool(
            float(prices.iloc[-1]) > row["ema20"] > row["ema50"] > row["ema150"] > row["ema200"]
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _canonical_terminal_state(state: pd.DataFrame) -> pd.DataFrame:
    out = state.rename(columns={"ticker": "symbol", "as_of_date": "date"}).copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    out["ema_stack_aligned"] = (
        (out["last_price"] > out["ema20"])
        & (out["ema20"] > out["ema50"])
        & (out["ema50"] > out["ema150"])
        & (out["ema150"] > out["ema200"])
    )
    return out


def _replace_terminal(features: pd.DataFrame, terminal: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.tz_localize(None).dt.normalize()
    lookup = terminal.set_index(["symbol", "date"])
    idx = out.sort_values(["symbol", "date"]).groupby("symbol", sort=False).tail(1).index
    for i in idx:
        key = (str(out.at[i, "symbol"]), pd.Timestamp(out.at[i, "date"]))
        row = lookup.loc[key]
        for p in PERIODS:
            out.at[i, f"ema{p}"] = float(row[f"ema{p}"])
        out.at[i, "ema_stack_aligned"] = bool(row["ema_stack_aligned"])
    return out


def _build_subset_features(ready_subset: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    raw_universe = to_feature_contract(ready_subset)
    raw_universe["date"] = pd.to_datetime(raw_universe["date"]).astype("datetime64[ns]")
    sector_map = pd.DataFrame({
        "symbol": symbols,
        "sector": [None] * len(symbols),
        "industry": [None] * len(symbols),
        "sector_benchmark": [None] * len(symbols),
    })
    original_download_universe = fe.download_universe
    original_download_raw_ohlcv = fe.download_raw_ohlcv
    original_earnings = fe.compute_days_to_next_earnings

    def normalize_download(*args, **kwargs):
        df = original_download_raw_ohlcv(*args, **kwargs)
        if not df.empty and "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
        return df

    try:
        fe.download_universe = lambda _: raw_universe.copy()
        fe.download_raw_ohlcv = normalize_download
        fe.compute_days_to_next_earnings = lambda *args, **kwargs: None
        return fe.build_feature_store(symbols, sector_map=sector_map)["features"]
    finally:
        fe.download_universe = original_download_universe
        fe.download_raw_ohlcv = original_download_raw_ohlcv
        fe.compute_days_to_next_earnings = original_earnings


def _latest_decision(features: pd.DataFrame) -> pd.DataFrame:
    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"])
    terminal_idx = decided.groupby("symbol", sort=False)["date"].idxmax()
    return decided.loc[terminal_idx].copy()


def _candidate_set(df: pd.DataFrame) -> set[str]:
    return set(df.loc[df["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"], "symbol"])


def _actionable_set(df: pd.DataFrame) -> set[str]:
    return set(df.loc[(df["investability_status"] == "PASS") & (df["tradability_status"] == "PASS"), "symbol"])


def main() -> None:
    ready, ready_manifest = load_ready_dataset()
    state, ema_manifest = load_shared_ema_state()

    legacy_terminal = _legacy_terminal_state(ready)
    canonical_terminal = _canonical_terminal_state(state)
    stack_compare = legacy_terminal[["security_id", "symbol", "date", "ema_stack_aligned"]].merge(
        canonical_terminal[["security_id", "symbol", "date", "ema_stack_aligned"]],
        on=["security_id", "symbol", "date"],
        suffixes=("_legacy", "_canonical"),
        validate="one_to_one",
    )
    stack_compare["changed"] = stack_compare["ema_stack_aligned_legacy"].ne(stack_compare["ema_stack_aligned_canonical"])
    affected = sorted(stack_compare.loc[stack_compare["changed"], "symbol"].tolist())

    if affected:
        ready_subset = ready[ready["ticker"].astype(str).isin(affected)].copy()
        state_subset = state[state["ticker"].astype(str).isin(affected)].copy()
        base_features = _build_subset_features(ready_subset, affected)
        canonical_features, ema_report = apply_shared_ema_terminal(
            base_features,
            ready_subset,
            ready_manifest,
            state=state_subset,
            ema_manifest=ema_manifest,
        )
        legacy_features = _replace_terminal(base_features, legacy_terminal[legacy_terminal["symbol"].isin(affected)])
        legacy = _latest_decision(legacy_features)
        canonical = _latest_decision(canonical_features)
        cols = ["symbol", "ema_stack_aligned", "trend_status", "hard_filter_status", "investability_status", "tradability_status"]
        merged = legacy[cols].merge(canonical[cols], on="symbol", suffixes=("_legacy", "_canonical"), validate="one_to_one")
        trend_changes = int(merged["trend_status_legacy"].ne(merged["trend_status_canonical"]).sum())
        hard_changes = int(merged["hard_filter_status_legacy"].ne(merged["hard_filter_status_canonical"]).sum())
        invest_changes = int(merged["investability_status_legacy"].ne(merged["investability_status_canonical"]).sum())
        trade_changes = int(merged["tradability_status_legacy"].ne(merged["tradability_status_canonical"]).sum())
        candidate_changes = len(_candidate_set(legacy) ^ _candidate_set(canonical))
        actionable_changes = len(_actionable_set(legacy) ^ _actionable_set(canonical))
    else:
        ema_report = {
            "price_basis": "adj_close",
            "terminal_rows_replaced": 0,
            "state_securities": int(len(state)),
            "source_ready_lineage_match": True,
            "equivalence_verified": int(ema_manifest["equivalence"]["verified"]),
            "production_parquet_key": ema_manifest["parquet_key"],
        }
        trend_changes = hard_changes = invest_changes = trade_changes = 0
        candidate_changes = actionable_changes = 0

    summary = {
        "status": "PASS" if trade_changes == 0 else "BLOCKED_UNEXPECTED_TRADABILITY_CHANGE",
        "governance": "MIGRATION_SHADOW_NO_PRODUCTION_WRITES",
        "ready_securities": int(ready["security_id"].nunique()),
        "canonical_price_basis": "adj_close",
        "legacy_price_basis": "close",
        "source_ready_lineage_match": (
            ema_manifest.get("source_ready_parquet_key") == ready_manifest.get("parquet_key")
            and ema_manifest.get("source_ready_sha256") == ready_manifest.get("sha256")
        ),
        "ema_stack_changes": int(len(affected)),
        "affected_symbols": affected,
        "affected_symbols_downstream_compared": int(len(affected)),
        "trend_status_changes": trend_changes,
        "hard_filter_status_changes": hard_changes,
        "investability_status_changes": invest_changes,
        "tradability_status_changes": trade_changes,
        "candidate_membership_changes": candidate_changes,
        "actionable_membership_changes": actionable_changes,
        "shared_ema_report": ema_report,
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise RuntimeError("EMA-only migration unexpectedly changed Tradability")


if __name__ == "__main__":
    main()
