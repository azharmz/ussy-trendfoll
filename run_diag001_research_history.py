"""Rebuild DIAG-001 using the governed PROB-019 research-history contract.

Observational only. Event definition and production thresholds are unchanged.
Independent entry-ready onset is detected on the full feature stream, then T0
is restricted to research_eligible rows. This prevents a warm-up boundary from
creating a false onset.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_ready import load_ready_dataset
from research_history import build_research_feature_store, load_research_history
from signal_path_diagnostic import build_signal_path_events, summarize_signal_path

SAMPLE_SIZE = 100
EVENT_PATH = "diag001_research_history_events.csv"
SUMMARY_PATH = "diag001_research_history_summary.json"


def _sample_security_ids(ready: pd.DataFrame, n: int = SAMPLE_SIZE) -> list[str]:
    pairs = ready[["security_id", "ticker"]].drop_duplicates().copy()
    pairs["security_id"] = pairs["security_id"].astype(str)
    pairs["ticker"] = pairs["ticker"].astype(str)
    pairs["rank"] = pairs.apply(
        lambda r: hashlib.sha256(f"{r['security_id']}|{r['ticker']}".encode()).hexdigest(), axis=1
    )
    return pairs.sort_values(["rank", "security_id"]).head(n)["security_id"].tolist()


def _quartile_table(events: pd.DataFrame, source: str) -> list[dict]:
    work = events.dropna(subset=[source, "ret_t1open_t5close"]).copy()
    if len(work) < 4:
        return []
    work["quartile"] = pd.qcut(work[source], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
    rows = []
    for q, g in work.groupby("quartile", observed=True):
        rows.append({
            "quartile": str(q),
            "n": int(len(g)),
            "source_median": float(g[source].median()),
            "t5_median": float(g["ret_t1open_t5close"].median()),
            "t5_positive_rate": float((g["ret_t1open_t5close"] > 0).mean()),
            "mfe5_median": float(g["mfe_high_t5"].median()),
            "mae5_median": float(g["mae_low_t5"].median()),
        })
    return rows


def _spearman_no_scipy(left: pd.Series, right: pd.Series) -> float:
    # Spearman rho = Pearson correlation of ranks. Using average ranks matches
    # the standard tied-value convention without introducing a SciPy dependency.
    return float(left.rank(method="average").corr(right.rank(method="average")))


def main() -> None:
    ready, manifest = load_ready_dataset()
    sample_ids = _sample_security_ids(ready)
    evaluation_end = manifest.get("snapshot_date") or str(pd.to_datetime(ready["date"]).max().date())

    history, history_report = load_research_history(
        sample_ids,
        evaluation_end=evaluation_end,
        min_preroll_bars=500,
        ready=ready,
        ready_manifest=manifest,
    )
    built = build_research_feature_store(history)
    features = built["features"].sort_values(["symbol", "date"]).copy()

    # Compute decisions over the full feature stream so onset state can cross the
    # pre-roll/evaluation boundary correctly. Restriction happens at event T0.
    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"]).copy()
    all_events = build_signal_path_events(decided)

    eligible_keys = decided.loc[
        decided["research_eligible"].astype(bool), ["symbol", "date"]
    ].rename(columns={"date": "t0_date"}).drop_duplicates()
    events = all_events.merge(eligible_keys.assign(_eligible=True), on=["symbol", "t0_date"], how="inner")
    events = events.drop(columns=["_eligible"])

    summary = summarize_signal_path(events, eligible_rows=int(decided["research_eligible"].sum()))
    summary.update({
        "research_contract": asdict(history_report),
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "sample_method": "SHA256-ranked deterministic security_id|ticker",
        "sample_size": len(sample_ids),
        "all_full_history_onsets": int(len(all_events)),
        "eligible_onsets": int(len(events)),
        "onset_boundary_rule": "detect on full stream first; filter T0 to research_eligible second",
        "survivorship_boundary": "current R2 readiness universe; not PIT historical membership",
        "spearman": {
            "ret_tminus1_t0_vs_t5": None,
            "ret_tminus1_t0_vs_mfe5": None,
            "ret_tminus1_t0_vs_mae5": None,
        },
        "momentum_quartiles": _quartile_table(events, "ret_tminus1_t0"),
        "gap_quartiles": _quartile_table(events, "gap_t0close_t1open"),
    })

    mature = events.dropna(subset=["ret_tminus1_t0", "ret_t1open_t5close", "mfe_high_t5", "mae_low_t5"])
    if len(mature) >= 3:
        summary["spearman"] = {
            "ret_tminus1_t0_vs_t5": _spearman_no_scipy(mature["ret_tminus1_t0"], mature["ret_t1open_t5close"]),
            "ret_tminus1_t0_vs_mfe5": _spearman_no_scipy(mature["ret_tminus1_t0"], mature["mfe_high_t5"]),
            "ret_tminus1_t0_vs_mae5": _spearman_no_scipy(mature["ret_tminus1_t0"], mature["mae_low_t5"]),
        }

    events.to_csv(EVENT_PATH, index=False)
    Path(SUMMARY_PATH).write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
