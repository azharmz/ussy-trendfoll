"""
USSY Swing — Decision Layer (Phase 2)
=======================================
Investability / Tradability split + Explainability, sesuai desain yang
disepakati di diskusi arsitektur awal proyek.

PRINSIP:
- Investability: karakteristik STRUKTURAL saham, berubah LAMBAT (trend, RS,
  liquidity, price floor). Jawab: "apakah saham ini layak dipertimbangkan?"
- Tradability: kondisi entry HARI INI, berubah HARIAN (breakout, volume,
  structure quality). Jawab: "apakah SEKARANG momen yang tepat?"
- Regime: gate portfolio-level terpisah (bukan per-saham).
- Explainability: checklist manusiawi dari feature yang SUDAH dihitung —
  presentation layer, TIDAK ada logika baru, murni menampilkan apa yang
  sudah ada dengan cara yang mudah dibaca.

Non-compensatory tetap dipertahankan: Investability dan Tradability masing-
masing punya status PASS/NEAR_PASS/FAIL sendiri, TIDAK digabung jadi satu
skor tunggal (konsisten dengan prinsip hierarchical filter yang sudah
disepakati sejak Sprint 2).
"""

import pandas as pd
from hard_filter import STATUS_RANK

INVESTABILITY_COLS = ["trend_status", "liquidity_status", "rs_status", "price_status"]


def compute_investability(fs_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Investability status — gabungan non-compensatory dari 4 kriteria struktural
    (TIDAK termasuk regime, karena itu gate portfolio-level terpisah).
    """
    df = fs_filtered.copy()

    def overall(row):
        ranks = [STATUS_RANK[row[c]] for c in INVESTABILITY_COLS]
        if min(ranks) == 0:
            return "FAIL"
        if min(ranks) == 1:
            return "NEAR_PASS"
        return "PASS"

    df["investability_status"] = df[INVESTABILITY_COLS].apply(
        lambda row: overall({c: row[c] for c in INVESTABILITY_COLS}), axis=1
    )
    return df


def compute_tradability(fs_filtered: pd.DataFrame, volume_percentile_threshold: float = 80,
                          vcp_tightness_threshold: float = 60) -> pd.DataFrame:
    """
    Tradability status — kondisi entry HARI INI. Breakout adalah syarat keras
    (non-compensatory: tanpa breakout, tidak ada gunanya vcp_tightness setinggi
    apapun). Volume confirmation dan vcp_tightness jadi pembeda PASS vs NEAR_PASS.
    """
    df = fs_filtered.sort_values(["symbol", "date"]).copy()
    df["prev_pivot_high"] = df.groupby("symbol")["pivot_high"].shift(1)
    df["has_breakout"] = (df["prev_pivot_high"].notna()) & (df["close_raw"] > df["prev_pivot_high"])
    df["has_volume_confirmation"] = df["breakout_volume_percentile"] >= volume_percentile_threshold
    df["has_tight_structure"] = df["vcp_tightness"] >= vcp_tightness_threshold

    def tradability(row):
        if not row["has_breakout"]:
            return "FAIL"
        if row["has_volume_confirmation"] and row["has_tight_structure"]:
            return "PASS"
        if row["has_volume_confirmation"] or row["has_tight_structure"]:
            return "NEAR_PASS"
        return "NEAR_PASS"  # breakout ada tapi tanpa konfirmasi apapun — masih dianggap kandidat lemah, bukan FAIL keras

    df["tradability_status"] = df.apply(tradability, axis=1)
    return df


def compute_decision_layer(fs_filtered: pd.DataFrame, volume_percentile_threshold: float = 80,
                             vcp_tightness_threshold: float = 60) -> pd.DataFrame:
    """Gabungkan Investability + Tradability + Regime (sudah ada) jadi satu view."""
    df = compute_investability(fs_filtered)
    df = compute_tradability(df, volume_percentile_threshold, vcp_tightness_threshold)
    return df


# ============================================================
# EXPLAINABILITY — checklist manusiawi, presentation layer murni
# ============================================================

def explain_candidate(row: pd.Series) -> str:
    """
    Checklist manusiawi untuk SATU baris (symbol, date). Murni menampilkan
    feature yang sudah dihitung — TIDAK ada logika/threshold baru di sini.
    """
    lines = [f"### {row['symbol']} — {pd.Timestamp(row['date']).date()}", ""]

    lines.append(f"**Investability: {row['investability_status']}**")
    lines.append(f"  {'✓' if row['trend_status']=='PASS' else '⚠' if row['trend_status']=='NEAR_PASS' else '✗'} "
                 f"Trend: {row['trend_status']} (EMA aligned: {row.get('ema_stack_aligned')}, Stage: {row.get('stage')})")
    lines.append(f"  {'✓' if row['rs_status']=='PASS' else '⚠' if row['rs_status']=='NEAR_PASS' else '✗'} "
                 f"Relative Strength: {row['rs_status']} (RS vs SPY: {row.get('rs_spy'):.3f})" if pd.notna(row.get('rs_spy')) else f"  ✗ Relative Strength: data tidak lengkap")
    lines.append(f"  {'✓' if row['liquidity_status']=='PASS' else '⚠' if row['liquidity_status']=='NEAR_PASS' else '✗'} "
                 f"Liquidity: {row['liquidity_status']} (avg volume 50d: {row.get('avg_volume_50d'):,.0f})" if pd.notna(row.get('avg_volume_50d')) else f"  ✗ Liquidity: data tidak lengkap")
    lines.append(f"  {'✓' if row['price_status']=='PASS' else '⚠' if row['price_status']=='NEAR_PASS' else '✗'} "
                 f"Price Floor: {row['price_status']} (${row.get('close_raw'):.2f})")

    lines.append("")
    lines.append(f"**Tradability: {row['tradability_status']}**")
    lines.append(f"  {'✓' if row.get('has_breakout') else '✗'} Breakout dari pivot high")
    lines.append(f"  {'✓' if row.get('has_volume_confirmation') else '✗'} Volume confirmation "
                 f"(percentile: {row.get('breakout_volume_percentile'):.0f})" if pd.notna(row.get('breakout_volume_percentile')) else "  ✗ Volume: data tidak lengkap")
    lines.append(f"  {'✓' if row.get('has_tight_structure') else '✗'} Struktur ketat "
                 f"(vcp_tightness: {row.get('vcp_tightness'):.0f})" if pd.notna(row.get('vcp_tightness')) else "  ✗ Structure: data tidak lengkap")

    lines.append("")
    lines.append(f"**Market Regime: {row.get('regime_status')}** ({row.get('market_regime')})")

    return "\n".join(lines)


def generate_watchlist_explanations(decision_df: pd.DataFrame, as_of_date=None,
                                      min_investability: str = "NEAR_PASS") -> str:
    """
    Ambil kandidat terbaik di tanggal tertentu (investability minimal NEAR_PASS),
    urutkan tradability terbaik dulu, generate checklist untuk semua.
    """
    if as_of_date is None:
        as_of_date = decision_df["date"].max()

    latest = decision_df[decision_df["date"] == as_of_date].copy()
    min_rank = STATUS_RANK[min_investability]
    candidates = latest[latest["investability_status"].map(STATUS_RANK) >= min_rank]
    candidates = candidates.sort_values(
        by="tradability_status", key=lambda s: s.map(STATUS_RANK), ascending=False
    )

    if candidates.empty:
        return f"# Watchlist — {pd.Timestamp(as_of_date).date()}\n\nTidak ada kandidat dengan investability >= {min_investability} di tanggal ini."

    output = [f"# Watchlist — {pd.Timestamp(as_of_date).date()}", "",
              f"{len(candidates)} kandidat dengan investability >= {min_investability}", ""]
    for _, row in candidates.iterrows():
        output.append(explain_candidate(row))
        output.append("\n---\n")

    return "\n".join(output)
