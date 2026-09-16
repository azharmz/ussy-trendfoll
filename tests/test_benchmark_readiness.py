import unittest
import pandas as pd

from benchmark_readiness import validate_spy_readiness


class BenchmarkReadinessContractTests(unittest.TestCase):
    def test_same_day_spy_is_ready(self):
        stock = pd.date_range("2026-09-10", periods=3, freq="B")
        spy = list(stock)
        result = validate_spy_readiness(stock, spy)
        self.assertTrue(result["spy_exact_as_of"])
        self.assertEqual(result["regime_source_date"], stock[-1])

    def test_r2_ahead_of_spy_fails_closed(self):
        stock = pd.date_range("2026-09-10", periods=3, freq="B")
        spy = stock[:-1]
        with self.assertRaisesRegex(RuntimeError, "exact-date row required by RS"):
            validate_spy_readiness(stock, spy)

    def test_spy_ahead_of_r2_is_benign(self):
        stock = pd.date_range("2026-09-10", periods=3, freq="B")
        spy = pd.date_range("2026-09-10", periods=4, freq="B")
        result = validate_spy_readiness(stock, spy)
        self.assertEqual(result["as_of_date"], stock[-1])
        self.assertEqual(result["regime_source_date"], stock[-1])
        self.assertGreater(result["spy_latest_date"], stock[-1])

    def test_future_spy_cannot_rescue_missing_exact_t0(self):
        stock = pd.to_datetime(["2026-09-14"])
        spy = pd.to_datetime(["2026-09-11", "2026-09-15"])
        with self.assertRaises(RuntimeError):
            validate_spy_readiness(stock, spy)

    def test_empty_spy_fails_closed(self):
        stock = pd.to_datetime(["2026-09-14"])
        with self.assertRaisesRegex(RuntimeError, "SPY unavailable"):
            validate_spy_readiness(stock, [])


if __name__ == "__main__":
    unittest.main()
