"""
USSY TrendFoll — Main Pipeline (dijalankan harian via GitHub Actions)
========================================================================
Urutan:
  1. Load trusted R2 ready universe + sector mapping cache
  2. Build feature store dari OHLCV R2 ready
  3. Hard filter (5 kriteria PASS/NEAR_PASS/FAIL, non-compensatory)
  4. Decision layer (Investability/Tradability/Explainability)
  5. Ambil baris tanggal terbaru, filter investability >= NEAR_PASS
  6. Simpan ke Supabase + kirim Telegram
  7. Tracking posisi otomatis
"""

import sys
import pandas as pd

from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer, explain_candidate
from sector_cache import get_sector_map
from r2_ready import load_ready_dataset
from r2_feature_engine import build_feature_store_from_r2
import database
import notify
import positions


def main():
    client = database.get_client()

    print("=== [1/7] R2 ready universe + sector mapping ===")
    ready_frame, ready_manifest = load_ready_dataset()
    universe = sorted(ready_frame["ticker"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready universe kosong")
    print(
        f"R2 snapshot={ready_manifest.get('snapshot_date')} "
        f"securities={len(universe)} rows={len(ready_frame)}"
    )
    sector_map = get_sector_map(client, universe)

    print("=== [2/7] Build feature store dari R2 ready OHLCV ===")
    result = build_feature_store_from_r2(sector_map=sector_map)
    features = result["features"]

    print("=== [3/7] Hard filter ===")
    filtered = compute_hard_filter(features)

    print("=== [4/7] Decision layer ===")
    decided = compute_decision_layer(filtered)
    decided = decided.sort_values(["symbol", "date"])
    decided["prev_close"] = decided.groupby("symbol")["close_raw"].shift(1)

    print("=== [5/7] Ambil tanggal terbaru + filter investability >= NEAR_PASS ===")
    as_of_date = decided["date"].max()
    latest = decided[decided["date"] == as_of_date].copy()
    candidates = latest[
        latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]
    ].copy()
    print(
        f"Tanggal: {pd.Timestamp(as_of_date).date()} — "
        f"{len(candidates)} kandidat dari {len(latest)} ticker pada tanggal terbaru "
        f"(R2 ready universe total {len(universe)})."
    )

    # Readiness menjamin bar-count contract, bukan market freshness. Ticker ready
    # yang stale tidak punya row pada as_of_date global sehingga tidak ikut latest.
    missing_latest = sorted(set(universe) - set(latest["symbol"].unique()))
    if missing_latest:
        print(
            f"[R2 freshness] {len(missing_latest)} ready ticker tidak punya bar "
            f"pada tanggal latest dan otomatis tidak discan: {missing_latest[:20]}"
            + (" ..." if len(missing_latest) > 20 else "")
        )

    # Posisi aktif tidak boleh hilang diam-diam dari snapshot terbaru.
    positions.validate_active_position_coverage(client, latest)

    explanations = {
        row["symbol"]: explain_candidate(row) for _, row in candidates.iterrows()
    }

    print("=== [6/7] Simpan ke Supabase + kirim Telegram (watchlist) ===")
    database.upsert_watchlist(client, candidates, explanations)
    notify.send_watchlist_summary(candidates, as_of_date)

    print("=== [7/7] Position tracking: entry realistis, exit, entry baru ===")
    all_trading_dates = decided["date"].unique()
    positions.fill_realistic_entry_prices(client, decided, as_of_date)
    positions.align_active_stops_to_filled_entry(client)
    exits = positions.check_exits(client, latest, as_of_date, all_trading_dates)
    notify.send_exit_alerts(exits)
    positions.register_new_positions(client, latest, as_of_date)

    print("Selesai.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Pipeline gagal: {type(e).__name__}: {e}")
        sys.exit(1)
