import unittest

import numpy as np
import pandas as pd

from atr_split_adjustment import compute_split_adjusted_atr


def frame(close, splits=None, known=None):
    close = np.asarray(close, dtype=float)
    n = len(close)
    d = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n, freq="B"),
        "high_raw": close + np.maximum(close * 0.01, 0.01),
        "low_raw": close - np.maximum(close * 0.01, 0.01),
        "close_raw": close,
        "stock_splits": splits if splits is not None else [0.0] * n,
    })
    if known is not None:
        d["split_factor_known"] = known
    return d


def legacy_atr(d, period=14):
    prev = d.close_raw.shift(1)
    tr = pd.concat([
        d.high_raw - d.low_raw,
        (d.high_raw - prev).abs(),
        (d.low_raw - prev).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()


class SplitAdjustedATRContractTests(unittest.TestCase):
    def test_no_split_identity(self):
        d = frame(np.linspace(100, 110, 40))
        got = compute_split_adjusted_atr(d)
        pd.testing.assert_series_equal(got.reset_index(drop=True), legacy_atr(d).reset_index(drop=True), check_names=False)

    def test_two_for_one_removes_mechanical_gap(self):
        # Constant economic price around 100 pre-split / 50 post-split.
        close = [100.0] * 20 + [50.0] * 20
        splits = [0.0] * 20 + [2.0] + [0.0] * 19
        d = frame(close, splits)
        raw = legacy_atr(d)
        corrected = compute_split_adjusted_atr(d)
        self.assertGreater(raw.iloc[20], corrected.iloc[20] * 3)
        self.assertAlmostEqual(corrected.iloc[20], 1.0, places=8)

    def test_reverse_split_removes_mechanical_gap(self):
        close = [10.0] * 20 + [100.0] * 20
        splits = [0.0] * 20 + [0.1] + [0.0] * 19
        d = frame(close, splits)
        raw = legacy_atr(d)
        corrected = compute_split_adjusted_atr(d)
        self.assertGreater(raw.iloc[20], corrected.iloc[20] * 3)
        self.assertAlmostEqual(corrected.iloc[20], 2.0, places=8)

    def test_future_split_does_not_change_historical_atr(self):
        close = [100.0] * 20 + [50.0] * 5
        splits = [0.0] * 20 + [2.0] + [0.0] * 4
        d = frame(close, splits)
        got = compute_split_adjusted_atr(d)
        prefix = compute_split_adjusted_atr(d.iloc[:20].copy())
        self.assertAlmostEqual(got.iloc[19], prefix.iloc[19])

    def test_unknown_split_factor_fails_closed(self):
        close = [100.0] * 20 + [50.0] * 5
        splits = [0.0] * 20 + [2.0] + [0.0] * 4
        known = [True] * 20 + [False] + [True] * 4
        got = compute_split_adjusted_atr(frame(close, splits, known))
        self.assertTrue(pd.isna(got.iloc[20]))
        self.assertTrue(pd.isna(got.iloc[-1]))

    def test_same_day_bar_not_double_adjusted(self):
        close = [100.0] * 20 + [50.0]
        splits = [0.0] * 20 + [2.0]
        got = compute_split_adjusted_atr(frame(close, splits))
        # post-split same-day range is 1.0; pre-split history normalizes to 50
        self.assertAlmostEqual(got.iloc[-1], 1.0, places=8)


if __name__ == "__main__":
    unittest.main()
