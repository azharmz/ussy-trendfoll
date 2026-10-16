import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_prob019_cctg_counterfactual import apply_counterfactual, recursive_ema


class CCTGCounterfactualTests(unittest.TestCase):
    def frame(self, dates, values):
        return pd.DataFrame({
            "date": pd.to_datetime(dates),
            "security_id": ["KYG1993R1184"] * len(dates),
            "ticker": ["CCTG"] * len(dates),
            "adj_close": values,
        })

    def test_counterfactual_changes_copy_only(self):
        current = self.frame(["2026-09-21", "2026-09-22", "2026-09-23"], [0.50, 0.5180, 0.52])
        recovery = self.frame(["2026-09-21", "2026-09-22", "2026-09-23"], [0.50, 0.5184, 0.52])
        corrected, evidence = apply_counterfactual(current, recovery)
        self.assertAlmostEqual(float(corrected.loc[corrected.date.eq(pd.Timestamp("2026-09-22")), "adj_close"].iloc[0]), 0.5184)
        self.assertAlmostEqual(float(current.loc[current.date.eq(pd.Timestamp("2026-09-22")), "adj_close"].iloc[0]), 0.5180)
        self.assertTrue(evidence["changed"])

    def test_duplicate_security_date_rejected(self):
        current = self.frame(["2026-09-22", "2026-09-22"], [0.5180, 0.5181])
        recovery = self.frame(["2026-09-22"], [0.5184])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            apply_counterfactual(current, recovery)

    def test_recursive_ema_has_expected_periods(self):
        result = recursive_ema(self.frame(["2026-09-21", "2026-09-22", "2026-09-23"], [0.50, 0.5184, 0.52]))
        self.assertEqual(set(result), {"ema20", "ema50", "ema150", "ema200"})
        self.assertTrue(all(np.isfinite(v) for v in result.values()))


if __name__ == "__main__":
    unittest.main()
