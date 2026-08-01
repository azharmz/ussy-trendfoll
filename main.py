"""
USSY TrendFoll — Main Pipeline (dijalankan harian via GitHub Actions)
========================================================================
Urutan:
  1. Ambil sector mapping (cache Supabase, fetch ulang cuma kalau basi/kosong)
  2. Build feature store (fetch OHLCV seluruh universe + hitung 33 feature)
  3. Hard filter (5 kriteria PASS/NEAR_PASS/FAIL, non-compensatory)
  4. Decision layer (Investability/Tradability/Explainability)
  5. Ambil baris tanggal terbaru, filter investability >= NEAR_PASS
  6. Simpan ke Supabase (tabel watchlist)
  7. Kirim ringkasan ke Telegram
"""

import sys
import pandas as pd

from feature_engine import UNIVERSE, build_feature_store
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer, explain_candidate
from sector_cache import get_sector_map
import database
import notify


def main():
    client = database.get_client()

    print("=== [1/6] Sector mapping ===")
    sector_map = get_sector_map(client, UNIVERSE)

    print("=== [2/6] Build feature store ===")
    result = build_feature_store(UNIVERSE, sector_map=sector_map)
    features = result["features"]

    print("=== [3/6] Hard filter ===")
    filtered = compute_hard_filter(features)

    print("=== [4/6] Decision layer ===")
    decided = compute_decision_layer(filtered)

    print("=== [5/6] Ambil tanggal terbaru + filter investability >= NEAR_PASS ===")
    as_of_date = decided["date"].max()
    latest = decided[decided["date"] == as_of_date].copy()
    candidates = latest[latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]].copy()
    print(f"Tanggal: {pd.Timestamp(as_of_date).date()} — {len(candidates)} kandidat dari {len(latest)} ticker.")

    explanations = {row["symbol"]: explain_candidate(row) for _, row in candidates.iterrows()}

    print("=== [6/6] Simpan ke Supabase + kirim Telegram ===")
    database.upsert_watchlist(client, candidates, explanations)
    notify.send_watchlist_summary(candidates, as_of_date)

    print("Selesai.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Pipeline gagal: {type(e).__name__}: {e}")
        sys.exit(1)
