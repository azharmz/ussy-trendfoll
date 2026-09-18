"""USSY TrendFoll — authoritative production pipeline.

R2 READY is the production stock-data source. Feature formulas are owned by
feature_engine.py; r2_integration.py is only the source/readiness boundary.
"""
import sys
import pandas as pd
from hard_filter import compute_hard_filter, STATUS_RANK
from decision_layer import compute_decision_layer, explain_candidate
from sector_cache import get_sector_map
from alert_state import compute_alert_transitions
from near_trigger_shadow import add_near_trigger_shadow
from near_trigger_forward_progress import write_forward_validation_progress
from candidate_lifecycle import write_candidate_lifecycle
from r2_ready import load_ready_dataset
from r2_integration import build_feature_store_from_r2
import database, notify, positions
import alert_delivery
import exit_candidate003_shadow

SHADOW_ARTIFACT_PATH = "near_trigger_shadow_snapshot.csv"
LIFECYCLE_ARTIFACT_PATH = "candidate_lifecycle.csv"
VALIDATION_PROGRESS_PATH = "near_trigger_validation_progress.json"
VALIDATION_EPISODES_PATH = "near_trigger_validation_episodes.csv"


def _write_near_trigger_shadow_snapshot(latest: pd.DataFrame, as_of_date):
    shadow = add_near_trigger_shadow(latest)
    monitored = shadow[shadow["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]].copy()
    cols = ["symbol", "date", "close_raw", "investability_status", "tradability_status",
            "has_breakout", "prev_pivot_high", "atr14", "distance_to_prev_pivot_pct",
            "distance_to_prev_pivot_atr", "near_trigger_shadow"]
    monitored[cols].to_csv(SHADOW_ARTIFACT_PATH, index=False)
    n_shadow = int(monitored["near_trigger_shadow"].sum()) if not monitored.empty else 0
    print(f"[near_trigger shadow] {n_shadow}/{len(monitored)} monitored ticker memenuhi frozen development candidate <= 0.60 ATR pada {pd.Timestamp(as_of_date).date()}.")


def main():
    client = database.get_client()
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready universe kosong")
    current_universe = set(universe)
    print(f"[R2] snapshot={manifest.get('snapshot_date')} securities={len(universe)} rows={len(ready)}")
    sector_map = get_sector_map(client, universe)
    features = build_feature_store_from_r2(sector_map=sector_map, ready=ready, manifest=manifest)["features"]
    filtered = compute_hard_filter(features)
    decided = compute_decision_layer(filtered).sort_values(["symbol", "date"])
    decided["prev_close"] = decided.groupby("symbol")["close_raw"].shift(1)
    as_of_date = decided["date"].max()
    latest = decided[decided["date"] == as_of_date].copy()
    candidates = latest[latest["investability_status"].map(STATUS_RANK) >= STATUS_RANK["NEAR_PASS"]].copy()
    missing_latest = sorted(current_universe - set(latest["symbol"].unique()))
    print(f"Tanggal {pd.Timestamp(as_of_date).date()}: {len(candidates)} kandidat / {len(latest)} latest / {len(universe)} ready")
    if missing_latest:
        print(f"[R2 freshness] {len(missing_latest)} ready ticker tanpa bar latest: {missing_latest[:20]}")

    _write_near_trigger_shadow_snapshot(latest, as_of_date)
    write_forward_validation_progress(decided, progress_path=VALIDATION_PROGRESS_PATH, episode_path=VALIDATION_EPISODES_PATH)

    positions.validate_active_position_coverage(client, latest)
    previous = database.get_previous_watchlist(client, as_of_date)
    transitions = compute_alert_transitions(latest, previous, current_universe)
    for e in transitions:
        print(f"[alert] {e['event']}: {e['symbol']} ({e['previous_state']} -> {e['current_state']})")
    explanations = {r["symbol"]: explain_candidate(r) for _, r in candidates.iterrows()}
    database.upsert_watchlist(client, candidates, explanations)

    watchlist_history = database.get_watchlist_history(client)
    write_candidate_lifecycle(watchlist_history, latest, LIFECYCLE_ARTIFACT_PATH, current_universe)

    if transitions:
        alert_delivery.persist_and_deliver_transitions(client, transitions)
    else:
        print("[notify] Tidak ada state change — tidak ada alert event baru.")

    dates = decided["date"].unique()
    positions.fill_realistic_entry_prices(client, decided, as_of_date)
    positions.align_active_stops_to_filled_entry(client)
    exits = positions.check_exits(client, latest, as_of_date, dates)
    notify.send_exit_alerts(exits)
    positions.register_new_positions(client, latest, as_of_date)

    print("[EXIT-CAND-003 shadow] non-decisioning observational pass")
    exit_candidate003_shadow.run_shadow(client, decided, as_of_date, dates)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] Pipeline gagal: {type(e).__name__}: {e}")
        sys.exit(1)
