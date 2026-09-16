import pandas as pd

from candidate_lifecycle import build_candidate_lifecycle


def test_near_pass_candidate_remains_in_lifecycle_after_leaving_watchlist():
    history = pd.DataFrame([
        {
            "symbol": "AAA", "date": "2026-09-10", "close_raw": 100.0,
            "investability_status": "PASS", "tradability_status": "NEAR_PASS",
        },
        {
            "symbol": "AAA", "date": "2026-09-11", "close_raw": 101.0,
            "investability_status": "PASS", "tradability_status": "NEAR_PASS",
        },
    ])
    latest = pd.DataFrame([
        {
            "symbol": "AAA", "date": "2026-09-12", "close_raw": 98.0,
            "investability_status": "FAIL", "tradability_status": "FAIL",
        },
    ])

    out = build_candidate_lifecycle(history, latest, {"AAA"})
    row = out.iloc[0]

    assert row["symbol"] == "AAA"
    assert bool(row["ever_tradability_near_pass"]) is True
    assert row["watch_days"] == 2
    assert row["last_watch_tradability"] == "NEAR_PASS"
    assert row["current_state"] == "INVALIDATED"
    assert bool(row["currently_monitored"]) is False


def test_current_actionable_candidate_is_marked_actionable():
    history = pd.DataFrame([
        {
            "symbol": "BBB", "date": "2026-09-10", "close_raw": 50.0,
            "investability_status": "NEAR_PASS", "tradability_status": "FAIL",
        },
    ])
    latest = pd.DataFrame([
        {
            "symbol": "BBB", "date": "2026-09-11", "close_raw": 52.0,
            "investability_status": "PASS", "tradability_status": "PASS",
        },
    ])

    out = build_candidate_lifecycle(history, latest, {"BBB"})
    row = out.iloc[0]

    assert row["current_state"] == "ACTIONABLE"
    assert bool(row["currently_monitored"]) is True
    assert bool(row["currently_actionable"]) is True
