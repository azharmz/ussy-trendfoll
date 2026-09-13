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


def compute_alert_transitions(latest: pd.DataFrame, previous_watchlist: pd.DataFrame | None) -> list[dict]:
    """Compute meaningful changes between previous watchlist and today's full decision output."""
    if latest.empty:
        return []

    current = {str(r["symbol"]): r for _, r in latest.iterrows()}
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
        if row is None or not is_monitored(row):
            events.append({
                "event": INVALIDATED,
                "symbol": symbol,
                "as_of_date": as_of_date,
                "previous_date": previous_date,
                "previous_state": base_state(prev),
                "current_state": INVALIDATED,
                "investability_status": None if row is None else row.get("investability_status"),
                "tradability_status": None if row is None else row.get("tradability_status"),
                "close_raw": None if row is None else row.get("close_raw"),
            })

    order = {ACTIONABLE: 0, NEW_WATCH: 1, NEAR_TRIGGER: 2, LOST_TRADABILITY: 3, INVALIDATED: 4}
    return sorted(events, key=lambda e: (order[e["event"]], e["symbol"]))
