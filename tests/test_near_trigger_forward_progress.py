import pandas as pd

from near_trigger_forward_progress import collect_forward_validation


def _row(symbol, date, distance, breakout=False, investability="PASS"):
    return {
        "symbol": symbol,
        "date": pd.Timestamp(date),
        "close_raw": 100.0 - distance,
        "prev_pivot_high": 100.0,
        "atr14": 1.0,
        "investability_status": investability,
        "tradability_status": "FAIL",
        "has_breakout": breakout,
    }


def test_consecutive_shadow_days_count_as_one_episode():
    rows = [
        _row("AAA", "2026-09-14", 1.0),
        _row("AAA", "2026-09-15", 0.5),
        _row("AAA", "2026-09-16", 0.4),
        _row("AAA", "2026-09-17", 0.3),
        _row("AAA", "2026-09-18", -0.1, breakout=True),
        _row("AAA", "2026-09-21", 1.2),
    ]
    episodes, controls, metrics = collect_forward_validation(pd.DataFrame(rows))
    assert len(episodes) == 1
    assert metrics["shadow_episodes"] == 1
    assert metrics["unique_symbols"] == 1
    assert metrics["shadow_breakouts_3d"] == 1
    assert metrics["shadow_breakouts_5d"] == 1


def test_unmatured_episode_is_not_counted():
    rows = [
        _row("BBB", "2026-09-14", 1.0),
        _row("BBB", "2026-09-15", 0.5),
        _row("BBB", "2026-09-16", 0.4),
        _row("BBB", "2026-09-17", 0.3),
    ]
    episodes, controls, metrics = collect_forward_validation(pd.DataFrame(rows))
    assert episodes.empty
    assert metrics["shadow_episodes"] == 0


def test_invalidation_matures_episode_early():
    rows = [
        _row("CCC", "2026-09-14", 1.0),
        _row("CCC", "2026-09-15", 0.5),
        _row("CCC", "2026-09-16", 0.8, investability="FAIL"),
    ]
    episodes, controls, metrics = collect_forward_validation(pd.DataFrame(rows))
    assert len(episodes) == 1
    assert bool(episodes.iloc[0]["invalidation_before_breakout"])
    assert metrics["shadow_breakouts_5d"] == 0


def test_consecutive_control_days_count_as_one_control_episode():
    rows = [
        _row("DDD", "2026-09-14", 0.5),
        _row("DDD", "2026-09-15", 0.8),
        _row("DDD", "2026-09-16", 0.9),
        _row("DDD", "2026-09-17", 1.0),
        _row("DDD", "2026-09-18", 1.1),
        _row("DDD", "2026-09-21", 1.2),
        _row("DDD", "2026-09-22", 1.3),
    ]
    episodes, controls, metrics = collect_forward_validation(pd.DataFrame(rows))
    assert len(controls) == 1
    assert metrics["control_episodes"] == 1
