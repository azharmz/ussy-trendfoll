"""DIAG-001 — observational TrendFoll signal-to-outcome diagnostics.

No production thresholds or trading decisions are changed here.
Primary unit = independent entry-ready onset (False -> True).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


EVENT_OUTPUT = "signal_path_events.csv"
SUMMARY_OUTPUT = "signal_path_summary.json"


def _safe_return(end, start):
    if pd.isna(end) or pd.isna(start) or float(start) == 0:
        return np.nan
    return float(end) / float(start) - 1.0


def _entry_ready(df: pd.DataFrame) -> pd.Series:
    return (
        df["hard_filter_status"].eq("PASS")
        & df["has_breakout"].fillna(False).astype(bool)
        & df["has_volume_confirmation"].fillna(False).astype(bool)
    )


def build_signal_path_events(decided: pd.DataFrame) -> pd.DataFrame:
    """Build one row per independent entry-ready onset from full decision history."""
    required = {
        "symbol", "date", "open_raw", "high_raw", "low_raw", "close_raw",
        "hard_filter_status", "investability_status", "tradability_status",
        "has_breakout", "has_volume_confirmation", "prev_pivot_high", "atr14",
    }
    missing = sorted(required - set(decided.columns))
    if missing:
        raise ValueError(f"DIAG-001 missing required columns: {missing}")

    df = decided.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    duplicates = df.duplicated(["symbol", "date"], keep=False)
    if duplicates.any():
        keys = df.loc[duplicates, ["symbol", "date"]].drop_duplicates()
        raise ValueError(f"DIAG-001 requires unique symbol+date rows; found {len(keys)} duplicate keys")

    df["entry_ready"] = _entry_ready(df)
    prior_ready = df.groupby("symbol")["entry_ready"].shift(1).fillna(False).astype(bool)
    df["entry_ready_onset"] = df["entry_ready"] & ~prior_ready

    events: list[dict[str, Any]] = []
    for symbol, rows in df.groupby("symbol", sort=False):
        rows = rows.reset_index(drop=True)
        onset_positions = rows.index[rows["entry_ready_onset"]].tolist()
        for pos in onset_positions:
            t0 = rows.iloc[pos]
            prev = rows.iloc[pos - 1] if pos >= 1 else None
            future = {n: rows.iloc[pos + n] if pos + n < len(rows) else None for n in range(1, 6)}
            t1 = future[1]

            t0_close = t0["close_raw"]
            prev_close = prev["close_raw"] if prev is not None else np.nan
            pivot = t0.get("prev_pivot_high")
            atr = t0.get("atr14")
            pivot_ext_raw = _safe_return(t0_close, pivot)
            pivot_ext_atr = (
                (float(t0_close) - float(pivot)) / float(atr)
                if pd.notna(t0_close) and pd.notna(pivot) and pd.notna(atr) and float(atr) > 0
                else np.nan
            )

            event: dict[str, Any] = {
                "symbol": symbol,
                "t0_date": t0["date"],
                "hard_filter_status": t0.get("hard_filter_status"),
                "investability_status": t0.get("investability_status"),
                "tradability_status": t0.get("tradability_status"),
                "trend_status": t0.get("trend_status"),
                "liquidity_status": t0.get("liquidity_status"),
                "rs_status": t0.get("rs_status"),
                "price_status": t0.get("price_status"),
                "regime_status": t0.get("regime_status"),
                "market_regime": t0.get("market_regime"),
                "breakout_volume_percentile": t0.get("breakout_volume_percentile"),
                "has_volume_confirmation": bool(t0.get("has_volume_confirmation")),
                "vcp_tightness": t0.get("vcp_tightness"),
                "has_tight_structure": t0.get("has_tight_structure"),
                "prev_pivot_high": pivot,
                "atr14_t0": atr,
                "tminus1_close": prev_close,
                "t0_close": t0_close,
                "ret_tminus1_t0": _safe_return(t0_close, prev_close),
                "pivot_extension_pct_t0": pivot_ext_raw,
                "pivot_extension_atr_t0": pivot_ext_atr,
                "t1_available": t1 is not None,
                "t3_available": future[3] is not None,
                "t5_available": future[5] is not None,
            }

            if t1 is not None:
                t1_open = t1.get("open_raw")
                event.update({
                    "t1_date": t1["date"],
                    "t1_open": t1_open,
                    "gap_t0close_t1open": _safe_return(t1_open, t0_close),
                    "t1_close": t1.get("close_raw"),
                    "ret_t1open_t1close": _safe_return(t1.get("close_raw"), t1_open),
                    "ret_t0close_t1close": _safe_return(t1.get("close_raw"), t0_close),
                })
                for horizon in (2, 3, 5):
                    bar = future[horizon]
                    event[f"t{horizon}_date"] = bar["date"] if bar is not None else pd.NaT
                    event[f"t{horizon}_close"] = bar.get("close_raw") if bar is not None else np.nan
                    event[f"ret_t1open_t{horizon}close"] = (
                        _safe_return(bar.get("close_raw"), t1_open) if bar is not None else np.nan
                    )

                for horizon in (1, 3, 5):
                    path = [future[n] for n in range(1, horizon + 1) if future[n] is not None]
                    if len(path) == horizon and pd.notna(t1_open) and float(t1_open) != 0:
                        max_high = max(float(b["high_raw"]) for b in path if pd.notna(b.get("high_raw")))
                        min_low = min(float(b["low_raw"]) for b in path if pd.notna(b.get("low_raw")))
                        event[f"mfe_high_t{horizon}"] = max_high / float(t1_open) - 1.0
                        event[f"mae_low_t{horizon}"] = min_low / float(t1_open) - 1.0
                    else:
                        event[f"mfe_high_t{horizon}"] = np.nan
                        event[f"mae_low_t{horizon}"] = np.nan
            events.append(event)

    return pd.DataFrame(events)


def link_positions(events: pd.DataFrame, positions: pd.DataFrame) -> pd.DataFrame:
    """Left-link production forward positions by symbol + T0 entry_date."""
    if events.empty or positions is None or positions.empty:
        out = events.copy()
        out["position_linked"] = False
        return out
    pos = positions.copy()
    if "entry_date" not in pos or "symbol" not in pos:
        raise ValueError("positions requires symbol and entry_date")
    pos["entry_date"] = pd.to_datetime(pos["entry_date"]).dt.normalize()
    keep = [c for c in [
        "symbol", "entry_date", "entry_price", "realistic_entry_price", "atr14_at_entry",
        "stop_price", "status", "exit_date", "exit_price", "exit_reason",
        "max_close_since_entry", "min_close_since_entry",
    ] if c in pos.columns]
    pos = pos[keep].drop_duplicates(["symbol", "entry_date"], keep="last")
    out = events.merge(pos, how="left", left_on=["symbol", "t0_date"], right_on=["symbol", "entry_date"])
    out["position_linked"] = out["entry_date"].notna()
    if "realistic_entry_price" in out and "exit_price" in out:
        out["realized_return_from_realistic_entry"] = [
            _safe_return(e, s) for e, s in zip(out["exit_price"], out["realistic_entry_price"])
        ]
    return out


def summarize_signal_path(events: pd.DataFrame, eligible_rows: int | None = None) -> dict[str, Any]:
    def med(col):
        return None if col not in events or events[col].dropna().empty else float(events[col].median())

    summary = {
        "diagnostic": "DIAG-001",
        "unit": "independent entry-ready onset",
        "eligible_decision_rows": eligible_rows,
        "events": int(len(events)),
        "t1_mature": int(events.get("t1_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "t3_mature": int(events.get("t3_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "t5_mature": int(events.get("t5_available", pd.Series(dtype=bool)).fillna(False).sum()),
        "linked_positions": int(events.get("position_linked", pd.Series(dtype=bool)).fillna(False).sum()),
        "medians": {
            "ret_tminus1_t0": med("ret_tminus1_t0"),
            "pivot_extension_atr_t0": med("pivot_extension_atr_t0"),
            "gap_t0close_t1open": med("gap_t0close_t1open"),
            "ret_t1open_t1close": med("ret_t1open_t1close"),
            "ret_t1open_t3close": med("ret_t1open_t3close"),
            "ret_t1open_t5close": med("ret_t1open_t5close"),
            "mfe_high_t5": med("mfe_high_t5"),
            "mae_low_t5": med("mae_low_t5"),
            "realized_return_from_realistic_entry": med("realized_return_from_realistic_entry"),
        },
        "governance": "observational only; no production threshold or rule change authorized",
    }
    return summary


def write_signal_path_diagnostic(decided: pd.DataFrame, positions_df: pd.DataFrame | None = None,
                                 event_path: str = EVENT_OUTPUT, summary_path: str = SUMMARY_OUTPUT):
    events = build_signal_path_events(decided)
    events = link_positions(events, positions_df)
    summary = summarize_signal_path(events, eligible_rows=len(decided))
    Path(event_path).parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(event_path, index=False)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    print(
        f"[DIAG-001] events={summary['events']} | T+1={summary['t1_mature']} | "
        f"T+3={summary['t3_mature']} | T+5={summary['t5_mature']} | "
        f"linked_positions={summary['linked_positions']}"
    )
    return events, summary
