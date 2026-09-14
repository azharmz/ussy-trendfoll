"""Execute DIAG-001 from the current R2-ready history and Supabase positions."""
from __future__ import annotations

import feature_engine as fe
import pandas as pd

import database
from decision_layer import compute_decision_layer
from hard_filter import compute_hard_filter
from r2_feature_engine import build_feature_store_from_r2
from r2_ready import load_ready_dataset
from sector_cache import get_sector_map
from signal_path_diagnostic import write_signal_path_diagnostic


POSITION_SELECT = (
    "symbol,entry_date,entry_price,realistic_entry_price,atr14_at_entry,"
    "stop_price,status,exit_date,exit_price,days_held,"
    "max_close_since_entry,min_close_since_entry,prev_close"
)


def load_positions(client) -> pd.DataFrame:
    rows = []
    start = 0
    page_size = 1000
    while True:
        resp = (
            client.table("positions")
            .select(POSITION_SELECT)
            .order("entry_date", desc=False)
            .order("symbol", desc=False)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = resp.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return pd.DataFrame(rows)


def main():
    client = database.get_client()
    ready, manifest = load_ready_dataset()
    universe = sorted(ready["ticker"].dropna().unique().tolist())
    sector_map = get_sector_map(client, universe)

    # Earnings lookup is irrelevant to DIAG-001 and makes a full-universe
    # historical diagnostic unnecessarily slow. Disable only for this run.
    original_earnings = fe.compute_days_to_next_earnings
    fe.compute_days_to_next_earnings = lambda *args, **kwargs: None
    try:
        features = build_feature_store_from_r2(
            sector_map=sector_map,
            ready=ready,
            manifest=manifest,
        )["features"]
    finally:
        fe.compute_days_to_next_earnings = original_earnings

    decided = compute_decision_layer(compute_hard_filter(features)).sort_values(["symbol", "date"]).copy()
    positions = load_positions(client)

    duplicate_positions = pd.DataFrame()
    if not positions.empty:
        positions["entry_date"] = pd.to_datetime(positions["entry_date"]).dt.normalize()
        duplicate_positions = positions[
            positions.duplicated(["symbol", "entry_date"], keep=False)
        ].sort_values(["symbol", "entry_date"])
        if not duplicate_positions.empty:
            duplicate_positions.to_csv("signal_path_position_duplicates.csv", index=False)
            keys = duplicate_positions[["symbol", "entry_date"]].drop_duplicates()
            print(f"[DIAG-001][DATA-INTEGRITY] duplicate position keys={len(keys)}")

    events, summary = write_signal_path_diagnostic(decided, positions)
    summary["ready_snapshot_date"] = manifest.get("snapshot_date")
    summary["position_rows"] = int(len(positions))
    summary["duplicate_position_keys"] = int(
        len(duplicate_positions[["symbol", "entry_date"]].drop_duplicates())
        if not duplicate_positions.empty else 0
    )

    # Rewrite summary with source coverage metadata appended.
    import json
    with open("signal_path_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print("=== DIAG-001 SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
