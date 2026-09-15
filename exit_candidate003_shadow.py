"""Non-decisioning production shadow for frozen EXIT-CAND-003.

Contract: exit-cand-003-shadow-v1.
This module may persist hypothetical state, but MUST NOT mutate `positions`
or influence production exit decisions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SHADOW_CONTRACT_VERSION = "exit-cand-003-shadow-v1"
INITIAL_ATR_MULT = 2.0
CHAND_PERIOD = 22
CHAND_ATR_MULT = 3.0
MAX_HOLDING_DAYS = 45
TOL = 1e-9


def _true_range(g: pd.DataFrame) -> pd.Series:
    prev_close = g["close_raw"].shift(1)
    return pd.concat(
        [
            g["high_raw"] - g["low_raw"],
            (g["high_raw"] - prev_close).abs(),
            (g["low_raw"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


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


def _active_shadow_rows(client):
    return (
        client.table("exit_candidate003_shadow")
        .select("*")
        .eq("contract_version", SHADOW_CONTRACT_VERSION)
        .eq("status", "active")
        .execute().data
        or []
    )


def register_missing_shadows(client, feature_history: pd.DataFrame, as_of_date):
    """Register shadows only after the real T+1 Open is observable."""
    positions = (
        client.table("positions")
        .select("id,symbol,entry_date,realistic_entry_price,atr14_at_entry,status,exit_date,exit_price")
        .execute().data
        or []
    )
    existing = (
        client.table("exit_candidate003_shadow")
        .select("position_id")
        .eq("contract_version", SHADOW_CONTRACT_VERSION)
        .execute().data
        or []
    )
    existing_ids = {int(r["position_id"]) for r in existing}
    history = feature_history.copy()
    history["date"] = pd.to_datetime(history["date"]).dt.normalize()
    rows = []
    for p in positions:
        if int(p["id"]) in existing_ids:
            continue
        entry = p.get("realistic_entry_price")
        atr14 = p.get("atr14_at_entry")
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
            "position_id": int(p["id"]),
            "symbol": symbol,
            "contract_version": SHADOW_CONTRACT_VERSION,
            "signal_date": t0.date().isoformat(),
            "shadow_entry_date": entry_date,
            "shadow_entry_price": float(entry),
            "atr14_t0": float(atr14),
            "initial_stop": initial_stop,
            "operative_stop": initial_stop,
            "status": "active",
        })
    if rows:
        client.table("exit_candidate003_shadow").insert(rows).execute()
        print(f"[shadow003] registered {len(rows)} shadow position(s).")
    return rows


def update_shadows(client, feature_history: pd.DataFrame, as_of_date, all_trading_dates):
    """Advance shadow state. Never writes to production `positions`."""
    active = _active_shadow_rows(client)
    if not active:
        return []
    history = add_frozen_shadow_features(feature_history)
    history["date"] = pd.to_datetime(history["date"]).dt.normalize()
    today = pd.Timestamp(as_of_date).normalize()
    latest = history[history.date == today].drop_duplicates("symbol").set_index("symbol")
    hypothetical_exits = []

    for s in active:
        symbol = s["symbol"]
        if symbol not in latest.index:
            continue
        row = latest.loc[symbol]
        operative = float(s["operative_stop"])
        initial = float(s["initial_stop"])
        if operative < initial - TOL:
            raise RuntimeError(f"shadow stop decreased below initial stop: {symbol}")

        op, lo, hi, close = map(float, (row.open_raw, row.low_raw, row.high_raw, row.close_raw))
        days = _trading_days_between(s["shadow_entry_date"], today, all_trading_dates) + 1
        reason = None
        exit_price = None
        if op <= operative:
            reason, exit_price = "risk_stop_gap", op
            if abs(exit_price - op) > TOL:
                raise RuntimeError("gap fill must equal observed Open")
        elif lo <= operative:
            reason, exit_price = "risk_stop_touch", operative
            if exit_price < lo - TOL or exit_price > hi + TOL:
                raise RuntimeError("touch fill outside observed daily range")
        elif days >= MAX_HOLDING_DAYS:
            reason, exit_price = "observation_boundary", close
        elif pd.notna(row.get("ema20")) and close < float(row.ema20):
            reason, exit_price = "trend_exit", close

        update = {"last_session_date": today.date().isoformat(), "days_observed": days}
        if reason:
            update.update({
                "status": "exited",
                "hypothetical_exit_reason": reason,
                "hypothetical_exit_date": today.date().isoformat(),
                "hypothetical_exit_price": exit_price,
            })
            hypothetical_exits.append({"position_id": s["position_id"], "symbol": symbol, "reason": reason, "price": exit_price})
        else:
            # Ratchet only AFTER surviving today's execution/trend checks; it is
            # therefore operative no earlier than the next session.
            chand = row.get("shadow_chandelier")
            next_stop = operative
            if pd.notna(chand) and float(chand) < close and float(chand) > operative:
                next_stop = float(chand)
            if next_stop < operative - TOL:
                raise RuntimeError("shadow operative stop decreased")
            update["operative_stop"] = next_stop

        client.table("exit_candidate003_shadow").update(update).eq("id", s["id"]).execute()

    print(f"[shadow003] advanced {len(active)} active shadow(s); hypothetical exits={len(hypothetical_exits)}.")
    return hypothetical_exits


def run_shadow(client, feature_history: pd.DataFrame, as_of_date, all_trading_dates):
    """Run after production exit decisions so shadow cannot affect them."""
    register_missing_shadows(client, feature_history, as_of_date)
    return update_shadows(client, feature_history, as_of_date, all_trading_dates)
