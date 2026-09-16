"""Research-only C06/FSE ATR corporate-action correction prototype.

Frozen contract:
- Preserve ATR period=14 and Wilder-style EWM alpha=1/14.
- Express historical raw OHLC observations on each evaluation row's current
  share basis using only split ratios effective through that row.
- A split effective on date j is already reflected in that day's reported raw
  OHLC; therefore observations i < j are divided by the split ratio, while
  same-day/post-event observations are not transformed.
- Future splits never alter historical as-of ATR state.
- Unknown required split factors fail closed.

This module is deliberately not wired into production feature_engine.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_frame(df: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "high_raw", "low_raw", "close_raw", "stock_splits"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    x = df.copy().sort_values("date").reset_index(drop=True)
    x["date"] = pd.to_datetime(x["date"])
    for col in ["high_raw", "low_raw", "close_raw", "stock_splits"]:
        x[col] = pd.to_numeric(x[col], errors="coerce").astype(float)
    x["stock_splits"] = x["stock_splits"].fillna(0.0)
    bad = (x["stock_splits"] < 0) | ((x["stock_splits"] > 0) & ~np.isfinite(x["stock_splits"]))
    if bad.any():
        raise ValueError("invalid split ratio")
    return x


def compute_split_adjusted_atr(
    df: pd.DataFrame,
    *,
    period: int = 14,
    fail_closed_on_missing_split: bool = True,
) -> pd.Series:
    """Compute causal ATR on each row's as-of share basis.

    For each evaluation row T0, all OHLC rows <=T0 are normalized to T0's
    share basis. A 2-for-1 split divides pre-split prices by 2; a 1-for-10
    reverse split (ratio 0.1) divides pre-split prices by 0.1. Then the existing
    true-range and EWM equations are applied without parameter tuning.

    Optional `split_factor_known` marks whether a positive split event has an
    authoritative factor. If a required event is unknown, affected as-of ATR
    rows return NaN rather than silently mixing units.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    x = _validate_frame(df)
    known = pd.Series(True, index=x.index)
    if "split_factor_known" in x.columns:
        known = x["split_factor_known"].fillna(False).astype(bool).reset_index(drop=True)

    out = pd.Series(np.nan, index=x.index, dtype=float)
    for end in range(len(x)):
        invalid = False
        factors = np.ones(end + 1, dtype=float)
        # Normalize every historical row i to the share basis effective at end.
        for i in range(end + 1):
            factor = 1.0
            for j in range(i + 1, end + 1):
                ratio = x.at[j, "stock_splits"]
                if ratio > 0:
                    if fail_closed_on_missing_split and not bool(known.iloc[j]):
                        invalid = True
                        break
                    factor *= ratio
            if invalid:
                break
            factors[i] = factor
        if invalid:
            continue

        hist = x.loc[:end, ["high_raw", "low_raw", "close_raw"]].copy()
        hist["high"] = hist["high_raw"].to_numpy() / factors
        hist["low"] = hist["low_raw"].to_numpy() / factors
        hist["close"] = hist["close_raw"].to_numpy() / factors
        prev_close = hist["close"].shift(1)
        tr = pd.concat(
            [
                hist["high"] - hist["low"],
                (hist["high"] - prev_close).abs(),
                (hist["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        out.iloc[end] = atr.iloc[-1]

    # Restore caller ordering.
    out.index = df.sort_values("date").index
    return out.reindex(df.index)
