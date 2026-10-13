"""DIAG-003 observational simulation of the current TrendFoll exit contract."""
from __future__ import annotations

import numpy as np
import pandas as pd

STOP_ATR_MULTIPLIER = 2.0
MAX_HOLDING_BARS = 45
EARLY_FAILURE_BARS = 5


def _ret(end, start):
    if pd.isna(end) or pd.isna(start) or float(start) == 0:
        return np.nan
    return float(end) / float(start) - 1.0


def _median(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    return None if values.empty else float(values.median())


def simulate_exit_conversion(
    decided: pd.DataFrame,
    events: pd.DataFrame,
    *,
    stop_atr_multiplier: float = STOP_ATR_MULTIPLIER,
    max_holding_bars: int = MAX_HOLDING_BARS,
    early_failure_bars: int = EARLY_FAILURE_BARS,
) -> pd.DataFrame:
    """Simulate current exits from each eligible event's T+1 open.

    decided must contain full per-symbol history with OHLC, ATR14 and EMA20.
    events must contain symbol and t0_date. The simulator enforces one active
    simulated position per symbol; a new onset before the prior exit date is
    marked blocked_overlap.
    """
    required = {"symbol", "date", "open_raw", "high_raw", "low_raw", "close_raw", "ema20", "atr14"}
    missing = sorted(required - set(decided.columns))
    if missing:
        raise ValueError(f"DIAG-003 history missing required columns: {missing}")
    if not {"symbol", "t0_date"}.issubset(events.columns):
        raise ValueError("DIAG-003 events requires symbol and t0_date")
    if stop_atr_multiplier <= 0 or max_holding_bars < 1 or early_failure_bars < 1:
        raise ValueError("Invalid frozen DIAG-003 parameters")

    history = decided.copy()
    history["date"] = pd.to_datetime(history["date"]).dt.normalize()
    history = history.sort_values(["symbol", "date"]).reset_index(drop=True)
    if history.duplicated(["symbol", "date"]).any():
        raise ValueError("DIAG-003 requires unique symbol+date history rows")
    by_symbol = {s: g.reset_index(drop=True) for s, g in history.groupby("symbol", sort=False)}
    index_by_symbol = {
        s: {pd.Timestamp(d): i for i, d in enumerate(g["date"])}
        for s, g in by_symbol.items()
    }

    ordered = events.copy()
    ordered["t0_date"] = pd.to_datetime(ordered["t0_date"]).dt.normalize()
    ordered = ordered.sort_values(["symbol", "t0_date"]).reset_index(drop=True)
    locked_through: dict[str, pd.Timestamp] = {}
    output = []

    for _, event in ordered.iterrows():
        symbol = str(event["symbol"])
        t0 = pd.Timestamp(event["t0_date"])
        row = event.to_dict()
        row.update({
            "simulation_status": None, "entry_date": pd.NaT, "entry_open": np.nan,
            "atr14_t0": np.nan, "stop_price": np.nan, "exit_date": pd.NaT,
            "exit_reason": None, "exit_price": np.nan, "days_held": np.nan,
            "realized_return": np.nan, "positive_return": None,
            "mfe_return": np.nan, "mae_return": np.nan, "time_to_mfe_bars": np.nan,
            "first_ema20_loss_day": np.nan, "early_failure": None,
            "giveback_return": np.nan, "giveback_fraction_of_positive_mfe": np.nan,
            "day45_close_return": np.nan, "day45_mature": False,
            "post45_max_high_return": np.nan, "post45_day90_close_return": np.nan,
            "post45_gain_vs_day45_close": np.nan, "post45_drawdown_vs_day45_close": np.nan,
            "post90_mature": False,
        })
        g = by_symbol.get(symbol)
        pos = index_by_symbol.get(symbol, {}).get(t0)
        if g is None or pos is None:
            row["simulation_status"] = "event_not_in_history"
            output.append(row)
            continue
        if symbol in locked_through and t0 < locked_through[symbol]:
            row["simulation_status"] = "blocked_overlap"
            output.append(row)
            continue
        if pos + 1 >= len(g):
            row["simulation_status"] = "no_t1_bar"
            output.append(row)
            locked_through[symbol] = pd.Timestamp(g.iloc[-1]["date"])
            continue

        t0_row = g.iloc[pos]
        atr = t0_row["atr14"]
        entry_i = pos + 1
        entry = g.iloc[entry_i]["open_raw"]
        if pd.isna(atr) or float(atr) <= 0 or pd.isna(entry) or float(entry) <= 0:
            row["simulation_status"] = "invalid_entry_or_atr"
            output.append(row)
            continue

        entry = float(entry)
        atr = float(atr)
        stop = entry - stop_atr_multiplier * atr
        row.update({
            "entry_date": g.iloc[entry_i]["date"], "entry_open": entry,
            "atr14_t0": atr, "stop_price": stop,
        })
        last_i = min(pos + max_holding_bars, len(g) - 1)
        exit_i = None
        exit_reason = None
        exit_price = np.nan
        first_ema_loss = None

        for i in range(entry_i, last_i + 1):
            bar = g.iloc[i]
            days_held = i - pos
            ema_loss = pd.notna(bar["ema20"]) and float(bar["close_raw"]) < float(bar["ema20"])
            if ema_loss and first_ema_loss is None:
                first_ema_loss = days_held
            if pd.notna(bar["low_raw"]) and float(bar["low_raw"]) <= stop:
                exit_i, exit_reason, exit_price = i, "stop_loss", stop
                break
            if days_held >= max_holding_bars:
                exit_i, exit_reason, exit_price = i, "max_holding", float(bar["close_raw"])
                break
            if ema_loss:
                exit_i, exit_reason, exit_price = i, "trend_exit", float(bar["close_raw"])
                break

        row["first_ema20_loss_day"] = np.nan if first_ema_loss is None else first_ema_loss
        day45_i = pos + MAX_HOLDING_BARS
        if day45_i < len(g):
            row["day45_mature"] = True
            row["day45_close_return"] = _ret(g.iloc[day45_i]["close_raw"], entry)
        if exit_reason == "max_holding" and pos + 90 < len(g):
            day45_close = float(g.iloc[day45_i]["close_raw"])
            future46_90 = g.iloc[pos + 46:pos + 91]
            row["post90_mature"] = True
            row["post45_max_high_return"] = _ret(future46_90["high_raw"].max(), entry)
            row["post45_day90_close_return"] = _ret(g.iloc[pos + 90]["close_raw"], entry)
            row["post45_gain_vs_day45_close"] = _ret(future46_90["high_raw"].max(), day45_close)
            row["post45_drawdown_vs_day45_close"] = _ret(future46_90["low_raw"].min(), day45_close)

        if exit_i is None:
            row["simulation_status"] = "censored_no_exit"
            locked_through[symbol] = pd.Timestamp(g.iloc[-1]["date"])
            output.append(row)
            continue

        exit_bar = g.iloc[exit_i]
        days_held = exit_i - pos
        realized = _ret(exit_price, entry)
        row.update({
            "simulation_status": "exited",
            "exit_date": exit_bar["date"],
            "exit_reason": exit_reason,
            "exit_price": exit_price,
            "days_held": days_held,
            "realized_return": realized,
            "positive_return": bool(realized > 0),
            "early_failure": bool(exit_reason in {"stop_loss", "trend_exit"} and days_held <= early_failure_bars),
        })

        # A stop bar's high/low ordering is unknowable from daily OHLC. Exclude
        # that bar from MFE and cap MAE at the assumed stop fill.
        excursion_end = exit_i - 1 if exit_reason == "stop_loss" else exit_i
        excursion = g.iloc[entry_i:excursion_end + 1]
        highs = [entry]
        lows = [entry]
        if not excursion.empty:
            highs.extend(pd.to_numeric(excursion["high_raw"], errors="coerce").dropna().tolist())
            lows.extend(pd.to_numeric(excursion["low_raw"], errors="coerce").dropna().tolist())
        if exit_reason == "stop_loss":
            lows.append(exit_price)
        max_high = max(highs)
        min_low = min(lows)
        mfe = _ret(max_high, entry)
        mae = _ret(min_low, entry)
        row["mfe_return"] = mfe
        row["mae_return"] = mae
        row["time_to_mfe_bars"] = next(
            (i - pos for i in range(entry_i, excursion_end + 1)
             if pd.notna(g.iloc[i]["high_raw"]) and float(g.iloc[i]["high_raw"]) == max_high),
            0 if max_high == entry else np.nan,
        )
        if pd.notna(mfe):
            giveback = mfe - realized
            row["giveback_return"] = giveback
            if mfe > 0:
                row["giveback_fraction_of_positive_mfe"] = giveback / mfe
        locked_through[symbol] = pd.Timestamp(exit_bar["date"])
        output.append(row)

    return pd.DataFrame(output)


def summarize_exit_conversion(results: pd.DataFrame) -> dict:
    exited = results[results["simulation_status"] == "exited"].copy()
    mature45 = results[results["day45_mature"].astype(bool)].copy()
    post90 = results[results["post90_mature"].astype(bool)].copy()
    reason_counts = {str(k): int(v) for k, v in exited["exit_reason"].value_counts(dropna=False).items()}
    return {
        "diagnostic": "DIAG-003",
        "status": "OBSERVATIONAL_ONLY_NO_PRODUCTION_CHANGE",
        "event_rows": int(len(results)),
        "exited_trades": int(len(exited)),
        "censored_no_exit": int((results["simulation_status"] == "censored_no_exit").sum()),
        "blocked_overlap": int((results["simulation_status"] == "blocked_overlap").sum()),
        "no_t1_bar": int((results["simulation_status"] == "no_t1_bar").sum()),
        "invalid_entry_or_atr": int((results["simulation_status"] == "invalid_entry_or_atr").sum()),
        "exit_reasons": reason_counts,
        "positive_return_rate": None if exited.empty else float(exited["positive_return"].mean()),
        "median_realized_return": _median(exited["realized_return"]),
        "median_days_held": _median(exited["days_held"]),
        "early_failure_count": int(exited["early_failure"].fillna(False).sum()),
        "early_failure_rate": None if exited.empty else float(exited["early_failure"].fillna(False).mean()),
        "median_mfe_return": _median(exited["mfe_return"]),
        "median_mae_return": _median(exited["mae_return"]),
        "median_time_to_mfe_bars": _median(exited["time_to_mfe_bars"]),
        "median_first_ema20_loss_day": _median(exited["first_ema20_loss_day"]),
        "median_giveback_return": _median(exited["giveback_return"]),
        "median_giveback_fraction_of_positive_mfe": _median(exited["giveback_fraction_of_positive_mfe"]),
        "day45_mature_count": int(len(mature45)),
        "day45_counterfactual_median_return": _median(mature45["day45_close_return"]),
        "post90_mature_max_holding_count": int(len(post90)),
        "post45_max_high_return_median": _median(post90["post45_max_high_return"]),
        "post45_day90_close_return_median": _median(post90["post45_day90_close_return"]),
        "post45_gain_vs_day45_close_median": _median(post90["post45_gain_vs_day45_close"]),
        "post45_drawdown_vs_day45_close_median": _median(post90["post45_drawdown_vs_day45_close"]),
        "interpretation": "Descriptive only; event-level simulation is not a portfolio backtest, current universe is not point-in-time, and no production change is authorized.",
    }
