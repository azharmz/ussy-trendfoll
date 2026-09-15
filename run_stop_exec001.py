"""STOP-EXEC-001: audit CURRENT exact-stop fill against gap-aware execution.

Diagnostic only. No production mutation and no parameter tuning.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import run_exit_candidate001_development as base

OUT = Path("artifacts/stop_exec001")
MAX_HOLD = 45
ATR_MULT = 2.0
TOL = 1e-12
VARIANTS = ("CURRENT_EXACT_STOP", "GAP_AWARE_DIAGNOSTIC")


def evaluate(g, event, variant):
    g = g.sort_values("date").reset_index(drop=True)
    t0 = pd.Timestamp(event["t0_date"])
    ix = g.index[g.date == t0]
    if len(ix) != 1 or ix[0] + MAX_HOLD >= len(g):
        return None
    i0 = int(ix[0])
    entry_i = i0 + 1
    entry = float(g.iloc[entry_i].open_raw)
    atr0 = float(g.iloc[i0].atr14) if pd.notna(g.iloc[i0].atr14) else np.nan
    if not np.isfinite(entry) or not np.isfinite(atr0) or atr0 <= 0:
        return None
    stop = entry - ATR_MULT * atr0
    fwd = g.iloc[entry_i:entry_i + MAX_HOLD].reset_index(drop=True)
    reason = "max_holding"
    exit_day = MAX_HOLD
    exit_price = float(fwd.iloc[-1].close_raw)
    gap_slippage = np.nan

    for j, row in fwd.iterrows():
        day = j + 1
        op = float(row.open_raw)
        lo = float(row.low_raw)
        if lo <= stop:
            exit_day = day
            if variant == "GAP_AWARE_DIAGNOSTIC" and op <= stop:
                reason = "stop_loss_gap"
                exit_price = op
                gap_slippage = op / stop - 1
            else:
                reason = "stop_loss" if variant == "CURRENT_EXACT_STOP" else "stop_loss_touch"
                exit_price = stop
            break
        if day >= MAX_HOLD:
            break
        if pd.notna(row.ema20) and float(row.close_raw) < float(row.ema20):
            reason = "trend_exit"
            exit_day = day
            exit_price = float(row.close_raw)
            break

    return {
        "symbol": event["symbol"],
        "t0_date": str(t0.date()),
        "variant": variant,
        "entry_price": entry,
        "stop_price": stop,
        "exit_day": exit_day,
        "exit_reason": reason,
        "exit_price": exit_price,
        "realized_return": exit_price / entry - 1,
        "gap_slippage_vs_stop": gap_slippage,
    }


def main():
    dec, events, meta = base.build_corpus()
    groups = {s: g.sort_values("date").reset_index(drop=True) for s, g in dec.groupby("symbol", sort=False)}
    rows = []
    for _, event in events.iterrows():
        pair = [evaluate(groups[event.symbol], event, v) for v in VARIANTS]
        if all(x is not None for x in pair):
            rows.extend(pair)
    df = pd.DataFrame(rows)
    counts = df.groupby("variant").size().to_dict()
    if set(counts) != set(VARIANTS) or len(set(counts.values())) != 1:
        raise RuntimeError(f"non-comparable paired corpus: {counts}")

    cur = df[df.variant == "CURRENT_EXACT_STOP"].set_index(["symbol", "t0_date"])
    gap = df[df.variant == "GAP_AWARE_DIAGNOSTIC"].set_index(["symbol", "t0_date"])
    paired = cur[["realized_return", "exit_reason", "exit_price", "stop_price"]].join(
        gap[["realized_return", "exit_reason", "exit_price", "gap_slippage_vs_stop"]],
        lsuffix="_current", rsuffix="_gapaware"
    )
    paired["paired_return_delta_gapaware_minus_current"] = paired.realized_return_gapaware - paired.realized_return_current
    paired["outcome_changed"] = paired.paired_return_delta_gapaware_minus_current.abs() > TOL
    paired = paired.reset_index()

    stop_events = int((cur.exit_reason == "stop_loss").sum())
    gap_events = gap[gap.exit_reason == "stop_loss_gap"]
    touch_events = int((gap.exit_reason == "stop_loss_touch").sum())
    slip = gap_events.gap_slippage_vs_stop.dropna()
    delta = paired.paired_return_delta_gapaware_minus_current

    summary = {
        "audit": "STOP-EXEC-001",
        "status": "DIAGNOSTIC_ONLY_NO_PRODUCTION_CHANGE",
        "corpus": meta,
        "paired_events": int(len(paired)),
        "current_stop_events": stop_events,
        "gap_through_events": int(len(gap_events)),
        "gap_fraction_of_current_stops": float(len(gap_events) / stop_events) if stop_events else 0.0,
        "touch_events": touch_events,
        "gap_slippage_vs_stop": {
            "median": float(slip.median()) if len(slip) else None,
            "q25": float(slip.quantile(.25)) if len(slip) else None,
            "q75": float(slip.quantile(.75)) if len(slip) else None,
            "worst": float(slip.min()) if len(slip) else None,
        },
        "current": {
            "median_return": float(cur.realized_return.median()),
            "positive_rate": float((cur.realized_return > 0).mean()),
        },
        "gap_aware": {
            "median_return": float(gap.realized_return.median()),
            "positive_rate": float((gap.realized_return > 0).mean()),
        },
        "paired_delta_gapaware_minus_current": {
            "median": float(delta.median()),
            "mean": float(delta.mean()),
            "q25": float(delta.quantile(.25)),
            "q75": float(delta.quantile(.75)),
            "worst": float(delta.min()),
            "changed_events": int(paired.outcome_changed.sum()),
            "changed_fraction": float(paired.outcome_changed.mean()),
        },
        "terminal_interpretation": (
            "CURRENT EXACT-STOP EXECUTION FEASIBILITY DEFECT OBSERVED"
            if len(gap_events) else "NO OBSERVED GAP-THROUGH IN GOVERNED CORPUS"
        ),
        "governance": {
            "atr_multiplier": ATR_MULT,
            "ema_period": 20,
            "max_holding": MAX_HOLD,
            "optimization": "none",
            "production_change": "none",
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "events.csv", index=False)
    paired.to_csv(OUT / "paired_events.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
