"""Compatibility import for the canonical shared EMA(adj_close) consumer.

The temporary raw-close `ema-close` namespace has been removed from ussy-data.
New code should import from `r2_shared_ema` directly.
"""
from r2_shared_ema import (
    EMA_POINTER_KEY as EMA_POINTER,
    EMA_RUN_PREFIX as EMA_PREFIX,
    PERIODS,
    PRICE_BASIS,
    PROMOTION_POLICY,
    load_shared_ema_state,
)

__all__ = [
    "EMA_POINTER",
    "EMA_PREFIX",
    "PERIODS",
    "PRICE_BASIS",
    "PROMOTION_POLICY",
    "load_shared_ema_state",
]
