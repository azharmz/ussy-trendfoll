import unittest

import numpy as np
import pandas as pd

from liquidity_split_adjustment import compute_split_adjusted_avg_volume, classify_liquidity


def frame(volumes, splits=None, known=None):
    n = len(volumes)
    d = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n, freq="B"),
        "volume_raw": volumes,
        "stock_splits": splits if splits is not None else [0.0] * n,
    })
    if known is not None:
        d["split_factor_known"] = known
    return d


class SplitAdjustedLiquidityContractTests(unittest.TestCase):
    def test_no_split_identity(self):
        d = frame([250_000.0] * 60)
        got = compute_split_adjusted_avg_volume(d)
        raw = d.volume_raw.rolling(50, min_periods=20).mean()
        pd.testing.assert_series_equal(got.reset_index(drop=True), raw.reset_index(drop=True), check_names=False)

    def test_two_for_one_normalizes_pre_split_volume(self):
        d = frame([100_000.0] * 25 + [200_000.0] * 25, [0.0] * 25 + [2.0] + [0.0] * 24)
        got = compute_split_adjusted_avg_volume(d)
        self.assertAlmostEqual(got.iloc[-1], 200_000.0)

    def test_reverse_split_normalizes_pre_split_volume(self):
        d = frame([1_000_000.0] * 25 + [100_000.0] * 25, [0.0] * 25 + [0.1] + [0.0] * 24)
        got = compute_split_adjusted_avg_volume(d)
        self.assertAlmostEqual(got.iloc[-1], 100_000.0)

    def test_multiple_splits_compose(self):
        volumes = [100_000.0] * 10 + [200_000.0] * 10 + [400_000.0] * 10
        splits = [0.0] * 10 + [2.0] + [0.0] * 9 + [2.0] + [0.0] * 9
        got = compute_split_adjusted_avg_volume(frame(volumes, splits), window=30, min_periods=20)
        self.assertAlmostEqual(got.iloc[-1], 400_000.0)

    def test_split_outside_window_does_not_change_window(self):
        volumes = [100_000.0] * 10 + [200_000.0] * 60
        splits = [0.0] * 10 + [2.0] + [0.0] * 59
        got = compute_split_adjusted_avg_volume(frame(volumes, splits))
        self.assertAlmostEqual(got.iloc[-1], 200_000.0)

    def test_min_periods_is_twenty(self):
        got = compute_split_adjusted_avg_volume(frame([300_000.0] * 20))
        self.assertTrue(pd.isna(got.iloc[18]))
        self.assertEqual(got.iloc[19], 300_000.0)

    def test_future_split_does_not_leak_into_historical_asof(self):
        d = frame([100_000.0] * 25 + [200_000.0] * 5, [0.0] * 25 + [2.0] + [0.0] * 4)
        got = compute_split_adjusted_avg_volume(d)
        self.assertAlmostEqual(got.iloc[24], 100_000.0)
        self.assertAlmostEqual(got.iloc[25], 200_000.0)

    def test_unknown_split_factor_fails_closed(self):
        splits = [0.0] * 20 + [2.0] + [0.0] * 9
        known = [True] * 20 + [False] + [True] * 9
        got = compute_split_adjusted_avg_volume(frame([100_000.0] * 30, splits, known))
        self.assertTrue(pd.isna(got.iloc[-1]))

    def test_unaffected_security_status_invariant(self):
        d = frame([310_000.0] * 55)
        got = compute_split_adjusted_avg_volume(d)
        raw = d.volume_raw.rolling(50, min_periods=20).mean()
        self.assertEqual(classify_liquidity(got).iloc[-1], classify_liquidity(raw).iloc[-1])
        self.assertEqual(classify_liquidity(got).iloc[-1], "PASS")

    def test_split_removes_mechanical_threshold_discontinuity(self):
        # Economic activity is constant at 260k shares on post-split basis.
        d = frame([130_000.0] * 25 + [260_000.0] * 25, [0.0] * 25 + [2.0] + [0.0] * 24)
        raw = d.volume_raw.rolling(50, min_periods=20).mean()
        corrected = compute_split_adjusted_avg_volume(d)
        self.assertEqual(classify_liquidity(raw).iloc[-1], "FAIL")
        self.assertEqual(classify_liquidity(corrected).iloc[-1], "NEAR_PASS")
        self.assertAlmostEqual(corrected.iloc[-1], 260_000.0)


if __name__ == "__main__":
    unittest.main()
