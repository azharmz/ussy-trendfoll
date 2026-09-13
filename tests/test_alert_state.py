import unittest
import pandas as pd

from alert_state import compute_alert_transitions


def frame(rows):
    return pd.DataFrame(rows)


class AlertStateTests(unittest.TestCase):
    def test_new_watch_and_immediate_actionable(self):
        latest = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "NEAR_PASS", "tradability_status": "FAIL", "close_raw": 10},
            {"symbol": "BBB", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "PASS", "close_raw": 20},
        ])
        events = compute_alert_transitions(latest, pd.DataFrame())
        self.assertEqual([(e["event"], e["symbol"]) for e in events], [("ACTIONABLE", "BBB"), ("NEW_WATCH", "AAA")])

    def test_upgrade_to_actionable(self):
        previous = frame([
            {"symbol": "AAA", "date": "2026-09-13", "investability_status": "PASS", "tradability_status": "FAIL"},
        ])
        latest = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "PASS", "close_raw": 11},
        ])
        events = compute_alert_transitions(latest, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "ACTIONABLE")

    def test_lost_tradability(self):
        previous = frame([
            {"symbol": "AAA", "date": "2026-09-13", "investability_status": "PASS", "tradability_status": "PASS"},
        ])
        latest = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "PASS", "tradability_status": "FAIL", "close_raw": 9},
        ])
        events = compute_alert_transitions(latest, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "LOST_TRADABILITY")

    def test_invalidated_when_investability_fails(self):
        previous = frame([
            {"symbol": "AAA", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"},
        ])
        latest = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "FAIL", "tradability_status": "FAIL", "close_raw": 8},
        ])
        events = compute_alert_transitions(latest, previous)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "INVALIDATED")

    def test_unchanged_state_emits_nothing(self):
        previous = frame([
            {"symbol": "AAA", "date": "2026-09-13", "investability_status": "NEAR_PASS", "tradability_status": "FAIL"},
        ])
        latest = frame([
            {"symbol": "AAA", "date": "2026-09-14", "investability_status": "NEAR_PASS", "tradability_status": "FAIL", "close_raw": 10},
        ])
        self.assertEqual(compute_alert_transitions(latest, previous), [])


if __name__ == "__main__":
    unittest.main()
