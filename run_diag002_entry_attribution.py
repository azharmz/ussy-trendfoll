"""DIAG-002 — pre-registered observational entry-quality attribution.

No production thresholds or trading decisions are changed here.
Uses the governed PROB-019 research-history contract and the same independent
entry-ready onset definition as rebuilt DIAG-001.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

SAMPLE_SIZE = 100
EVENT_PATH = "diag002_entry_attribution_events.csv"
SUMMARY_PATH = "diag002_entry_attribution_summary.json"

CONTINUOUS = [
    "ret_tminus1_t0",
    "pivot_extension_atr_t0",
    "gap_t0close_t1open",
    "breakout_volume_percentile",
    "vcp_tightness",
]
CATEGORICAL = [
    "investability_status", "trend_status", "liquidity_status", "rs_status",
    "price_status", "regime_status", "market_regime", "has_tight_structure",
]
OUTCOMES = ["ret_t1open_t1close", "ret_t1open_t3close", "ret_t1open_t5close", "mfe_high_t5", "mae_low_t5"]


def _sample_security_ids(ready: pd.DataFrame, n: int = SAMPLE_SIZE) -> list[str]:
    pairs = ready[["security_id", "ticker"]].drop_duplicates().copy()
    pairs["security_id"] = pairs["security_id"].astype(str)
    pairs["ticker"] = pairs["ticker"].astype(str)
    pairs["rank"] = pairs.apply(
        lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(), axis=1
    )
    return pairs.sort_values(["rank", "security_id"]).head(n)["security_id"].tolist()


def _rho(a: pd.Series, b: pd.Series):
    pair = pd.concat([a, b], axis=1).dropna()
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return None
    return float(pair.iloc[:, 0].rank(method="average").corr(pair.iloc[:, 1].rank(method="average")))


def _outcome_summary(g: pd.DataFrame) -> dict:
    def med(c):
        x = g[c].dropna() if c in g else pd.Series(dtype=float)
        return None if x.empty else float(x.median())
    t5 = g["ret_t1open_t5close"].dropna()
    return {
        "n": int(len(g)),
        "t5_mature": int(len(t5)),
        "t1_median": med("ret_t1open_t1close"),
        "t3_median": med("ret_t1open_t3close"),
        "t5_median": med("ret_t1open_t5close"),
        "t5_positive_rate": None if t5.empty else float((t5 > 0).mean()),
        "mfe5_median": med("mfe_high_t5"),
        "mae5_median": med("mae_low_t5"),
    }


def _continuous_view(events: pd.DataFrame, col: str) -> dict:
    vals = events[col].dropna()
    result = {
        "n_nonmissing": int(len(vals)),
        "unique": int(vals.nunique()),
        "median": None if vals.empty else float(vals.median()),
        "q25": None if vals.empty else float(vals.quantile(.25)),
        "q75": None if vals.empty else float(vals.quantile(.75)),
        "spearman": {out: _rho(events[col], events[out]) for out in ["ret_t1open_t5close", "mfe_high_t5", "mae_low_t5"]},
        "quartiles": [],
    }
    work = events.dropna(subset=[col, "ret_t1open_t5close"]).copy()
    if len(work) >= 4 and work[col].nunique() >= 4:
        # labels=False remains valid when tied quantile edges collapse under
        # duplicates='drop'.  We label only the bins that actually exist rather
        # than allowing tied source values to crash the frozen diagnostic.
        codes = pd.qcut(work[col], 4, labels=False, duplicates="drop")
        work["bucket_code"] = codes
        for code, g in work.groupby("bucket_code", observed=True):
            row = _outcome_summary(g)
            row.update({"bucket": f"Q{int(code) + 1}", "source_median": float(g[col].median())})
            result["quartiles"].append(row)
    return result


def _categorical_view(events: pd.DataFrame, col: str) -> dict:
    work = events.loc[events[col].notna()].copy()
    levels = []
    for level, g in work.groupby(col, dropna=False, observed=True):
        row = _outcome_summary(g)
        row["level"] = str(level)
        levels.append(row)
    return {
        "n_nonmissing": int(len(work)),
        "levels_observed": int(work[col].nunique(dropna=True)),
        "identifiability": "NON_IDENTIFIABLE_BY_CONSTRUCTION_OR_CORPUS" if work[col].nunique(dropna=True) <= 1 else "DESCRIPTIVELY_IDENTIFIABLE",
        "levels": levels,
    }


def main() -> None:
    ready, manifest = load_ready_dataset()
    sample_ids = _sample_security_ids(ready)
    evaluation_end = manifest.get("snapshot_date") or str(pd.to_datetime(ready["date"]).max().date())
    history, history_report = load_research_history(
        sample_ids, evaluation_end=evaluation_end, min_preroll_bars=500,
        ready=ready, ready_manifest=manifest,
    )
    features = build_research_feature_store(history)["features"].sort_values(["symbol", "date"]).copy()
    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"]).copy()
    all_events = build_signal_path_events(decided)
    eligible = decided.loc[decided["research_eligible"].astype(bool), ["symbol", "date"]].rename(columns={"date": "t0_date"}).drop_duplicates()
    events = all_events.merge(eligible.assign(_eligible=True), on=["symbol", "t0_date"], how="inner").drop(columns="_eligible")

    for col in CONTINUOUS + CATEGORICAL + OUTCOMES:
        if col not in events:
            events[col] = np.nan

    positive_gap = events.loc[events["gap_t0close_t1open"].notna() & (events["gap_t0close_t1open"] > 0)].copy()
    summary = {
        "diagnostic": "DIAG-002",
        "status": "OBSERVATIONAL_ONLY_NO_PRODUCTION_CHANGE",
        "contract": "docs/DIAG_002_ENTRY_ATTRIBUTION_CONTRACT.md",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic security_id|ticker",
        "sample_size": len(sample_ids),
        "research_contract": asdict(history_report),
        "eligible_decision_rows": int(decided["research_eligible"].sum()),
        "all_full_history_onsets": int(len(all_events)),
        "eligible_onsets": int(len(events)),
        "t5_mature": int(events["ret_t1open_t5close"].notna().sum()),
        "whole_sample": _outcome_summary(events),
        "continuous": {col: _continuous_view(events, col) for col in CONTINUOUS},
        "positive_gap_only": _continuous_view(positive_gap, "gap_t0close_t1open") if not positive_gap.empty else {},
        "categorical": {col: _categorical_view(events, col) for col in CATEGORICAL},
        "governance": {
            "quartiles": "descriptive only; boundaries are not candidate thresholds",
            "causality": "not established",
            "survivorship": "current R2 readiness universe; not PIT historical membership",
            "authorization": "no entry/exit/filter/alert rule change authorized",
        },
    }
    events.to_csv(EVENT_PATH, index=False)
    Path(SUMMARY_PATH).write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
