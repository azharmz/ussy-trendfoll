"""Alert state transitions for USSY TrendFoll.

This layer interprets changes in existing Investability/Tradability outputs.
It does not change their definitions or thresholds.
"""
from __future__ import annotations

import pandas as pd

STATUS_RANK = {"FAIL": 0, "NEAR_PASS": 1, "PASS": 2}

NEW_WATCH = "NEW_WATCH"
NEAR_TRIGGER = "NEAR_TRIGGER"
ACTIONABLE = "ACTIONABLE"
LOST_TRADABILITY = "LOST_TRADABILITY"
INVALIDATED = "INVALIDATED"
DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
OUT_OF_UNIVERSE = "OUT_OF_UNIVERSE"


def is_monitored(row) -> bool:
    return STATUS_RANK.get(row.get("investability_status"), 0) >= STATUS_RANK["NEAR_PASS"]


def is_actionable(row) -> bool:
    return row.get("investability_status") == "PASS" and row.get("tradability_status") == "PASS"


def base_state(row) -> str:
    if not is_monitored(row):
        return INVALIDATED
    if is_actionable(row):
        return ACTIONABLE
    return NEAR_TRIGGER


def compute_alert_transitions(
    latest: pd.DataFrame,
    previous_watchlist: pd.DataFrame | None,
    current_universe: set[str] | list[str] | tuple[str, ...],
) -> list[dict]:
    """Compute meaningful changes against the common-date decision snapshot.

    ``current_universe`` is the current R2 READY membership, distinct from
    ``latest`` (members with a row on the common effective date). A previous
    symbol still in current READY but absent from ``latest`` is DATA_UNAVAILABLE;
    a previous symbol no longer in current READY is OUT_OF_UNIVERSE.
    """
    if latest.empty:
        return []

    universe = {str(symbol) for symbol in current_universe}
    current = {str(r["symbol"]): r for _, r in latest.iterrows()}
    if not set(current).issubset(universe):
        raise ValueError("latest contains symbols outside current R2 READY universe")

    previous = {} if previous_watchlist is None or previous_watchlist.empty else {
        str(r["symbol"]): r for _, r in previous_watchlist.iterrows()
    }
    previous_date = None if not previous else pd.Timestamp(previous_watchlist["date"].iloc[0]).date().isoformat()
    as_of_date = pd.Timestamp(latest["date"].max()).date().isoformat()
    events = []

    for symbol, row in sorted(current.items()):
        if not is_monitored(row):
            continue
        prev = previous.get(symbol)
        current_state = base_state(row)
        event = None
        prior_state = "UNSEEN"

        if prev is None:
            event = ACTIONABLE if current_state == ACTIONABLE else NEW_WATCH
        else:
            prior_state = base_state(prev)
            if current_state == ACTIONABLE and prior_state != ACTIONABLE:
                event = ACTIONABLE
            elif prior_state == ACTIONABLE and current_state != ACTIONABLE:
                event = LOST_TRADABILITY
            elif current_state == NEAR_TRIGGER and prior_state != NEAR_TRIGGER:
                event = NEAR_TRIGGER

        if event:
            events.append({
                "event": event,
                "symbol": symbol,
                "as_of_date": as_of_date,
                "previous_date": previous_date,
                "previous_state": prior_state,
                "current_state": current_state,
                "investability_status": row.get("investability_status"),
                "tradability_status": row.get("tradability_status"),
                "close_raw": row.get("close_raw"),
            })

    for symbol, prev in sorted(previous.items()):
        row = current.get(symbol)
        if row is None:
            absence_state = DATA_UNAVAILABLE if symbol in universe else OUT_OF_UNIVERSE
            events.append({
                "event": absence_state,
                "symbol": symbol,
                "as_of_date": as_of_date,
                "previous_date": previous_date,
                "previous_state": base_state(prev),
                "current_state": absence_state,
                "investability_status": None,
                "tradability_status": None,
                "close_raw": None,
            })
        elif not is_monitored(row):
            events.append({
                "event": INVALIDATED,
                "symbol": symbol,
                "as_of_date": as_of_date,
                "previous_date": previous_date,
                "previous_state": base_state(prev),
                "current_state": INVALIDATED,
                "investability_status": row.get("investability_status"),
                "tradability_status": row.get("tradability_status"),
                "close_raw": row.get("close_raw"),
            })

    order = {
        ACTIONABLE: 0,
        NEW_WATCH: 1,
        NEAR_TRIGGER: 2,
        LOST_TRADABILITY: 3,
        INVALIDATED: 4,
        DATA_UNAVAILABLE: 5,
        OUT_OF_UNIVERSE: 6,
    }
    return sorted(events, key=lambda e: (order[e["event"]], e["symbol"]))
