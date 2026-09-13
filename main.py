"""
USSY TrendFoll — Main Pipeline (dijalankan harian via GitHub Actions)
========================================================================
Urutan:
  1. Ambil sector mapping
  2. Build feature store
  3. Hard filter
  4. Decision layer (Investability/Tradability/Explainability)
  5. Ambil snapshot terbaru + hitung state transition vs watchlist sebelumnya
  6. Simpan watchlist + kirim notifikasi hanya bila ada state change
  7. Position tracking
"""

import sys
import pandas as pd

from feature_engine import UNIVERSE, build_feature_store
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer, explain_candidate
from sector_cache import get_sector_map
from alert_state import compute_alert_transitions
import database
import notify
import positions


def main():
    client = database.get_client()

    print("=== [1/7] Sector mapping ===")
    sector_map = get_sector_map(client, UNIVERSE)

    print("=== [2/7] Build feature store ===")
    result = build_feature_store(UNIVERSE, sector_map=sector_map)
    features = result["features"]

    print("=== [3/7] Hard filter ===")
    filtered = compute_hard_filter(features)

    print("=== [4/7] Decision layer ===")
    decided = compute_decision_layer(filtered)
    decided = decided.sort_values(["symbol", "date"])
    decided["prev_close"] = decided.groupby("symbol")["close_raw"].shift(1)

    print("=== [5/7] Latest snapshot + alert state transition ===")
    as_of_date = decided["date"].max()
    latest = decided[decided["date"] == as_of_date].copy()
    candidates = latest[
        latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]
    ].copy()
    print(f"Tanggal: {pd.Timestamp(as_of_date).date()} — {len(candidates)} kandidat dari {len(latest)} ticker.")

    positions.validate_active_position_coverage(client, latest)

    previous_watchlist = database.get_previous_watchlist(client, as_of_date)
    transitions = compute_alert_transitions(latest, previous_watchlist)
    if transitions:
        print(f"[alert] {len(transitions)} state change:")
        for event in transitions:
            print(
                f"  {event['event']}: {event['symbol']} "
                f"({event['previous_state']} -> {event['current_state']}; "
                f"investability={event.get('investability_status')}, "
                f"tradability={event.get('tradability_status')})"
            )
    else:
        print("[alert] Tidak ada state change.")

    explanations = {row["symbol"]: explain_candidate(row) for _, row in candidates.iterrows()}

    print("=== [6/7] Simpan watchlist + notification gate ===")
    database.upsert_watchlist(client, candidates, explanations)
    if transitions:
        # Transport Telegram yang ada tetap dipakai; perbedaannya sekarang
        # digest tidak dikirim setiap hari jika state tidak berubah.
        notify.send_watchlist_summary(candidates, as_of_date)
    else:
        print("[notify] Watchlist tidak berubah bermakna — skip digest Telegram.")

    print("=== [7/7] Position tracking ===")
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
