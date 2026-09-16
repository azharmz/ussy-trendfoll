"""Persistent candidate lifecycle derived from watchlist history.

No new production table is required. The existing watchlist table already keeps
one row per (symbol, date); this module reconstructs a durable lifecycle summary
so candidates do not conceptually disappear when they leave the latest snapshot.
"""
from __future__ import annotations

import pandas as pd

from alert_state import base_state, INVALIDATED, DATA_UNAVAILABLE, OUT_OF_UNIVERSE
from hard_filter import STATUS_RANK


def build_candidate_lifecycle(
    history: pd.DataFrame,
    latest: pd.DataFrame,
    current_universe: set[str] | list[str] | tuple[str, ...],
) -> pd.DataFrame:
    columns = [
        "symbol", "first_watch_date", "last_watch_date", "watch_days",
        "ever_tradability_near_pass", "ever_tradability_pass",
        "last_watch_investability", "last_watch_tradability",
        "current_investability", "current_tradability", "current_state",
        "currently_monitored", "currently_actionable", "days_since_last_watch",
    ]
    if history is None or history.empty:
        return pd.DataFrame(columns=columns)

    universe = {str(symbol) for symbol in current_universe}
    h = history.copy()
    h["date"] = pd.to_datetime(h["date"]).dt.normalize()
    h = h.sort_values(["symbol", "date"])

    latest_by_symbol = {}
    if latest is not None and not latest.empty:
        latest_by_symbol = {
            str(r["symbol"]): r for _, r in latest.drop_duplicates("symbol").iterrows()
        }
        if not set(latest_by_symbol).issubset(universe):
            raise ValueError("latest contains symbols outside current R2 READY universe")
        as_of_date = pd.Timestamp(latest["date"].max()).normalize()
    else:
        as_of_date = h["date"].max()

    rows = []
    for symbol, g in h.groupby("symbol", sort=True):
        g = g.sort_values("date")
        last = g.iloc[-1]
        symbol_key = str(symbol)
        current = latest_by_symbol.get(symbol_key)

        if current is None:
            current_investability = None
            current_tradability = None
            current_state = DATA_UNAVAILABLE if symbol_key in universe else OUT_OF_UNIVERSE
            currently_monitored = False
            currently_actionable = False
        else:
            current_investability = current.get("investability_status")
            current_tradability = current.get("tradability_status")
            currently_monitored = (
                STATUS_RANK.get(current_investability, 0) >= STATUS_RANK["NEAR_PASS"]
            )
            current_state = base_state(current) if currently_monitored else INVALIDATED
            currently_actionable = current_state == "ACTIONABLE"

        rows.append({
            "symbol": symbol,
            "first_watch_date": g["date"].min().date().isoformat(),
            "last_watch_date": g["date"].max().date().isoformat(),
            "watch_days": int(g["date"].nunique()),
            "ever_tradability_near_pass": bool((g["tradability_status"] == "NEAR_PASS").any()),
            "ever_tradability_pass": bool((g["tradability_status"] == "PASS").any()),
            "last_watch_investability": last.get("investability_status"),
            "last_watch_tradability": last.get("tradability_status"),
            "current_investability": current_investability,
            "current_tradability": current_tradability,
            "current_state": current_state,
            "currently_monitored": bool(currently_monitored),
            "currently_actionable": bool(currently_actionable),
            "days_since_last_watch": int((as_of_date - g["date"].max()).days),
        })

    out = pd.DataFrame(rows, columns=columns)
    state_rank = {
        "ACTIONABLE": 0,
        "NEAR_TRIGGER": 1,
        "INVALIDATED": 2,
        "DATA_UNAVAILABLE": 3,
        "OUT_OF_UNIVERSE": 4,
    }
    out["_state_rank"] = out["current_state"].map(state_rank).fillna(9)
    return (
        out.sort_values(["_state_rank", "last_watch_date", "symbol"], ascending=[True, False, True])
        .drop(columns="_state_rank")
        .reset_index(drop=True)
    )


def write_candidate_lifecycle(
    history: pd.DataFrame,
    latest: pd.DataFrame,
    path: str,
    current_universe: set[str] | list[str] | tuple[str, ...],
) -> pd.DataFrame:
    lifecycle = build_candidate_lifecycle(history, latest, current_universe)
    lifecycle.to_csv(path, index=False)
    near_history = int(lifecycle["ever_tradability_near_pass"].sum()) if not lifecycle.empty else 0
    inactive = int((~lifecycle["currently_monitored"]).sum()) if not lifecycle.empty else 0
    print(
        f"[candidate lifecycle] {len(lifecycle)} historical symbols; "
        f"{near_history} pernah Tradability=NEAR_PASS; {inactive} saat ini tidak monitored."
    )
    return lifecycle
