import unittest

import pandas as pd

from run_exit_candidate003_development import stop_timing_summary


class TestExitCandidate003Reporting(unittest.TestCase):
    def test_stop_timing_aggregates_gap_and_touch_reasons(self):
        rows = pd.DataFrame([
            {"exit_reason": "risk_stop_gap", "holding_days": 1},
            {"exit_reason": "risk_stop_touch", "holding_days": 5},
            {"exit_reason": "trend_exit", "holding_days": 11},
        ])

        summary = stop_timing_summary(rows, "EXIT-CAND-003")

        self.assertEqual(summary["stop_events"], 2)
        self.assertEqual(summary["median_stop_day"], 3.0)
        self.assertAlmostEqual(summary["fraction_all_events_stopped_by_day_1"], 1 / 3)
        self.assertAlmostEqual(summary["fraction_all_events_stopped_by_day_3"], 1 / 3)
        self.assertAlmostEqual(summary["fraction_all_events_stopped_by_day_5"], 2 / 3)
        self.assertAlmostEqual(summary["fraction_all_events_stopped_by_day_10"], 2 / 3)

    def test_current_reporting_keeps_legacy_stop_loss_reason(self):
        rows = pd.DataFrame([
            {"exit_reason": "stop_loss", "holding_days": 2},
            {"exit_reason": "trend_exit", "holding_days": 4},
        ])

        summary = stop_timing_summary(rows, "CURRENT")

        self.assertEqual(summary["stop_events"], 1)
        self.assertEqual(summary["median_stop_day"], 2.0)
        self.assertAlmostEqual(summary["fraction_all_events_stopped_by_day_1"], 0.0)


if __name__ == "__main__":
    unittest.main()
