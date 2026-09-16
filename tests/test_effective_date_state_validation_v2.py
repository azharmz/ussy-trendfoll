"""Governed untouched validation set for the frozen effective-date correction.

Cycle V1 was invalidated before semantic interpretation because its fixtures omitted
required input-contract field `date`. V1 remains unchanged as audit evidence.
This V2 set corrects only fixture contract completeness and is frozen before first run.
"""
import unittest

import pandas as pd

from alert_state import compute_alert_transitions
from candidate_lifecycle import build_candidate_lifecycle


def frame(rows):
    return pd.DataFrame(rows)


class EffectiveDateStateUntouchedValidationV2(unittest.TestCase):
    def test_mixed_population_alert_states(self):
        previous = frame([
            {"symbol": "LIVE", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "NEAR_PASS"},
            {"symbol": "STALE", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "NEAR_PASS"},
            {"symbol": "REMOVED", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "NEAR_PASS"},
        ])
        latest = frame([
            {"symbol": "LIVE", "date": "2026-09-16", "investability_status": "PASS", "tradability_status": "NEAR_PASS", "close_raw": 12.0},
        ])
        events = compute_alert_transitions(latest, previous, {"LIVE", "STALE"})
        states = {row["symbol"]: row["event"] for row in events}
        self.assertNotIn("LIVE", states)
        self.assertEqual(states["STALE"], "DATA_UNAVAILABLE")
        self.assertEqual(states["REMOVED"], "OUT_OF_UNIVERSE")

    def test_present_failure_and_two_absence_causes_remain_distinct(self):
        previous = frame([
            {"symbol": "FAILED", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
            {"symbol": "STALE", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
            {"symbol": "REMOVED", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        latest = frame([
            {"symbol": "FAILED", "date": "2026-09-16", "investability_status": "FAIL", "tradability_status": "FAIL", "close_raw": 7.0},
        ])
        events = compute_alert_transitions(latest, previous, {"FAILED", "STALE"})
        states = {row["symbol"]: row["event"] for row in events}
        self.assertEqual(states, {
            "FAILED": "INVALIDATED",
            "STALE": "DATA_UNAVAILABLE",
            "REMOVED": "OUT_OF_UNIVERSE",
        })

    def test_mixed_population_lifecycle_states(self):
        history = frame([
            {"symbol": "FAILED", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
            {"symbol": "STALE", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
            {"symbol": "REMOVED", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        latest = frame([
            {"symbol": "FAILED", "date": "2026-09-16", "investability_status": "FAIL", "tradability_status": "FAIL"},
        ])
        lifecycle = build_candidate_lifecycle(history, latest, {"FAILED", "STALE"})
        states = dict(zip(lifecycle["symbol"], lifecycle["current_state"]))
        self.assertEqual(states["FAILED"], "INVALIDATED")
        self.assertEqual(states["STALE"], "DATA_UNAVAILABLE")
        self.assertEqual(states["REMOVED"], "OUT_OF_UNIVERSE")

    def test_reentry_uses_current_facts_not_prior_absence(self):
        history = frame([
            {"symbol": "RETURN", "date": "2026-09-10", "investability_status": "PASS", "tradability_status": "FAIL"},
        ])
        latest = frame([
            {"symbol": "RETURN", "date": "2026-09-16", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        lifecycle = build_candidate_lifecycle(history, latest, {"RETURN"})
        row = lifecycle[lifecycle["symbol"] == "RETURN"].iloc[0]
        self.assertEqual(row["current_state"], "ACTIONABLE")
        self.assertTrue(bool(row["currently_actionable"]))

    def test_snapshot_membership_inconsistency_fails_closed(self):
        latest = frame([
            {"symbol": "GHOST", "date": "2026-09-16", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        with self.assertRaises(ValueError):
            compute_alert_transitions(latest, pd.DataFrame(), {"OTHER"})


if __name__ == "__main__":
    unittest.main()
