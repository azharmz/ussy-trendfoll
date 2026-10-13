import pandas as pd

from exit_conversion import simulate_exit_conversion, summarize_exit_conversion


def _history(rows):
    dates = pd.date_range("2026-01-02", periods=len(rows), freq="B")
    frame = []
    for i, r in enumerate(rows):
        frame.append({
            "symbol": "AAA", "date": dates[i],
            "open_raw": r.get("open", r["close"]),
            "high_raw": r.get("high", r["close"] + 1),
            "low_raw": r.get("low", r["close"] - 1),
            "close_raw": r["close"], "ema20": r.get("ema20", 100.0),
            "atr14": r.get("atr", 2.0),
        })
    return pd.DataFrame(frame)


def _event(history, index=0):
    return pd.DataFrame([{"symbol": "AAA", "t0_date": history.iloc[index]["date"]}])


def test_stop_loss_has_priority_and_uses_stop_fill():
    history = _history([
        {"close": 100, "open": 100, "high": 101, "low": 99, "ema20": 99},
        {"close": 94, "open": 100, "high": 105, "low": 95, "ema20": 100},
        {"close": 100, "open": 95, "high": 101, "low": 94, "ema20": 99},
    ])
    result = simulate_exit_conversion(history, _event(history))
    trade = result.iloc[0]
    assert trade["exit_reason"] == "stop_loss"
    assert trade["exit_price"] == 96.0
    assert round(trade["realized_return"], 6) == -0.04
    assert round(trade["mae_return"], 6) == -0.04
    assert trade["mfe_return"] == 0.0


def test_trend_exit_uses_close_and_includes_exit_day_excursion():
    history = _history([
        {"close": 100, "open": 100, "high": 101, "low": 99, "ema20": 99},
        {"close": 101, "open": 100, "high": 102, "low": 99, "ema20": 100},
        {"close": 99, "open": 101, "high": 104, "low": 98, "ema20": 100},
        {"close": 103, "open": 99, "high": 104, "low": 98, "ema20": 100},
    ])
    result = simulate_exit_conversion(history, _event(history))
    trade = result.iloc[0]
    assert trade["exit_reason"] == "trend_exit"
    assert trade["exit_price"] == 99.0
    assert round(trade["realized_return"], 6) == -0.01
    assert round(trade["mfe_return"], 6) == 0.04
    assert trade["time_to_mfe_bars"] == 2
    assert round(trade["giveback_return"], 6) == 0.05


def test_unresolved_trade_is_censored_not_zero_return():
    history = _history([
        {"close": 100, "open": 100, "high": 101, "low": 99, "ema20": 90},
        {"close": 101, "open": 100, "high": 102, "low": 99, "ema20": 90},
        {"close": 102, "open": 101, "high": 103, "low": 100, "ema20": 90},
    ])
    result = simulate_exit_conversion(history, _event(history), max_holding_bars=45)
    assert result.iloc[0]["simulation_status"] == "censored_no_exit"
    assert pd.isna(result.iloc[0]["realized_return"])
    summary = summarize_exit_conversion(result)
    assert summary["censored_no_exit"] == 1
    assert summary["exited_trades"] == 0


def test_new_onset_during_active_trade_is_blocked():
    history = _history([
        {"close": 100, "open": 100, "high": 101, "low": 99, "ema20": 90},
        {"close": 101, "open": 100, "high": 102, "low": 99, "ema20": 90},
        {"close": 102, "open": 101, "high": 103, "low": 100, "ema20": 90},
        {"close": 103, "open": 102, "high": 104, "low": 101, "ema20": 90},
        {"close": 99, "open": 103, "high": 104, "low": 98, "ema20": 100},
        {"close": 101, "open": 99, "high": 102, "low": 98, "ema20": 100},
    ])
    events = pd.DataFrame([
        {"symbol": "AAA", "t0_date": history.iloc[0]["date"]},
        {"symbol": "AAA", "t0_date": history.iloc[2]["date"]},
    ])
    result = simulate_exit_conversion(history, events)
    assert result.iloc[0]["exit_reason"] == "trend_exit"
    assert result.iloc[1]["simulation_status"] == "blocked_overlap"
