import unittest

import numpy as np
import pandas as pd

from canonical_ema import EMA_PERIODS, compute_canonical_ema_features


class CanonicalEmaTests(unittest.TestCase):
    def test_uses_adj_close_not_raw_close(self):
        n = 300
        adj = pd.Series(np.linspace(10.0, 40.0, n))
        raw = adj.copy()
        raw.iloc[:150] = raw.iloc[:150] / 2.0  # synthetic split discontinuity
        frame = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=n, freq="D"),
            "close_raw": raw,
            "close_adj": adj,
        })

        got = compute_canonical_ema_features(frame)
        for period in EMA_PERIODS:
            expected = adj.ewm(span=period, adjust=False).mean()
            np.testing.assert_allclose(got[f"ema{period}"], expected, rtol=0, atol=1e-12)

        raw_ema200 = raw.ewm(span=200, adjust=False).mean()
        self.assertFalse(np.allclose(got["ema200"], raw_ema200))

    def test_stack_uses_adj_close(self):
        frame = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=300, freq="D"),
            "close_raw": np.linspace(1000.0, 1.0, 300),
            "close_adj": np.linspace(1.0, 1000.0, 300),
        })
        got = compute_canonical_ema_features(frame)
        self.assertTrue(bool(got.iloc[-1]["ema_stack_aligned"]))

    def test_missing_adj_close_fails_closed(self):
        with self.assertRaises(ValueError):
            compute_canonical_ema_features(pd.DataFrame({"date": ["2026-01-01"], "close_raw": [10.0]}))

    def test_non_numeric_adj_close_fails_closed(self):
        frame = pd.DataFrame({"date": ["2026-01-01"], "close_adj": ["bad"]})
        with self.assertRaises(ValueError):
            compute_canonical_ema_features(frame)


if __name__ == "__main__":
    unittest.main()
