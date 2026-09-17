"""Canonical TrendFoll EMA calculation.

The analytical EMA price basis is adjusted close, matching the governed shared
EMA contract owned by ussy-data. This helper is intentionally small so both
historical feature rows and terminal shared state can use the same mathematical
contract without changing unrelated raw-price features.
"""
from __future__ import annotations

import pandas as pd

EMA_PERIODS = (20, 50, 150, 200)
EMA_PRICE_COLUMN = "close_adj"


def compute_canonical_ema_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return date-sorted rows with canonical adj-close EMA features.

    Only EMA columns and ``ema_stack_aligned`` are written. Raw-price features
    such as nominal price floor, pivot/breakout, 52-week-high distance, ATR,
    volume and stage calculations remain owned by their existing contracts.
    """
    if EMA_PRICE_COLUMN not in df.columns:
        raise ValueError(f"Canonical EMA requires {EMA_PRICE_COLUMN!r}")

    out = df.copy().sort_values("date").reset_index(drop=True)
    price = pd.to_numeric(out[EMA_PRICE_COLUMN], errors="coerce")
    if price.isna().any():
        raise ValueError("Canonical EMA price basis contains missing/non-numeric adj_close")

    for period in EMA_PERIODS:
        out[f"ema{period}"] = price.ewm(span=period, adjust=False).mean()

    out["ema_stack_aligned"] = (
        (price > out["ema20"])
        & (out["ema20"] > out["ema50"])
        & (out["ema50"] > out["ema150"])
        & (out["ema150"] > out["ema200"])
    )
    return out
