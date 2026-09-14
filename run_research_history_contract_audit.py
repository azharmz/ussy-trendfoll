"""PROB-019 one-shot architecture audit for the research-history contract.

The audit is observational. It validates source provenance, no-future trimming,
canonical long-history EMA equivalence, and latest Stage agreement without
changing any signal or trading rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import feature_engine as fe
from r2_ready import load_ready_dataset, to_feature_contract as ready_to_feature
from shared_ema_state import load_shared_ema_state
from research_history import (
    DEFAULT_MIN_PREROLL_BARS,
    build_research_feature_store,
    evaluation_rows,
    load_research_history,
)

SAMPLE_SIZE = 100
SOURCE_TOLERANCE = 0.0025  # same 0.25% compatibility guard used in PROB-018
OUT = Path("research_history_contract_audit.json")


def deterministic_sample(authority: pd.DataFrame) -> pd.DataFrame:
    ranked = authority.copy()
    ranked["_rank"] = ranked.apply(
        lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(), axis=1
    )
    return ranked.sort_values("_rank").head(SAMPLE_SIZE).drop(columns="_rank")


def _latest_stage_from_ready(ready_sample: pd.DataFrame) -> pd.DataFrame:
    raw = ready_to_feature(ready_sample)
    rows = []
    for symbol, group in raw.groupby("symbol", sort=True):
        g = group.sort_values("date").reset_index(drop=True)
        weekly = fe.compute_weekly_stage_features(g).sort_values("date")
        latest_date = pd.Timestamp(g["date"].max())
        eligible = weekly.loc[pd.to_datetime(weekly["date"]) <= latest_date]
        if eligible.empty:
            rows.append({"symbol": symbol, "ready_stage": None})
        else:
            rows.append({"symbol": symbol, "ready_stage": eligible.iloc[-1]["stage"]})
    return pd.DataFrame(rows)


def main() -> None:
    ready, ready_manifest = load_ready_dataset()
    ready = ready.copy()
    ready["security_id"] = ready["security_id"].astype(str)
    authority = ready[["security_id", "ticker"]].drop_duplicates()
    sample = deterministic_sample(authority)
    sample_ids = sample["security_id"].tolist()
    ready_sample = ready.loc[ready["security_id"].isin(sample_ids)].copy()
    evaluation_end = pd.Timestamp(ready_sample["date"].max()).normalize()
    evaluation_start = pd.Timestamp(ready_sample["date"].min()).normalize()

    history, history_report = load_research_history(
        sample_ids,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        min_preroll_bars=DEFAULT_MIN_PREROLL_BARS,
        ready=ready,
        ready_manifest=ready_manifest,
    )

    # Source compatibility on exact overlapping security/date rows.
    overlap = history.merge(
        ready_sample[["security_id", "date", "close", "adj_close"]],
        on=["security_id", "date"],
        suffixes=("_history", "_ready"),
        how="inner",
        validate="one_to_one",
    )
    for col in ["close", "adj_close"]:
        denom = overlap[f"{col}_ready"].abs().replace(0, np.nan)
        overlap[f"{col}_rel_diff"] = (
            overlap[f"{col}_history"] - overlap[f"{col}_ready"]
        ).abs() / denom
    overlap["source_compatible"] = (
        (overlap["close_rel_diff"] <= SOURCE_TOLERANCE)
        & (overlap["adj_close_rel_diff"] <= SOURCE_TOLERANCE)
    )

    built = build_research_feature_store(history)
    research = built["features"].sort_values(["symbol", "date"])
    eligible = evaluation_rows(research)
    latest_research = research.groupby("symbol", sort=False).tail(1).copy()

    # Exact canonical EMA equivalence against the governed production state.
    shared, shared_manifest = load_shared_ema_state()
    shared = shared.loc[shared["security_id"].astype(str).isin(sample_ids)].copy()
    shared["as_of_date"] = pd.to_datetime(shared["as_of_date"]).dt.tz_localize(None).dt.normalize()
    sid_by_symbol = dict(zip(sample["ticker"].astype(str), sample["security_id"].astype(str)))
    latest_research["security_id"] = latest_research["symbol"].map(sid_by_symbol)
    ema_cmp = latest_research[
        ["security_id", "symbol", "date", "close_adj", "ema20", "ema50", "ema150", "ema200", "ema_stack_aligned"]
    ].merge(
        shared[["security_id", "as_of_date", "last_price", "ema20", "ema50", "ema150", "ema200"]],
        on="security_id",
        suffixes=("_research", "_shared"),
        how="inner",
        validate="one_to_one",
    )
    ema_cmp["date_match"] = pd.to_datetime(ema_cmp["date"]).dt.normalize().eq(ema_cmp["as_of_date"])
    ema_numeric_failures = 0
    max_abs_error = {}
    for period in [20, 50, 150, 200]:
        diff = (ema_cmp[f"ema{period}_research"] - ema_cmp[f"ema{period}_shared"]).abs()
        max_abs_error[f"ema{period}"] = float(diff.max()) if len(diff) else None
        ema_numeric_failures += int((diff > 1e-10).sum())
    price_diff = (ema_cmp["close_adj"] - ema_cmp["last_price"]).abs()
    ema_numeric_failures += int((price_diff > 1e-10).sum())

    e20 = ema_cmp["ema20_shared"]
    e50 = ema_cmp["ema50_shared"]
    e150 = ema_cmp["ema150_shared"]
    e200 = ema_cmp["ema200_shared"]
    shared_stack = ema_cmp["last_price"] > e20
    shared_stack &= e20 > e50
    shared_stack &= e50 > e150
    shared_stack &= e150 > e200
    stack_mismatches = int(ema_cmp["ema_stack_aligned"].ne(shared_stack).sum())

    # Weekly Stage is still raw-close based in production. Verify that using full
    # pre-roll does not change the latest classification versus the ready window.
    ready_stage = _latest_stage_from_ready(ready_sample)
    research_stage = latest_research[["symbol", "stage"]].rename(columns={"stage": "research_stage"})
    stage_cmp = ready_stage.merge(research_stage, on="symbol", how="inner", validate="one_to_one")
    stage_valid = stage_cmp.dropna(subset=["ready_stage", "research_stage"])
    stage_mismatches = int(stage_valid["ready_stage"].ne(stage_valid["research_stage"]).sum())

    source_mismatches = int((~overlap["source_compatible"]).sum())
    missing_shared = int(len(sample_ids) - len(ema_cmp))
    status = "PASS"
    reasons = []
    if source_mismatches:
        status = "BLOCKED"
        reasons.append("SOURCE_COMPATIBILITY_MISMATCH")
    if missing_shared or not ema_cmp["date_match"].all() or ema_numeric_failures or stack_mismatches:
        status = "BLOCKED"
        reasons.append("CANONICAL_EMA_EQUIVALENCE_FAILURE")
    if stage_mismatches:
        status = "BLOCKED"
        reasons.append("LATEST_STAGE_MISMATCH")
    if history_report.eligible_securities < 1:
        status = "BLOCKED"
        reasons.append("NO_ELIGIBLE_RESEARCH_ROWS")

    summary = {
        "status": status,
        "reasons": reasons,
        "governance": "OBSERVATIONAL_ARCHITECTURE_GATE_NO_STRATEGY_CHANGE",
        "ready_snapshot_date": ready_manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic security_id|ticker",
        "sample_size": int(len(sample)),
        "history_contract": history_report.__dict__,
        "source_overlap_rows": int(len(overlap)),
        "source_compatible_rows": int(overlap["source_compatible"].sum()),
        "source_mismatches": source_mismatches,
        "source_tolerance": SOURCE_TOLERANCE,
        "research_feature_rows": int(len(research)),
        "research_eligible_rows": int(len(eligible)),
        "research_eligible_securities": int(eligible["symbol"].nunique()),
        "canonical_ema": {
            "price_basis": shared_manifest.get("price_basis"),
            "shared_rows_compared": int(len(ema_cmp)),
            "missing_shared_rows": missing_shared,
            "date_mismatches": int((~ema_cmp["date_match"]).sum()),
            "numeric_failures": int(ema_numeric_failures),
            "stack_mismatches": stack_mismatches,
            "max_abs_error": max_abs_error,
        },
        "latest_stage": {
            "comparable_symbols": int(len(stage_valid)),
            "mismatches": stage_mismatches,
        },
        "no_lookahead_rule": "history is trimmed to evaluation_end before feature computation",
        "evaluation_rule": "signals/outcomes may use only research_eligible rows after feature computation",
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    if status != "PASS":
        raise RuntimeError(f"PROB-019 architecture gate failed: {reasons}")


if __name__ == "__main__":
    main()
