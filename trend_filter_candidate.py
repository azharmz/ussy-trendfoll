"""Frozen development candidate for the O'Neil-aligned structural trend gate.

Governance:
- Production baseline remains unchanged.
- TF-SMA-STRUCT-01 is development-only until untouched validation passes.
- No slope lookback or extra moving-average terms may be added here without a
  new evidence-backed candidate contract.
"""
from __future__ import annotations

import pandas as pd

CANDIDATE_ID = "TF-SMA-STRUCT-01"


def compute_sma_struct_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the frozen structural candidate on one symbol's daily history.

    Required columns: date, close_raw.
    The candidate is evaluable only once both finite-window SMAs exist.
    """
    required = {"date", "close_raw"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy().sort_values("date").reset_index(drop=True)
    out["sma50"] = out["close_raw"].rolling(50, min_periods=50).mean()
    out["sma200"] = out["close_raw"].rolling(200, min_periods=200).mean()
    out["tf_sma_struct_evaluable"] = out[["sma50", "sma200"]].notna().all(axis=1)
    out["tf_sma_struct_pass"] = (
        out["tf_sma_struct_evaluable"]
        & (out["close_raw"] > out["sma50"])
        & (out["sma50"] > out["sma200"])
    )
    return out


def add_sma_struct_features(features: pd.DataFrame) -> pd.DataFrame:
    """Apply TF-SMA-STRUCT-01 to a multi-symbol feature/history frame."""
    if "symbol" not in features.columns:
        raise ValueError("Missing required column: symbol")
    if features.empty:
        out = features.copy()
        out["sma50"] = pd.Series(dtype=float)
        out["sma200"] = pd.Series(dtype=float)
        out["tf_sma_struct_evaluable"] = pd.Series(dtype=bool)
        out["tf_sma_struct_pass"] = pd.Series(dtype=bool)
        return out

    parts = [compute_sma_struct_features(group) for _, group in features.groupby("symbol", sort=False)]
    return pd.concat(parts, ignore_index=True).sort_values(["symbol", "date"]).reset_index(drop=True)
