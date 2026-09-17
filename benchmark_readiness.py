"""Benchmark readiness contract for R2 production decisions.

- RS requires an exact SPY observation for the stock as-of date.
- Market regime may use same/prior SPY state via backward-as-of, but production
  readiness must not silently accept an R2 terminal date that lacks exact SPY
  coverage because RS is decision-relevant.
- Benchmark rows after the stock as-of date are harmless and ignored.
"""
from __future__ import annotations

import pandas as pd


def validate_spy_readiness(stock_dates, spy_dates, as_of_date=None):
    stock = pd.DatetimeIndex(pd.to_datetime(list(stock_dates))).normalize().unique().sort_values()
    spy = pd.DatetimeIndex(pd.to_datetime(list(spy_dates))).normalize().unique().sort_values()
    if len(stock) == 0:
        raise ValueError("stock dates empty")
    if len(spy) == 0:
        raise RuntimeError("SPY unavailable")

    t0 = pd.Timestamp(as_of_date).normalize() if as_of_date is not None else stock.max()
    if t0 not in stock:
        raise ValueError("as_of_date is not present in stock dates")

    exact = t0 in spy
    prior = spy[spy <= t0]
    regime_source = prior.max() if len(prior) else pd.NaT
    if not exact:
        raise RuntimeError(
            f"SPY not READY for stock as-of {t0.date()}: exact-date row required by RS"
        )

    return {
        "as_of_date": t0,
        "spy_exact_as_of": True,
        "regime_source_date": regime_source,
        "spy_latest_date": spy.max(),
    }