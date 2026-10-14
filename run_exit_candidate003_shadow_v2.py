"""Standalone research-only runner for EXIT-CAND-003 shadow v2.
Dry-run is the default. Live shadow writes require --write and an explicit acknowledgement.
This file is never imported by the production main.py pipeline.
"""
from __future__ import annotations
import argparse
import os
import sys
import pandas as pd
import database
from r2_ready import load_ready_dataset
from r2_feature_engine import build_feature_store_from_r2
import exit_candidate003_shadow_v2 as shadow

ACK_VALUE = "I_UNDERSTAND_SHADOW_ONLY"
REQUIRED_COLUMNS = {"symbol", "date", "open_raw", "high_raw", "low_raw", "close_raw", "ema20"}

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-date", required=True, help="Expected latest READY market date (YYYY-MM-DD)")
    parser.add_argument("--write", action="store_true", help="Persist versioned v2 shadow evidence; otherwise dry-run")
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    as_of = pd.Timestamp(args.as_of_date).normalize()
    if str(as_of.date()) != args.as_of_date:
        raise ValueError("--as-of-date must use exact YYYY-MM-DD format")
    if args.write and os.environ.get("USSY_CAND003_SHADOW_V2_WRITE_ACK") != ACK_VALUE:
        raise RuntimeError(f"Live shadow writes require USSY_CAND003_SHADOW_V2_WRITE_ACK={ACK_VALUE}")

    ready, manifest = load_ready_dataset()
    features = build_feature_store_from_r2(ready=ready, manifest=manifest)["features"].copy()
    missing = sorted(REQUIRED_COLUMNS - set(features.columns))
    if missing:
        raise RuntimeError(f"R2 feature store missing required v2 columns: {missing}")
    features["date"] = pd.to_datetime(features["date"]).dt.normalize()
    latest = features["date"].max()
    if pd.isna(latest) or latest != as_of:
        raise RuntimeError(f"as-of mismatch: requested={as_of.date()} latest_R2_feature_date={latest}")

    client = database.get_client()
    version_rows = (client.table("exit_candidate003_shadow").select("id,position_id,status")
                    .eq("contract_version", shadow.SHADOW_CONTRACT_VERSION).execute().data or [])
    active_count = sum(1 for row in version_rows if row.get("status") == "active")
    positions = (client.table("positions").select("id,symbol,entry_date,realistic_entry_price,atr14_at_entry,status,exit_date,exit_price")
                 .execute().data or [])
    known_ids = {int(row["position_id"]) for row in version_rows}
    eligible = [p for p in positions if p.get("status") == "active" and p.get("exit_date") is None
                and p.get("realistic_entry_price") is not None and p.get("atr14_at_entry") is not None
                and int(p["id"]) not in known_ids]
    print(f"[shadow-v2] contract={shadow.SHADOW_CONTRACT_VERSION} as_of={as_of.date()} R2_latest={latest.date()}")
    print(f"[shadow-v2] mode={'WRITE' if args.write else 'DRY-RUN'} active_v2={active_count} "
          f"active_positions_without_v2={len(eligible)}")
    print("[shadow-v2] production positions are read-only inputs; no production exit/stop/alert/dashboard functions are called.")
    if not args.write:
        print("[shadow-v2] dry-run complete; no database writes attempted.")
        return 0

    shadow.run_shadow(client, features, as_of, features["date"].unique())
    print("[shadow-v2] write pass complete; inspect row counts and evidence before any further run.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[shadow-v2] FATAL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
