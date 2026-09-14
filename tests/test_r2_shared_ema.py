import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from r2_shared_ema import apply_shared_ema_terminal


class SharedEmaTerminalTests(unittest.TestCase):
    def setUp(self):
        self.ready = pd.DataFrame({
            "date": pd.to_datetime(["2026-09-10", "2026-09-11", "2026-09-10", "2026-09-11"]),
            "security_id": ["s1", "s1", "s2", "s2"],
            "ticker": ["AAA", "AAA", "BBB", "BBB"],
            "adj_close": [99.0, 110.0, 49.0, 50.0],
        })
        self.features = pd.DataFrame({
            "symbol": ["AAA", "AAA", "BBB", "BBB"],
            "date": pd.to_datetime(["2026-09-10", "2026-09-11", "2026-09-10", "2026-09-11"]),
            "close_adj": [99.0, 110.0, 49.0, 50.0],
            "ema20": [1.0, 1.0, 1.0, 1.0],
            "ema50": [1.0, 1.0, 1.0, 1.0],
            "ema150": [1.0, 1.0, 1.0, 1.0],
            "ema200": [1.0, 1.0, 1.0, 1.0],
            "ema_stack_aligned": [False, False, False, False],
        })
        self.state = pd.DataFrame({
            "security_id": ["s1", "s2"],
            "ticker": ["AAA", "BBB"],
            "as_of_date": pd.to_datetime(["2026-09-11", "2026-09-11"]),
            "last_price": [110.0, 50.0],
            "ema20": [105.0, 55.0],
            "ema50": [100.0, 54.0],
            "ema150": [95.0, 53.0],
            "ema200": [90.0, 52.0],
        })
        self.ready_manifest = {"parquet_key": "production/ready/runs/x.parquet", "sha256": "readysha"}
        self.ema_manifest = {
            "source_ready_parquet_key": "production/ready/runs/x.parquet",
            "source_ready_sha256": "readysha",
            "equivalence": {"verified": 2},
            "parquet_key": "production/indicators/ema/runs/e.parquet",
        }

    def test_replaces_only_terminal_rows_and_uses_adjusted_price_stack(self):
        out, report = apply_shared_ema_terminal(
            self.features, self.ready, self.ready_manifest,
            state=self.state, ema_manifest=self.ema_manifest,
        )
        first_aaa = out[(out.symbol == "AAA") & (out.date == pd.Timestamp("2026-09-10"))].iloc[0]
        last_aaa = out[(out.symbol == "AAA") & (out.date == pd.Timestamp("2026-09-11"))].iloc[0]
        last_bbb = out[(out.symbol == "BBB") & (out.date == pd.Timestamp("2026-09-11"))].iloc[0]
        self.assertEqual(first_aaa.ema20, 1.0)
        self.assertEqual(last_aaa.ema20, 105.0)
        self.assertTrue(bool(last_aaa.ema_stack_aligned))
        self.assertFalse(bool(last_bbb.ema_stack_aligned))
        self.assertEqual(report["terminal_rows_replaced"], 2)
        self.assertTrue(report["source_ready_lineage_match"])

    def test_rejects_ready_lineage_mismatch(self):
        bad = dict(self.ema_manifest)
        bad["source_ready_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "not aligned"):
            apply_shared_ema_terminal(
                self.features, self.ready, self.ready_manifest,
                state=self.state, ema_manifest=bad,
            )

    def test_rejects_terminal_price_mismatch(self):
        bad_state = self.state.copy()
        bad_state.loc[bad_state.ticker == "AAA", "last_price"] = 111.0
        with self.assertRaisesRegex(ValueError, "last_price"):
            apply_shared_ema_terminal(
                self.features, self.ready, self.ready_manifest,
                state=bad_state, ema_manifest=self.ema_manifest,
            )


if __name__ == "__main__":
    unittest.main()
