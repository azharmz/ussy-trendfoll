import itertools
import unittest

import numpy as np
import pandas as pd

from decision_layer import compute_investability, compute_tradability
from hard_filter import compute_hard_filter


STATUSES = ("FAIL", "NEAR_PASS", "PASS")


class InvestabilityContractTests(unittest.TestCase):
    def test_complete_non_compensatory_truth_table(self):
        rows = []
        expected = []
        rank = {"FAIL": 0, "NEAR_PASS": 1, "PASS": 2}
        for combo in itertools.product(STATUSES, repeat=4):
            rows.append(dict(zip(
                ["trend_status", "liquidity_status", "rs_status", "price_status"], combo
            )))
            minimum = min(rank[s] for s in combo)
            expected.append("FAIL" if minimum == 0 else "NEAR_PASS" if minimum == 1 else "PASS")

        out = compute_investability(pd.DataFrame(rows))
        self.assertEqual(out["investability_status"].tolist(), expected)
        self.assertEqual(len(out), 81)

    def test_raw_nan_inputs_fail_closed_before_investability(self):
        raw = pd.DataFrame([{
            "ema_stack_aligned": np.nan,
            "stage": np.nan,
            "avg_volume_50d": np.nan,
            "rs_spy": np.nan,
            "close_raw": np.nan,
            "market_regime": np.nan,
        }])
        filtered = compute_hard_filter(raw)
        self.assertEqual(filtered.loc[0, "trend_status"], "FAIL")
        self.assertEqual(filtered.loc[0, "liquidity_status"], "FAIL")
        self.assertEqual(filtered.loc[0, "rs_status"], "FAIL")
        self.assertEqual(filtered.loc[0, "price_status"], "FAIL")
        self.assertEqual(filtered.loc[0, "regime_status"], "FAIL")
        self.assertEqual(filtered.loc[0, "hard_filter_status"], "FAIL")
        decided = compute_investability(filtered)
        self.assertEqual(decided.loc[0, "investability_status"], "FAIL")


class TradabilityContractTests(unittest.TestCase):
    @staticmethod
    def _frame(volume_percentile, tightness, close=101.0, prior_pivot=100.0):
        # Two rows are required because prev_pivot_high is shift(1) of pivot_high.
        return pd.DataFrame([
            {
                "symbol": "AAA", "date": "2026-01-01", "pivot_high": prior_pivot,
                "close_raw": 99.0, "breakout_volume_percentile": 0.0, "vcp_tightness": 0.0,
            },
            {
                "symbol": "AAA", "date": "2026-01-02", "pivot_high": 105.0,
                "close_raw": close, "breakout_volume_percentile": volume_percentile,
                "vcp_tightness": tightness,
            },
        ])

    def test_complete_boolean_truth_table(self):
        cases = [
            # breakout, volume, tight, expected
            (False, False, False, "FAIL"),
            (False, False, True, "FAIL"),
            (False, True, False, "FAIL"),
            (False, True, True, "FAIL"),
            (True, False, False, "NEAR_PASS"),
            (True, False, True, "NEAR_PASS"),
            (True, True, False, "NEAR_PASS"),
            (True, True, True, "PASS"),
        ]
        for breakout, volume, tight, expected in cases:
            with self.subTest(breakout=breakout, volume=volume, tight=tight):
                frame = self._frame(
                    90.0 if volume else 10.0,
                    70.0 if tight else 10.0,
                    close=101.0 if breakout else 99.0,
                )
                out = compute_tradability(frame).iloc[-1]
                self.assertEqual(bool(out["has_breakout"]), breakout)
                self.assertEqual(bool(out["has_volume_confirmation"]), volume)
                self.assertEqual(bool(out["has_tight_structure"]), tight)
                self.assertEqual(out["tradability_status"], expected)

    def test_missing_prior_pivot_fails_closed(self):
        frame = self._frame(90.0, 70.0, prior_pivot=np.nan)
        out = compute_tradability(frame).iloc[-1]
        self.assertFalse(bool(out["has_breakout"]))
        self.assertEqual(out["tradability_status"], "FAIL")

    def test_nan_confirmations_do_not_create_pass(self):
        frame = self._frame(np.nan, np.nan)
        out = compute_tradability(frame).iloc[-1]
        self.assertTrue(bool(out["has_breakout"]))
        self.assertFalse(bool(out["has_volume_confirmation"]))
        self.assertFalse(bool(out["has_tight_structure"]))
        self.assertEqual(out["tradability_status"], "NEAR_PASS")

    def test_breakout_uses_prior_pivot_not_current_pivot(self):
        frame = self._frame(90.0, 70.0, close=101.0, prior_pivot=100.0)
        frame.loc[1, "pivot_high"] = 200.0
        out = compute_tradability(frame).iloc[-1]
        self.assertEqual(out["prev_pivot_high"], 100.0)
        self.assertTrue(bool(out["has_breakout"]))


if __name__ == "__main__":
    unittest.main()
