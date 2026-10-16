"""Standalone research-only runner for EXIT-CAND-003 shadow v2.
Dry-run is the only enabled mode pending a verified database security boundary.
This file is never imported by the production main.py pipeline.
"""
from __future__ import annotations
import argparse
import os
import sys
import pandas as pd
import psycopg
from psycopg.rows import dict_row
from r2_ready import load_ready_dataset, to_feature_contract
import exit_candidate003_shadow_v2 as shadow

WRITE_MODE_ENABLED = False
REQUIRED_COLUMNS = {"symbol", "date", "open_raw", "high_raw", "low_raw", "close_raw", "ema20"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-date", required=True, help="Expected latest READY market date (YYYY-MM-DD)")
    parser.add_argument("--write", action="store_true", help="Disabled until the database security gate is approved")
    return parser.parse_args(argv)


def load_database_inputs():
    """Read through the dedicated PostgreSQL login; never use service_role/PostgREST."""
    database_url = os.environ.get("SHADOW_V2_DATABASE_URL")
    if not database_url:
        raise RuntimeError("Missing SHADOW_V2_DATABASE_URL; refusing fallback to privileged credentials.")
    with psycopg.connect(database_url, row_factory=dict_row, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, position_id, status
                   FROM public.exit_candidate003_shadow
                   WHERE contract_version = %s""",
                (shadow.SHADOW_CONTRACT_VERSION,),
            )
            version_rows = cur.fetchall()
            cur.execute(
                """SELECT id, symbol, entry_date, realistic_entry_price, atr14_at_entry,
                          status, exit_date, exit_price
                   FROM public.positions"""
            )
            positions = cur.fetchall()
    return version_rows, positions


def main(argv=None):
    args = parse_args(argv)
    if args.write and not WRITE_MODE_ENABLED:
        raise RuntimeError("Shadow v2 write mode is disabled: credential-level isolation and approval are still required.")
    as_of = pd.Timestamp(args.as_of_date).normalize()
    if str(as_of.date()) != args.as_of_date:
        raise ValueError("--as-of-date must use exact YYYY-MM-DD format")

    ready, manifest = load_ready_dataset()
    # EXIT-CAND-003 only needs raw OHLC and the production EMA20 formula.
    features = to_feature_contract(ready)
    features["date"] = pd.to_datetime(features["date"]).dt.normalize()
    features = features.sort_values(["symbol", "date"]).reset_index(drop=True)
    features["ema20"] = features.groupby("symbol", sort=False)["close_raw"].transform(
        lambda series: series.ewm(span=20, adjust=False).mean()
    )
    missing = sorted(REQUIRED_COLUMNS - set(features.columns))
    if missing:
        raise RuntimeError(f"R2 feature store missing required v2 columns: {missing}")
    latest = pd.to_datetime(features["date"]).dt.normalize().max()
    if pd.isna(latest) or latest != as_of:
        raise RuntimeError(f"as-of mismatch: requested={as_of.date()} latest_R2_feature_date={latest}")

    # Direct PostgreSQL login uses database-enforced grants/RLS. No service-role fallback.
    version_rows, positions = load_database_inputs()
    active_count = sum(1 for row in version_rows if row.get("status") == "active")
    known_ids = {int(row["position_id"]) for row in version_rows}
    active_missing = [p for p in positions if p.get("status") == "active" and p.get("exit_date") is None
                      and int(p["id"]) not in known_ids]
    valid_missing = [p for p in active_missing if p.get("realistic_entry_price") is not None
                     and p.get("atr14_at_entry") is not None and float(p["atr14_at_entry"]) > 0]
    t1_today, late_bootstrap, no_post_entry_bar, missing_entry_data = [], [], [], 0
    for position in valid_missing:
        if not position.get("entry_date"):
            missing_entry_data += 1
            continue
        history = features[(features["symbol"] == position["symbol"])
                           & (features["date"] > pd.Timestamp(position["entry_date"]).normalize())]
        if history.empty:
            no_post_entry_bar.append(position)
        elif pd.Timestamp(history["date"].min()).normalize() == as_of:
            t1_today.append(position)
        else:
            late_bootstrap.append(position)
    # Diagnostic only: expose exact first-post-entry market inputs for manual review.
    # This does not register shadows, persist evidence, or change write-mode gating.
    for candidate in t1_today:
        symbol = candidate["symbol"]
        candidate_id = int(candidate["id"])
        bar = features[(features["symbol"] == symbol) & (features["date"] == as_of)]
        if len(bar) != 1:
            raise RuntimeError(
                f"Expected exactly one as-of feature row for T+1 candidate "
                f"position_id={candidate_id} symbol={symbol}; found={len(bar)}"
            )
        row = bar.iloc[0]
        entry_price = float(candidate["realistic_entry_price"])
        atr14 = float(candidate["atr14_at_entry"])
        initial_stop = entry_price - shadow.INITIAL_ATR_MULT * atr14
        low = float(row["low_raw"])
        close = float(row["close_raw"])
        ema20 = float(row["ema20"])
        print(
            f"[shadow-v2] T1_DIAGNOSTIC position_id={candidate_id} symbol={symbol} "
            f"bar_date={as_of.date()} open={float(row['open_raw']):.6f} "
            f"high={float(row['high_raw']):.6f} low={low:.6f} "
            f"close={close:.6f} ema20={ema20:.6f} "
            f"entry={entry_price:.6f} atr14_at_entry={atr14:.6f} "
            f"initial_stop={initial_stop:.6f} "
            f"low_at_or_below_initial_stop={low <= initial_stop} "
            f"close_below_ema20={close < ema20}"
        )

    print(f"[shadow-v2] contract={shadow.SHADOW_CONTRACT_VERSION} as_of={as_of.date()} R2_latest={latest.date()}")
    print(f"[shadow-v2] mode=DRY-RUN active_v2={active_count} "
          f"active_missing_v2={len(active_missing)} valid_missing_v2={len(valid_missing)}")
    print(f"[shadow-v2] cohort_preview genuine_T1_today={len(t1_today)} "
          f"late_bootstrap_rejected={len(late_bootstrap)} no_post_entry_bar={len(no_post_entry_bar)} "
          f"missing_entry_date={missing_entry_data}")
    print("[shadow-v2] positions read through dedicated PostgreSQL login; no production exit/stop/alert/dashboard functions called.")
    print("[shadow-v2] dry-run complete; no database writes attempted.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[shadow-v2] FATAL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
