"""
USSY Swing — Hard Filter (Sprint 2, Deliverable #1)
=====================================================

Menerapkan kriteria PASS/NEAR_PASS/FAIL (non-compensatory) di atas Feature Store
yang sudah divalidasi di Sprint 1. TIDAK ada scoring/ranking di sini — murni
gate/filter. Scoring & ranking (kalau nanti dibutuhkan) masuk Phase 2, bukan Sprint 2.

PRINSIP NON-COMPENSATORY:
FAIL kalau ADA SATU SAJA kriteria FAIL, walau kriteria lain sempurna. Ini
mencegah "trend bagus + RS bagus" menutupi "liquidity jelek" — sesuai kesepakatan
di diskusi arsitektur sebelumnya (hierarchical filter, bukan weighted sum).

Kriteria (lihat tabel desain):
1. Trend      — ema_stack_aligned + stage (Minervini Trend Template + Weinstein Stage)
2. Liquidity  — avg_volume_50d minimum (hindari saham terlalu tidak likuid)
3. RS         — rs_spy > 0 (saham harus mengalahkan pasar, prinsip dari diskusi RS)
4. Price      — minimum price floor (hindari penny stock / data quality issue)
5. Regime     — market_regime dari SPY (gate portfolio-level, bukan per-saham)
"""

import pandas as pd
import numpy as np

# ============================================================
# THRESHOLD — bisa diubah tanpa mengubah logic (contract-first)
# ============================================================

THRESHOLDS = {
    "liquidity": {"pass": 300_000, "near_pass": 240_000},
    "rs_spy": {"pass": 0.0, "near_pass": -0.02},
    "price": {"pass": 10.0, "near_pass": 8.0},
}

STATUS_RANK = {"FAIL": 0, "NEAR_PASS": 1, "PASS": 2}


def _status_from_threshold(value: float, pass_th: float, near_pass_th: float, higher_is_better: bool = True) -> str:
    if pd.isna(value):
        return "FAIL"
    if higher_is_better:
        if value >= pass_th:
            return "PASS"
        elif value >= near_pass_th:
            return "NEAR_PASS"
        return "FAIL"
    else:
        if value <= pass_th:
            return "PASS"
        elif value <= near_pass_th:
            return "NEAR_PASS"
        return "FAIL"


def _trend_status(row) -> str:
    """PASS: ema_stack_aligned True DAN stage Stage2.
    NEAR_PASS: ema_stack_aligned True tapi stage bukan Stage2 (mis. Stage1, base
    belum lolos ke uptrend confirmed), ATAU EMA stack "hampir" benar.
    FAIL: selainnya (termasuk data NaN — belum cukup histori)."""
    aligned = row.get("ema_stack_aligned")
    stage = row.get("stage")

    if pd.isna(aligned) or aligned not in (True, False):
        return "FAIL"

    if aligned and stage == "Stage2":
        return "PASS"
    if aligned and stage in ("Stage1", "Stage3"):
        return "NEAR_PASS"
    return "FAIL"


def _regime_status(market_regime: str) -> str:
    if market_regime == "Bullish":
        return "PASS"
    if market_regime == "Neutral":
        return "NEAR_PASS"
    return "FAIL"  # Bearish atau NaN


def compute_hard_filter(fs: pd.DataFrame) -> pd.DataFrame:
    """
    Input: Feature Store (hasil Sprint 1).
    Output: DataFrame dengan kolom tambahan per kriteria + overall_status,
    satu baris per (symbol, date) — sama granularitasnya dengan feature store.
    """
    df = fs.copy()

    df["trend_status"] = df.apply(_trend_status, axis=1)

    df["liquidity_status"] = df["avg_volume_50d"].apply(
        lambda v: _status_from_threshold(v, THRESHOLDS["liquidity"]["pass"],
                                          THRESHOLDS["liquidity"]["near_pass"], higher_is_better=True)
    )

    df["rs_status"] = df["rs_spy"].apply(
        lambda v: _status_from_threshold(v, THRESHOLDS["rs_spy"]["pass"],
                                          THRESHOLDS["rs_spy"]["near_pass"], higher_is_better=True)
    )

    df["price_status"] = df["close_raw"].apply(
        lambda v: _status_from_threshold(v, THRESHOLDS["price"]["pass"],
                                          THRESHOLDS["price"]["near_pass"], higher_is_better=True)
    )

    df["regime_status"] = df["market_regime"].apply(_regime_status)

    status_cols = ["trend_status", "liquidity_status", "rs_status", "price_status", "regime_status"]

    def overall(row):
        ranks = [STATUS_RANK[row[c]] for c in status_cols]
        if min(ranks) == 0:
            return "FAIL"
        if min(ranks) == 1:
            return "NEAR_PASS"
        return "PASS"

    df["hard_filter_status"] = df[status_cols].apply(
        lambda row: overall({c: row[c] for c in status_cols}), axis=1
    )

    def fail_reasons(row):
        failed = [c.replace("_status", "") for c in status_cols if row[c] == "FAIL"]
        near = [c.replace("_status", "") for c in status_cols if row[c] == "NEAR_PASS"]
        parts = []
        if failed:
            parts.append(f"FAIL: {', '.join(failed)}")
        if near:
            parts.append(f"NEAR_PASS: {', '.join(near)}")
        return " | ".join(parts) if parts else "All PASS"

    df["hard_filter_reason"] = df[status_cols].apply(
        lambda row: fail_reasons({c: row[c] for c in status_cols}), axis=1
    )

    return df


def summarize_hard_filter(df: pd.DataFrame, as_of_date: pd.Timestamp = None) -> pd.DataFrame:
    """Ringkasan status terbaru per ticker — untuk watchlist mingguan."""
    if as_of_date is None:
        as_of_date = df["date"].max()
    latest = df[df["date"] == as_of_date].copy()
    cols = ["symbol", "close_raw", "hard_filter_status", "hard_filter_reason",
            "trend_status", "liquidity_status", "rs_status", "price_status", "regime_status"]
    return latest[cols].sort_values(
        by="hard_filter_status", key=lambda s: s.map(STATUS_RANK), ascending=False
    ).reset_index(drop=True)
