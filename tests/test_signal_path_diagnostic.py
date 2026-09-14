import pandas as pd

from signal_path_diagnostic import build_signal_path_events, link_positions


def _rows():
    dates = pd.date_range("2026-01-01", periods=8, freq="B")
    close = [99, 100, 105, 106, 104, 103, 107, 108]
    ready = [False, False, True, True, False, False, True, True]
    rows = []
    for i, (d, c, r) in enumerate(zip(dates, close, ready)):
        rows.append({
            "symbol": "AAA", "date": d,
            "open_raw": c - 0.5, "high_raw": c + 1, "low_raw": c - 1, "close_raw": c,
            "hard_filter_status": "PASS",
            "investability_status": "PASS", "tradability_status": "PASS" if r else "FAIL",
            "trend_status": "PASS", "liquidity_status": "PASS", "rs_status": "PASS",
            "price_status": "PASS", "regime_status": "PASS", "market_regime": "Bullish",
            "has_breakout": r, "has_volume_confirmation": r,
            "breakout_volume_percentile": 90 if r else 50,
            "vcp_tightness": 70, "has_tight_structure": True,
            "prev_pivot_high": 102 if i >= 2 else 101,
            "atr14": 2.0,
        })
    return pd.DataFrame(rows)


def test_consecutive_entry_ready_days_are_one_episode():
    events = build_signal_path_events(_rows())
    assert len(events) == 2
    assert events.iloc[0]["t0_date"] == pd.Timestamp("2026-01-05")
    assert events.iloc[1]["t0_date"] == pd.Timestamp("2026-01-09")


def test_tminus1_and_executable_path_metrics():
    events = build_signal_path_events(_rows())
    first = events.iloc[0]
    assert round(first["ret_tminus1_t0"], 6) == 0.05
    assert first["t1_available"]
    assert first["t3_available"]
    assert first["t1_open"] == 105.5
    assert round(first["gap_t0close_t1open"], 6) == round(105.5 / 105 - 1, 6)
    assert round(first["pivot_extension_atr_t0"], 6) == 1.5


def test_position_link_uses_symbol_and_t0_date():
    events = build_signal_path_events(_rows())
    positions = pd.DataFrame([{
        "symbol": "AAA",
        "entry_date": "2026-01-05",
        "entry_price": 105.0,
        "realistic_entry_price": 105.5,
        "exit_date": "2026-01-09",
        "exit_price": 107.0,
        "exit_reason": "trend_exit",
        "status": "closed",
    }])
    linked = link_positions(events, positions)
    assert bool(linked.iloc[0]["position_linked"])
    assert not bool(linked.iloc[1]["position_linked"])
    assert round(linked.iloc[0]["realized_return_from_realistic_entry"], 6) == round(107 / 105.5 - 1, 6)
