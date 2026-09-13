import sys
import pandas as pd
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer, explain_candidate
from sector_cache import get_sector_map
from alert_state import compute_alert_transitions
from r2_ready import load_ready_dataset
from r2_feature_engine import build_feature_store_from_r2
import database, notify, positions


def main():
    client = database.get_client()
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready universe kosong")
    print(f"[R2] snapshot={manifest.get('snapshot_date')} securities={len(universe)} rows={len(ready)}")
    sector_map = get_sector_map(client, universe)
    features = build_feature_store_from_r2(
        sector_map=sector_map,
        ready=ready,
        manifest=manifest,
    )["features"]
    filtered = compute_hard_filter(features)
    decided = compute_decision_layer(filtered).sort_values(["symbol", "date"])
    decided["prev_close"] = decided.groupby("symbol")["close_raw"].shift(1)
    as_of_date = decided["date"].max()
    latest = decided[decided["date"] == as_of_date].copy()
    candidates = latest[latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]].copy()
    missing_latest = sorted(set(universe) - set(latest["symbol"].unique()))
    print(f"Tanggal {pd.Timestamp(as_of_date).date()}: {len(candidates)} kandidat / {len(latest)} latest / {len(universe)} ready")
    if missing_latest:
        print(f"[R2 freshness] {len(missing_latest)} ready ticker tanpa bar latest: {missing_latest[:20]}")
    positions.validate_active_position_coverage(client, latest)
    previous = database.get_previous_watchlist(client, as_of_date)
    transitions = compute_alert_transitions(latest, previous)
    for e in transitions:
        print(f"[alert] {e['event']}: {e['symbol']} ({e['previous_state']} -> {e['current_state']})")
    explanations = {r["symbol"]: explain_candidate(r) for _, r in candidates.iterrows()}
    database.upsert_watchlist(client, candidates, explanations)
    if transitions:
        notify.send_watchlist_summary(candidates, as_of_date)
    else:
        print("[notify] Tidak ada state change — skip digest Telegram.")
    dates = decided["date"].unique()
    positions.fill_realistic_entry_prices(client, decided, as_of_date)
    positions.align_active_stops_to_filled_entry(client)
    exits = positions.check_exits(client, latest, as_of_date, dates)
    notify.send_exit_alerts(exits)
    positions.register_new_positions(client, latest, as_of_date)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] R2 pipeline gagal: {type(e).__name__}: {e}")
        sys.exit(1)
