import pandas as pd
import run_stop_exec001 as audit


def _event():
    return {"symbol": "X", "t0_date": "2026-01-01"}


def _history(open_day1, low_day1, stop_at=98.0):
    # ATR=1 and entry=100 would make stop=98 only with multiplier 2.
    # We explicitly construct enough forward rows for the governed 45-day evaluator.
    rows = [{
        "symbol": "X", "date": pd.Timestamp("2026-01-01"), "open_raw": 99.0,
        "high_raw": 101.0, "low_raw": 98.0, "close_raw": 100.0,
        "atr14": (100.0 - stop_at) / 2.0, "ema20": 90.0,
    }]
    for i in range(1, 47):
        op = open_day1 if i == 1 else 100.0
        lo = low_day1 if i == 1 else 99.0
        rows.append({
            "symbol": "X", "date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
            "open_raw": op, "high_raw": max(op, 101.0), "low_raw": lo,
            "close_raw": 100.0, "atr14": 1.0, "ema20": 90.0,
        })
    return pd.DataFrame(rows)


def test_gap_aware_fills_open_when_open_below_stop():
    g = _history(open_day1=95.0, low_day1=94.0)
    cur = audit.evaluate(g, _event(), "CURRENT_EXACT_STOP")
    gap = audit.evaluate(g, _event(), "GAP_AWARE_DIAGNOSTIC")
    assert cur["exit_reason"] == "stop_loss"
    assert cur["exit_price"] == 98.0
    assert gap["exit_reason"] == "stop_loss_gap"
    assert gap["exit_price"] == 95.0
    assert gap["gap_slippage_vs_stop"] == 95.0 / 98.0 - 1


def test_gap_aware_touch_preserves_exact_stop_when_open_above_stop():
    g = _history(open_day1=100.0, low_day1=97.0)
    cur = audit.evaluate(g, _event(), "CURRENT_EXACT_STOP")
    gap = audit.evaluate(g, _event(), "GAP_AWARE_DIAGNOSTIC")
    assert cur["exit_price"] == 98.0
    assert gap["exit_reason"] == "stop_loss_touch"
    assert gap["exit_price"] == 98.0
    assert pd.isna(gap["gap_slippage_vs_stop"])
