import unittest

import pandas as pd

from alert_state import compute_alert_transitions
from candidate_lifecycle import build_candidate_lifecycle


class EffectiveDateStateUntouchedValidationTests(unittest.TestCase):
    """Independent one-shot validation scenarios for the frozen three-way state contract.

    This file is a governed validation set, not a development characterization suite.
    After its first execution it must not be edited to make a failing correction pass.
    """

    def _latest(self, rows):
        return pd.DataFrame(rows)

    def _previous(self, symbols):
        return pd.DataFrame(
            [
                {
                    "symbol": symbol,
                    "investability_status": "PASS",
                    "tradability_status": "NEAR_PASS",
                }
                for symbol in symbols
            ]
        )

    def test_mixed_membership_population_has_distinct_absence_states(self):
        latest = self._latest(
            [
                {
                    "symbol": "LIVE",
                    "investability_status": "PASS",
                    "tradability_status": "NEAR_PASS",
                }
            ]
        )
        previous = self._previous(["LIVE", "STALE", "REMOVED"])
        current_universe = {"LIVE", "STALE"}

        events = compute_alert_transitions(latest, previous, current_universe)
        states = {row["symbol"]: row["event"] for row in events}

        self.assertNotIn("LIVE", states)
        self.assertEqual(states["STALE"], "DATA_UNAVAILABLE")
        self.assertEqual(states["REMOVED"], "OUT_OF_UNIVERSE")

    def test_current_failure_is_not_conflated_with_absence(self):
        latest = self._latest(
            [
                {
                    "symbol": "FAILED",
                    "investability_status": "FAIL",
                    "tradability_status": "FAIL",
                }
            ]
        )
        previous = self._previous(["FAILED", "STALE", "REMOVED"])
        current_universe = {"FAILED", "STALE"}

        events = compute_alert_transitions(latest, previous, current_universe)
        states = {row["symbol"]: row["event"] for row in events}

        self.assertEqual(states["FAILED"], "INVALIDATED")
        self.assertEqual(states["STALE"], "DATA_UNAVAILABLE")
        self.assertEqual(states["REMOVED"], "OUT_OF_UNIVERSE")

    def test_lifecycle_mixed_population_preserves_three_way_semantics(self):
        history = pd.DataFrame(
            [
                {"symbol": "FAILED", "event": "NEW_WATCH", "as_of_date": "2026-09-10"},
                {"symbol": "STALE", "event": "NEW_WATCH", "as_of_date": "2026-09-10"},
                {"symbol": "REMOVED", "event": "NEW_WATCH", "as_of_date": "2026-09-10"},
            ]
        )
        latest = self._latest(
            [
                {
                    "symbol": "FAILED",
                    "investability_status": "FAIL",
                    "tradability_status": "FAIL",
                }
            ]
        )
        current_universe = {"FAILED", "STALE"}

        lifecycle = build_candidate_lifecycle(history, latest, current_universe)
        states = dict(zip(lifecycle["symbol"], lifecycle["current_state"]))

        self.assertEqual(states["FAILED"], "INVALIDATED")
        self.assertEqual(states["STALE"], "DATA_UNAVAILABLE")
        self.assertEqual(states["REMOVED"], "OUT_OF_UNIVERSE")

    def test_universe_reentry_is_driven_by_current_row(self):
        history = pd.DataFrame(
            [
                {"symbol": "RETURN", "event": "OUT_OF_UNIVERSE", "as_of_date": "2026-09-10"},
            ]
        )
        latest = self._latest(
            [
                {
                    "symbol": "RETURN",
                    "investability_status": "PASS",
                    "tradability_status": "PASS",
                }
            ]
        )

        lifecycle = build_candidate_lifecycle(history, latest, {"RETURN"})
        state = lifecycle.loc[lifecycle["symbol"] == "RETURN", "current_state"].iloc[0]
        self.assertEqual(state, "ACTIONABLE")

    def test_latest_outside_current_universe_fails_closed(self):
        latest = self._latest(
            [
                {
                    "symbol": "GHOST",
                    "investability_status": "PASS",
                    "tradability_status": "PASS",
                }
            ]
        )
        with self.assertRaises(ValueError):
            compute_alert_transitions(latest, pd.DataFrame(), {"OTHER"})


if __name__ == "__main__":
    unittest.main()
