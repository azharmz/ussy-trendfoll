"""Audit Candidate Lifecycle membership against the authoritative current R2 READY universe.

Diagnostic only. This script does not mutate Supabase, R2, watchlist, lifecycle,
or production decisions.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import database
from r2_ready import load_ready_dataset

SUMMARY_PATH = Path("r2_lifecycle_membership_audit.json")
DETAIL_PATH = Path("r2_lifecycle_membership_audit.csv")


def main() -> None:
    client = database.get_client()
    ready, manifest = load_ready_dataset()
    history = database.get_watchlist_history(client)

    ready_symbols = set(ready["ticker"].dropna().astype(str).str.strip())
    history_symbols = set()
    if history is not None and not history.empty:
        history_symbols = set(history["symbol"].dropna().astype(str).str.strip())

    intersection = ready_symbols & history_symbols
    legacy_only = history_symbols - ready_symbols
    r2_not_yet_lifecycle = ready_symbols - history_symbols

    first_last = {}
    if history is not None and not history.empty:
        h = history.copy()
        h["date"] = pd.to_datetime(h["date"], errors="coerce")
        for symbol, g in h.groupby(h["symbol"].astype(str).str.strip()):
            first_last[symbol] = {
                "first_watch_date": g["date"].min().date().isoformat() if g["date"].notna().any() else None,
                "last_watch_date": g["date"].max().date().isoformat() if g["date"].notna().any() else None,
            }

    rows = []
    for symbol in sorted(ready_symbols | history_symbols):
        in_r2 = symbol in ready_symbols
        in_lifecycle = symbol in history_symbols
        if in_r2 and in_lifecycle:
            membership = "R2_AND_LIFECYCLE"
        elif in_lifecycle:
            membership = "LEGACY_ONLY_NOT_CURRENT_R2"
        else:
            membership = "CURRENT_R2_NOT_YET_LIFECYCLE"
        dates = first_last.get(symbol, {})
        rows.append({
            "symbol": symbol,
            "membership": membership,
            "in_current_r2_ready": in_r2,
            "in_historical_watchlist": in_lifecycle,
            "first_watch_date": dates.get("first_watch_date"),
            "last_watch_date": dates.get("last_watch_date"),
        })

    pd.DataFrame(rows).to_csv(DETAIL_PATH, index=False)

    summary = {
        "audit": "R2-LIFECYCLE-MEMBERSHIP",
        "status": "DIAGNOSTIC_ONLY_NO_MUTATION",
        "ready_pointer": "production/ready/current.json",
        "ready_snapshot_date": manifest.get("snapshot_date"),
        "ready_manifest_rows": manifest.get("rows"),
        "current_r2_ready_symbols": len(ready_symbols),
        "historical_lifecycle_symbols": len(history_symbols),
        "r2_and_lifecycle": len(intersection),
        "legacy_only_not_current_r2": len(legacy_only),
        "current_r2_not_yet_lifecycle": len(r2_not_yet_lifecycle),
        "legacy_only_symbols": sorted(legacy_only),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"detail={DETAIL_PATH} rows={len(rows)}")


if __name__ == "__main__":
    main()
