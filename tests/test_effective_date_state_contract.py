"""Contract tests for effective-date state semantics."""
import unittest

import pandas as pd

from alert_state import compute_alert_transitions
from candidate_lifecycle import build_candidate_lifecycle


def frame(rows):
    return pd.DataFrame(rows)


class EffectiveDateStateContractTests(unittest.TestCase):
    def test_current_row_with_failed_investability_is_invalidated(self):
        previous = frame([{"symbol": "AAA", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "AAA", "date": "2026-09-14", "investability_status": "FAIL", "tradability_status": "FAIL", "close_raw": 8.0}])
        events = compute_alert_transitions(latest, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "INVALIDATED")

    def test_missing_current_row_is_data_unavailable_not_signal_invalidation(self):
        previous = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "FAIL", "close_raw": 10.0}])
        events = compute_alert_transitions(latest, previous)
        bbb = [e for e in events if e["symbol"] == "BBB"]
        self.assertEqual(len(bbb), 1)
        self.assertEqual(bbb[0]["event"], "DATA_UNAVAILABLE")
        self.assertEqual(bbb[0]["current_state"], "DATA_UNAVAILABLE")

    def test_older_row_is_not_present_in_common_date_snapshot(self):
        features = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "FAIL"},
            {"symbol": "BBB", "date": "2026-09-11", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        as_of_date = features["date"].max()
        latest = features[features["date"] == as_of_date].copy()
        self.assertEqual(set(latest["symbol"]), {"AAA"})

    def test_missing_current_symbol_cannot_become_actionable(self):
        previous = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "PASS", "close_raw": 10.0}])
        events = compute_alert_transitions(latest, previous)
        bbb = [e for e in events if e["symbol"] == "BBB"]
        self.assertTrue(bbb)
        self.assertTrue(all(e["event"] != "ACTIONABLE" for e in bbb))

    def test_current_data_restoration_resumes_normal_evaluation(self):
        previous = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "BBB", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS", "close_raw": 12.0}])
        events = compute_alert_transitions(latest, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ACTIONABLE")
        self.assertEqual(events[0]["as_of_date"], "2026-09-15")

    def test_lifecycle_missing_current_row_is_data_unavailable(self):
        history = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "FAIL"}])
        lifecycle = build_candidate_lifecycle(history, latest)
        bbb = lifecycle[lifecycle["symbol"] == "BBB"].iloc[0]
        self.assertEqual(bbb["current_state"], "DATA_UNAVAILABLE")
        self.assertFalse(bool(bbb["currently_monitored"]))
        self.assertFalse(bool(bbb["currently_actionable"]))

    def test_lifecycle_present_failed_row_is_invalidated(self):
        history = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "BBB", "date": "2026-09-14", "investability_status": "FAIL", "tradability_status": "FAIL"}])
        lifecycle = build_candidate_lifecycle(history, latest)
        bbb = lifecycle.iloc[0]
        self.assertEqual(bbb["current_state"], "INVALIDATED")
        self.assertFalse(bool(bbb["currently_monitored"]))

    def test_lifecycle_restored_current_row_resumes_actionable(self):
        history = frame([{"symbol": "BBB", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"}])
        latest = frame([{"symbol": "BBB", "date": "2026-09-15", "investability_status": "PASS", "tradability_status": "PASS"}])
        lifecycle = build_candidate_lifecycle(history, latest)
        bbb = lifecycle.iloc[0]
        self.assertEqual(bbb["current_state"], "ACTIONABLE")
        self.assertTrue(bool(bbb["currently_monitored"]))
        self.assertTrue(bool(bbb["currently_actionable"]))


if __name__ == "__main__":
    unittest.main()
