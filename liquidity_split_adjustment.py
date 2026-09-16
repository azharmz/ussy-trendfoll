"""Research-only FSE-014 split-adjusted share-liquidity prototype.

Implements the frozen Evidence-13 contract without changing production feature_engine.
Split ratios use Yahoo convention: 2.0 means 2-for-1, 0.1 means 1-for-10.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_volume_asof(
    dates: pd.Series,
    raw_volume: pd.Series,
    split_ratio: pd.Series,
) -> pd.Series:
    """Express each historical volume observation on each row's as-of share basis.

    For row T0, observation t<=T0 is multiplied by split ratios effective in
    (t, T0]. Future events never affect historical rows. Returns only the
    per-row current-basis volume for the same date; rolling helper below builds
    the causal window explicitly.
    """
    d = pd.to_datetime(dates).reset_index(drop=True)
    v = pd.to_numeric(raw_volume, errors="coerce").reset_index(drop=True)
    s = pd.to_numeric(split_ratio, errors="coerce").fillna(0.0).reset_index(drop=True)
    if not (len(d) == len(v) == len(s)):
        raise ValueError("dates, raw_volume, split_ratio must have equal length")
    if not d.is_monotonic_increasing:
        raise ValueError("dates must be sorted ascending")
    bad = (s < 0) | ((s > 0) & ~np.isfinite(s))
    if bad.any():
        raise ValueError("invalid split ratio")
    # A same-day volume is already reported on that day's post-event share basis.
    return v.astype(float)


def compute_split_adjusted_avg_volume(
    df: pd.DataFrame,
    *,
    window: int = 50,
    min_periods: int = 20,
    fail_closed_on_missing_split: bool = True,
) -> pd.Series:
    """Causal rolling average share volume on each evaluation row's share basis.

    Required columns: date, volume_raw, stock_splits.
    Optional column: split_factor_known. If False for a positive split event,
    corrected liquidity is NaN from that event through any window containing
    pre-event observations, rather than silently mixing units.
    """
    required = {"date", "volume_raw", "stock_splits"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if window <= 0 or min_periods <= 0 or min_periods > window:
        raise ValueError("invalid window/min_periods")

    x = df.copy().sort_values("date").reset_index(drop=True)
    dates = pd.to_datetime(x["date"])
    volume = pd.to_numeric(x["volume_raw"], errors="coerce").astype(float)
    splits = pd.to_numeric(x["stock_splits"], errors="coerce").fillna(0.0).astype(float)
    if (splits < 0).any() or ((splits > 0) & ~np.isfinite(splits)).any():
        raise ValueError("invalid split ratio")

    known = pd.Series(True, index=x.index)
    if "split_factor_known" in x.columns:
        known = x["split_factor_known"].fillna(False).astype(bool)

    out = pd.Series(np.nan, index=x.index, dtype=float)
    for end in range(len(x)):
        start = max(0, end - window + 1)
        if end - start + 1 < min_periods:
            continue
        vals = []
        invalid = False
        for i in range(start, end + 1):
            val = volume.iloc[i]
            if pd.isna(val):
                vals.append(np.nan)
                continue
            factor = 1.0
            # Split effective on observation date i is already reflected in
            # that day's reported volume, hence strictly later events only.
            for j in range(i + 1, end + 1):
                ratio = splits.iloc[j]
                if ratio > 0:
                    if fail_closed_on_missing_split and not known.iloc[j]:
                        invalid = True
                        break
                    factor *= ratio
            if invalid:
                break
            vals.append(val * factor)
        if invalid:
            continue
        valid_vals = pd.Series(vals, dtype=float).dropna()
        if len(valid_vals) >= min_periods:
            out.iloc[end] = float(valid_vals.mean())
    out.index = df.sort_values("date").index
    return out.reindex(df.index)


def classify_liquidity(avg_volume: pd.Series) -> pd.Series:
    """Existing frozen thresholds; no threshold tuning in FSE-014."""
    a = pd.to_numeric(avg_volume, errors="coerce")
    result = pd.Series("FAIL", index=a.index, dtype=object)
    result[a >= 240_000] = "NEAR_PASS"
    result[a >= 300_000] = "PASS"
    result[a.isna()] = None
    return result
