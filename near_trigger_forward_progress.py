"""Forward-validation progress tracker for frozen NEAR_TRIGGER Cycle 1.

This module is observational. It recomputes progress from the decision history
and never changes Investability, Tradability, alerts, entry, or exits.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from hard_filter import STATUS_RANK
from near_trigger_shadow import add_near_trigger_shadow
from near_trigger_validation import (
    MIN_BREAKOUTS_5D,
    MIN_EPISODES,
    MIN_UNIQUE_SYMBOLS,
    STATUS_ACCUMULATING,
    evaluate_near_trigger_validation,
)

VALIDATION_START_DATE = pd.Timestamp("2026-09-15")


def _independent_breakout_onset(frame: pd.DataFrame) -> pd.Series:
    breakout = frame["has_breakout"].fillna(False).astype(bool)
    return breakout & (~breakout.shift(1, fill_value=False))


def _eligible_monitored(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["investability_status"].map(STATUS_RANK).fillna(0) >= STATUS_RANK["NEAR_PASS"]
    )


def _forward_result(rows: pd.DataFrame, pos: int) -> dict | None:
    """Return outcome for a start row when its frozen forward window is mature.

    The episode is mature when either:
    - an independent breakout onset occurs within T+1..T+5,
    - the setup becomes no longer monitored within T+1..T+5, or
    - five later trading observations for the symbol are available.
    """
    later = rows.iloc[pos + 1 : pos + 6]
    if later.empty:
        return None

    onset_offsets = [i + 1 for i, v in enumerate(later["breakout_onset"].tolist()) if bool(v)]
    invalid_offsets = [i + 1 for i, v in enumerate(later["eligible_monitored"].tolist()) if not bool(v)]
    first_onset = min(onset_offsets) if onset_offsets else None
    first_invalid = min(invalid_offsets) if invalid_offsets else None

    matured_early = first_onset is not None or first_invalid is not None
    if len(later) < 5 and not matured_early:
        return None

    invalid_before_breakout = (
        first_invalid is not None
        and (first_onset is None or first_invalid < first_onset)
    )
    return {
        "onset_1d": first_onset is not None and first_onset <= 1,
        "onset_2d": first_onset is not None and first_onset <= 2,
        "onset_3d": first_onset is not None and first_onset <= 3,
        "onset_5d": first_onset is not None and first_onset <= 5,
        "invalidation_before_breakout": invalid_before_breakout,
        "first_onset_offset": first_onset,
        "first_invalidation_offset": first_invalid,
    }


def collect_forward_validation(decided: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    work = add_near_trigger_shadow(decided).copy()
    work["date"] = pd.to_datetime(work["date"]).dt.normalize()
    work = work.sort_values(["symbol", "date"]).reset_index(drop=True)
    work["eligible_monitored"] = _eligible_monitored(work)

    episode_rows: list[dict] = []
    control_rows: list[dict] = []

    for symbol, group in work.groupby("symbol", sort=False):
        g = group.sort_values("date").reset_index(drop=True).copy()
        g["breakout_onset"] = _independent_breakout_onset(g)
        previous_shadow = g["near_trigger_shadow"].shift(1, fill_value=False).astype(bool)
        g["shadow_episode_start"] = g["near_trigger_shadow"].astype(bool) & (~previous_shadow)

        for pos, row in g.iterrows():
            if row["date"] < VALIDATION_START_DATE:
                continue
            result = _forward_result(g, pos)
            if result is None:
                continue

            if bool(row["shadow_episode_start"]):
                episode_rows.append({
                    "symbol": symbol,
                    "episode_start_date": row["date"].date().isoformat(),
                    "distance_to_prev_pivot_atr": float(row["distance_to_prev_pivot_atr"]),
                    **result,
                })

            is_control = (
                bool(row["eligible_monitored"])
                and not bool(row["has_breakout"])
                and pd.notna(row["distance_to_prev_pivot_atr"])
                and float(row["distance_to_prev_pivot_atr"]) > 0.60
            )
            if is_control:
                control_rows.append({
                    "symbol": symbol,
                    "date": row["date"].date().isoformat(),
                    "distance_to_prev_pivot_atr": float(row["distance_to_prev_pivot_atr"]),
                    **result,
                })

    episodes = pd.DataFrame(episode_rows)
    controls = pd.DataFrame(control_rows)

    shadow_episodes = len(episodes)
    unique_symbols = int(episodes["symbol"].nunique()) if not episodes.empty else 0
    shadow_breakouts_3d = int(episodes["onset_3d"].sum()) if not episodes.empty else 0
    shadow_breakouts_5d = int(episodes["onset_5d"].sum()) if not episodes.empty else 0
    control_episodes = len(controls)
    control_breakouts_3d = int(controls["onset_3d"].sum()) if not controls.empty else 0
    control_breakouts_5d = int(controls["onset_5d"].sum()) if not controls.empty else 0

    metrics = {
        "validation_start_date": VALIDATION_START_DATE.date().isoformat(),
        "shadow_episodes": shadow_episodes,
        "unique_symbols": unique_symbols,
        "shadow_breakouts_3d": shadow_breakouts_3d,
        "shadow_breakouts_5d": shadow_breakouts_5d,
        "control_episodes": control_episodes,
        "control_breakouts_3d": control_breakouts_3d,
        "control_breakouts_5d": control_breakouts_5d,
        "episode_target": MIN_EPISODES,
        "unique_symbol_target": MIN_UNIQUE_SYMBOLS,
        "breakout_5d_target": MIN_BREAKOUTS_5D,
    }

    evidence_ready = (
        shadow_episodes >= MIN_EPISODES
        and unique_symbols >= MIN_UNIQUE_SYMBOLS
        and shadow_breakouts_5d >= MIN_BREAKOUTS_5D
        and control_episodes > 0
    )

    if evidence_ready:
        verdict = evaluate_near_trigger_validation(metrics)
        metrics["status"] = verdict.status
        metrics["verdict"] = verdict.to_dict()
    else:
        metrics["status"] = STATUS_ACCUMULATING
        metrics["verdict"] = None

    return episodes, controls, metrics


def write_forward_validation_progress(
    decided: pd.DataFrame,
    progress_path: str = "near_trigger_validation_progress.json",
    episode_path: str = "near_trigger_validation_episodes.csv",
) -> dict:
    episodes, controls, metrics = collect_forward_validation(decided)
    Path(progress_path).write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    episodes.to_csv(episode_path, index=False)

    print(
        "[near_trigger validation] "
        f"{metrics['shadow_episodes']}/{MIN_EPISODES} episodes · "
        f"{metrics['unique_symbols']}/{MIN_UNIQUE_SYMBOLS} tickers · "
        f"{metrics['shadow_breakouts_5d']}/{MIN_BREAKOUTS_5D} onsets<=5d · "
        f"status={metrics['status']}"
    )
    return metrics
