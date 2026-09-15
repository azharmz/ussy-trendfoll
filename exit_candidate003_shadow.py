"""Non-decisioning production shadow for frozen EXIT-CAND-003.

Contract: exit-cand-003-shadow-v1.
This module may persist hypothetical state/evidence, but MUST NOT mutate
`positions` or influence production exit decisions.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

SHADOW_CONTRACT_VERSION = "exit-cand-003-shadow-v1"
INITIAL_ATR_MULT = 2.0
CHAND_PERIOD = 22
CHAND_ATR_MULT = 3.0
MAX_HOLDING_DAYS = 45
TOL = 1e-9
SESSION_LEDGER_TABLE = "exit_candidate003_shadow_sessions"


def _true_range(g: pd.DataFrame) -> pd.Series:
    prev_close = g["close_raw"].shift(1)
    return pd.concat([
        g["high_raw"] - g["low_raw"],
        (g["high_raw"] - prev_close).abs(),
        (g["low_raw"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def add_frozen_shadow_features(history: pd.DataFrame) -> pd.DataFrame:
    """Add HH22, Wilder ATR22 and frozen Chandelier to feature history."""
    out = []
    for _, g in history.groupby("symbol", sort=False):
        g = g.sort_values("date").copy()
        tr = _true_range(g)
        atr22 = tr.ewm(alpha=1 / CHAND_PERIOD, adjust=False, min_periods=CHAND_PERIOD).mean()
        hh22 = g["high_raw"].rolling(CHAND_PERIOD, min_periods=CHAND_PERIOD).max()
        g["shadow_hh22"] = hh22
        g["shadow_wilder_atr22"] = atr22
        g["shadow_chandelier"] = hh22 - CHAND_ATR_MULT * atr22
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else history.copy()


def _trading_days_between(entry_date, as_of_date, trading_dates) -> int:
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(trading_dates)).unique()))
    return int(((dates > pd.Timestamp(entry_date)) & (dates <= pd.Timestamp(as_of_date))).sum())


def _optional_float(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def _active_shadow_rows(client):
    return (client.table("exit_candidate003_shadow").select("*")
            .eq("contract_version", SHADOW_CONTRACT_VERSION)
            .eq("status", "active").execute().data or [])


def _production_position_map(client):
    rows = (client.table("positions")
            .select("id,status,exit_date,exit_price")
            .execute().data or [])
    return {int(r["id"]): r for r in rows}


def _evaluate_session(s: dict, row: pd.Series, today, all_trading_dates) -> tuple[dict, dict]:
    """Pure frozen session evaluation; returns mutable state update + evidence."""
    operative = float(s["operative_stop"])
    initial = float(s["initial_stop"])
    if operative < initial - TOL:
        raise RuntimeError(f"shadow stop decreased below initial stop: {s['symbol']}")

    op, lo, hi, close = map(float, (row.open_raw, row.low_raw, row.high_raw, row.close_raw))
    if hi < lo or not (lo - TOL <= op <= hi + TOL) or not (lo - TOL <= close <= hi + TOL):
        raise RuntimeError(f"invalid OHLC evidence: {s['symbol']} {today}")

    days = _trading_days_between(s["shadow_entry_date"], today, all_trading_dates) + 1
    reason = None
    exit_price = None

    # Frozen execution ordering: gap must be evaluated before intraday touch.
    if op <= operative:
        reason, exit_price = "risk_stop_gap", op
    elif lo <= operative:
        reason, exit_price = "risk_stop_touch", operative
        if exit_price < lo - TOL or exit_price > hi + TOL:
            raise RuntimeError("touch fill outside observed daily range")
    elif days >= MAX_HOLDING_DAYS:
        reason, exit_price = "observation_boundary", close
    elif pd.notna(row.get("ema20")) and close < float(row.ema20):
        reason, exit_price = "trend_exit", close

    chand = _optional_float(row.get("shadow_chandelier"))
    next_stop = None
    if reason is None:
        next_stop = operative
        # Session-t Chandelier may only arm t+1 after session t survives.
        if chand is not None and chand < close and chand > operative:
            next_stop = chand
        if next_stop < operative - TOL:
            raise RuntimeError("shadow operative stop decreased")

    update = {"last_session_date": pd.Timestamp(today).date().isoformat(), "days_observed": days}
    if reason:
        update.update({
            "status": "exited",
            "hypothetical_exit_reason": reason,
            "hypothetical_exit_date": pd.Timestamp(today).date().isoformat(),
            "hypothetical_exit_price": exit_price,
        })
    else:
        update["operative_stop"] = next_stop

    stop_source = "initial_2atr" if abs(operative - initial) <= TOL else "chandelier_ratchet"
    evidence = {
        "position_id": int(s["position_id"]),
        "shadow_id": int(s["id"]),
        "symbol": s["symbol"],
        "session_date": pd.Timestamp(today).date().isoformat(),
        "contract_version": SHADOW_CONTRACT_VERSION,
        "shadow_entry_date": str(s["shadow_entry_date"]),
        "shadow_entry_price": float(s["shadow_entry_price"]),
        "days_observed": days,
        "open_raw": op,
        "high_raw": hi,
        "low_raw": lo,
        "close_raw": close,
        "ema20": _optional_float(row.get("ema20")),
        "operative_stop_before": operative,
        "stop_source_before": stop_source,
        "shadow_hh22": _optional_float(row.get("shadow_hh22")),
        "shadow_wilder_atr22": _optional_float(row.get("shadow_wilder_atr22")),
        "shadow_chandelier": chand,
        "next_operative_stop": next_stop,
        "hypothetical_exit_reason": reason,
        "hypothetical_exit_price": exit_price,
        "gap_checked_first": True,
        "chandelier_arms_next_session": True,
    }
    return update, evidence


def _evidence_equivalent(existing: dict, payload: dict) -> bool:
    """Compare immutable evidence while tolerating PostgREST numeric strings."""
    for key, expected in payload.items():
        actual = existing.get(key)
        if expected is None:
            if actual is not None:
                return False
            continue
        if isinstance(expected, bool):
            if bool(actual) != expected:
                return False
            continue
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            try:
                if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=TOL):
                    return False
            except (TypeError, ValueError):
                return False
            continue
        if str(actual) != str(expected):
            return False
    return True


def _persist_session_evidence(client, payload: dict):
    """Append once; identical replay is idempotent, divergent replay is fatal."""
    existing = (client.table(SESSION_LEDGER_TABLE).select("*")
                .eq("position_id", payload["position_id"])
                .eq("session_date", payload["session_date"])
                .eq("contract_version", payload["contract_version"])
                .execute().data or [])
    if existing:
        if len(existing) != 1 or not _evidence_equivalent(existing[0], payload):
            raise RuntimeError(
                "divergent CAND-003 session evidence for invariant key "
                f"({payload['position_id']}, {payload['session_date']}, {payload['contract_version']})"
            )
        return "replay_identical"
    client.table(SESSION_LEDGER_TABLE).insert(payload).execute()
    return "inserted"


def register_missing_shadows(client, feature_history: pd.DataFrame, as_of_date):
    """Register shadows only after the real T+1 Open is observable."""
    positions = (client.table("positions")
                 .select("id,symbol,entry_date,realistic_entry_price,atr14_at_entry,status,exit_date,exit_price")
                 .execute().data or [])
    existing = (client.table("exit_candidate003_shadow").select("position_id")
                .eq("contract_version", SHADOW_CONTRACT_VERSION).execute().data or [])
    existing_ids = {int(r["position_id"]) for r in existing}
    history = feature_history.copy()
    history["date"] = pd.to_datetime(history["date"]).dt.normalize()
    rows = []
    for p in positions:
        if int(p["id"]) in existing_ids:
            continue
        entry, atr14 = p.get("realistic_entry_price"), p.get("atr14_at_entry")
        if entry is None or atr14 is None or float(atr14) <= 0:
            continue
        symbol = p["symbol"]
        t0 = pd.Timestamp(p["entry_date"]).normalize()
        after = history[(history.symbol == symbol) & (history.date > t0)].sort_values("date")
        if after.empty:
            continue
        entry_date = pd.Timestamp(after.iloc[0].date).date().isoformat()
        initial_stop = float(entry) - INITIAL_ATR_MULT * float(atr14)
        rows.append({
            "position_id": int(p["id"]), "symbol": symbol,
            "contract_version": SHADOW_CONTRACT_VERSION,
            "signal_date": t0.date().isoformat(), "shadow_entry_date": entry_date,
            "shadow_entry_price": float(entry), "atr14_t0": float(atr14),
            "initial_stop": initial_stop, "operative_stop": initial_stop, "status": "active",
        })
    if rows:
        client.table("exit_candidate003_shadow").insert(rows).execute()
        print(f"[shadow003] registered {len(rows)} shadow position(s).")
    return rows


def update_shadows(client, feature_history: pd.DataFrame, as_of_date, all_trading_dates):
    """Advance shadow state and append immutable evidence. Never writes positions."""
    active = _active_shadow_rows(client)
    if not active:
        return []
    history = add_frozen_shadow_features(feature_history)
    history["date"] = pd.to_datetime(history["date"]).dt.normalize()
    today = pd.Timestamp(as_of_date).normalize()
    latest = history[history.date == today].drop_duplicates("symbol").set_index("symbol")
    production = _production_position_map(client)
    hypothetical_exits = []
    advanced = 0

    for s in active:
        symbol = s["symbol"]
        if symbol not in latest.index:
            continue
        update, evidence = _evaluate_session(s, latest.loc[symbol], today, all_trading_dates)
        p = production.get(int(s["position_id"]), {})
        evidence.update({
            "production_status": p.get("status"),
            "production_exit_date": p.get("exit_date"),
            "production_exit_price": _optional_float(p.get("exit_price")),
        })

        # Evidence is persisted before mutable state advances. A divergent replay
        # therefore fails closed instead of silently rewriting history.
        _persist_session_evidence(client, evidence)
        client.table("exit_candidate003_shadow").update(update).eq("id", s["id"]).execute()
        advanced += 1
        if evidence["hypothetical_exit_reason"]:
            hypothetical_exits.append({
                "position_id": s["position_id"], "symbol": symbol,
                "reason": evidence["hypothetical_exit_reason"],
                "price": evidence["hypothetical_exit_price"],
            })

    print(f"[shadow003] advanced {advanced} active shadow(s); hypothetical exits={len(hypothetical_exits)}.")
    return hypothetical_exits


def run_shadow(client, feature_history: pd.DataFrame, as_of_date, all_trading_dates):
    """Run after production exit decisions so shadow cannot affect them."""
    register_missing_shadows(client, feature_history, as_of_date)
    return update_shadows(client, feature_history, as_of_date, all_trading_dates)
