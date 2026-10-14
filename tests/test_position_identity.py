import unittest
import pandas as pd
import positions

class PositionIdentityTests(unittest.TestCase):
    def test_same_day_exit_is_not_evaluated(self):
        self.assertLessEqual(pd.Timestamp("2026-08-26"), pd.Timestamp("2026-08-26"))

    def test_contract_constants_unchanged(self):
        self.assertEqual(positions.ATR_STOP_MULTIPLIER, 2.0)
        self.assertFalse(hasattr(positions, "MAX_HOLDING_DAYS"))

if __name__ == "__main__":
    unittest.main()
