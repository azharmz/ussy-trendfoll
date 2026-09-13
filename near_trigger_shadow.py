"""Shadow-only NEAR_TRIGGER candidate.

This module is observational. It must not alter Investability, Tradability,
position entry, or exit rules. The boundary was selected from development
research and requires forward/untouched validation before production use.
"""
from __future__ import annotations

import pandas as pd

NEAR_TRIGGER_MAX_ATR_DISTANCE = 0.60


def add_near_trigger_shadow(df: pd.DataFrame) -> pd.DataFrame:
    """Add distance facts and a shadow near-trigger flag without changing strategy status."""
    out = df.copy()
    out["distance_to_prev_pivot_pct"] = (
        (out["prev_pivot_high"] - out["close_raw"]) / out["prev_pivot_high"] * 100.0
    )
    out["distance_to_prev_pivot_atr"] = (
        (out["prev_pivot_high"] - out["close_raw"]) / out["atr14"]
    )
    out["near_trigger_shadow"] = (
        out["investability_status"].isin(["NEAR_PASS", "PASS"])
        & (~out["has_breakout"].astype(bool))
        & out["distance_to_prev_pivot_atr"].notna()
        & (out["distance_to_prev_pivot_atr"] >= 0)
        & (out["distance_to_prev_pivot_atr"] <= NEAR_TRIGGER_MAX_ATR_DISTANCE)
    )
    return out
