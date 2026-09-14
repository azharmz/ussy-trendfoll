import io
import unittest

import numpy as np
import pandas as pd

from research_history import (
    apply_canonical_research_ema,
    evaluation_rows,
    load_research_history,
)


class FakeBody:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self):
        return self.payload


class FakeS3:
    def __init__(self, objects):
        self.objects = objects

    def get_object(self, Bucket, Key):
        return {"Body": FakeBody(self.objects[Key])}


def parquet_bytes(frame: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    frame.to_parquet(buf, index=False)
    return buf.getvalue()


class ResearchHistoryTests(unittest.TestCase):
    def setUp(self):
        dates = pd.bdate_range("2024-01-02", periods=510)
        base = np.arange(510, dtype=float) + 100.0
        self.history = pd.DataFrame({
            "date": dates,
            "security_id": "sec-1",
            "ticker": "AAA",
            "open": base,
            "high": base + 2,
            "low": base - 2,
            "close": base + 0.5,
            "adj_close": base + 0.25,
            "volume": np.arange(510) + 1000,
        })
        self.ready = self.history.tail(300).copy()
        self.ready_manifest = {"snapshot_date": str(dates[-1].date())}
        self.s3 = FakeS3({"backtest/ohlcv/sec-1.parquet": parquet_bytes(self.history)})

    def test_preroll_is_context_only_and_future_is_trimmed(self):
        start = self.history["date"].iloc[504]
        end = self.history["date"].iloc[507]
        loaded, report = load_research_history(
            ["sec-1"],
            evaluation_start=start,
            evaluation_end=end,
            min_preroll_bars=500,
            ready=self.ready,
            ready_manifest=self.ready_manifest,
            s3=self.s3,
            bucket="test",
        )
        self.assertEqual(508, len(loaded))
        eligible = loaded.loc[loaded["research_eligible"]]
        self.assertEqual(list(self.history["date"].iloc[504:508]), list(eligible["date"]))
        self.assertEqual(4, report.eligible_rows)
        self.assertLessEqual(loaded["date"].max(), end)

    def test_outside_ready_universe_is_rejected(self):
        with self.assertRaises(ValueError):
            load_research_history(
                ["other"],
                ready=self.ready,
                ready_manifest=self.ready_manifest,
                s3=self.s3,
                bucket="test",
            )

    def test_canonical_ema_uses_adjusted_close(self):
        frame = pd.DataFrame({
            "symbol": ["AAA"] * 4,
            "date": pd.bdate_range("2026-01-01", periods=4),
            "close_raw": [10.0, 20.0, 30.0, 40.0],
            "close_adj": [10.0, 10.0, 10.0, 10.0],
        })
        out = apply_canonical_research_ema(frame)
        self.assertTrue((out[["ema20", "ema50", "ema150", "ema200"]] == 10.0).all().all())
        self.assertFalse(out["ema_stack_aligned"].any())

    def test_evaluation_rows_requires_governed_mask(self):
        with self.assertRaises(ValueError):
            evaluation_rows(pd.DataFrame({"x": [1]}))


if __name__ == "__main__":
    unittest.main()
