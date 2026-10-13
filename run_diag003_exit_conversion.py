"""DIAG-003: observational exit conversion / give-back audit."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from decision_layer import compute_decision_layer
from exit_conversion import simulate_exit_conversion, summarize_exit_conversion
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events

SAMPLE_SIZE = 100
EVENT_PATH = "diag003_exit_conversion_events.csv"
SUMMARY_PATH = "diag003_exit_conversion_summary.json"


def _sample_security_ids(ready: pd.DataFrame, n: int = SAMPLE_SIZE) -> list[str]:
    pairs = ready[["security_id", "ticker"]].drop_duplicates().copy()
    pairs["security_id"] = pairs["security_id"].astype(str)
    pairs["ticker"] = pairs["ticker"].astype(str)
    pairs["rank"] = pairs.apply(
        lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(), axis=1
    )
    return pairs.sort_values(["rank", "security_id"]).head(n)["security_id"].tolist()


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
    eligible = decided.loc[decided["research_eligible"].astype(bool), ["symbol", "date"]].rename(
        columns={"date": "t0_date"}
    ).drop_duplicates()
    events = all_events.merge(eligible.assign(_eligible=True), on=["symbol", "t0_date"], how="inner").drop(
        columns="_eligible"
    )
    results = simulate_exit_conversion(decided, events)
    summary = {
        **summarize_exit_conversion(results),
        "contract": "docs/DIAG_003_EXIT_CONVERSION_CONTRACT.md",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic security_id|ticker",
        "sample_size": len(sample_ids),
        "research_contract": asdict(history_report),
        "eligible_decision_rows": int(decided["research_eligible"].sum()),
        "all_full_history_onsets": int(len(all_events)),
        "eligible_onsets": int(len(events)),
        "stop_atr_multiplier": 2.0,
        "max_holding_bars": 45,
        "early_failure_bars": 5,
        "production_change_authorized": False,
    }
    results.to_csv(EVENT_PATH, index=False)
    Path(SUMMARY_PATH).write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
