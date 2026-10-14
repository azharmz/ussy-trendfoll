import unittest
import pandas as pd

from run_diag003_exit_risk import path_row


class TestDiag003GapAwareFill(unittest.TestCase):
    def _history(self, exit_open, exit_low):
        return pd.DataFrame([
            {"date": pd.Timestamp("2026-10-01"), "open_raw": 100.0, "high_raw": 101.0,
             "low_raw": 99.0, "close_raw": 100.0, "atr14": 1.0, "ema20": 95.0},
            {"date": pd.Timestamp("2026-10-02"), "open_raw": 100.0, "high_raw": 101.0,
             "low_raw": 99.0, "close_raw": 100.0, "atr14": 1.0, "ema20": 95.0},
            {"date": pd.Timestamp("2026-10-05"), "open_raw": exit_open, "high_raw": 92.0,
             "low_raw": exit_low, "close_raw": 91.0, "atr14": 1.0, "ema20": 95.0},
        ])

    def test_gap_through_uses_open_not_stop(self):
        result = path_row(self._history(90.0, 89.0), {"symbol": "X", "t0_date": "2026-10-01"})
        self.assertEqual(result["exit_reason"], "stop_loss")
        self.assertEqual(result["stop_price"], 98.0)
        self.assertEqual(result["exit_price"], 90.0)
        self.assertAlmostEqual(result["realized_return"], -0.10)

    def test_intraday_touch_uses_stop(self):
        result = path_row(self._history(100.0, 97.0), {"symbol": "X", "t0_date": "2026-10-01"})
        self.assertEqual(result["exit_reason"], "stop_loss")
        self.assertEqual(result["exit_price"], 98.0)


if __name__ == "__main__":
    unittest.main()
