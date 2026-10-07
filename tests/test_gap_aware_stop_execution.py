import unittest
from types import SimpleNamespace

import pandas as pd

import positions


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.filters = {}
        self.mode = "select"
        self.payload = None

    def select(self, *_):
        self.mode = "select"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def update(self, payload):
        self.mode = "update"
        self.payload = payload
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])
        matched = [r for r in rows if all(str(r.get(k)) == str(v) for k, v in self.filters.items())]
        if self.mode == "select":
            return SimpleNamespace(data=[r.copy() for r in matched])
        if self.mode == "update":
            for row in matched:
                row.update(self.payload)
            return SimpleNamespace(data=[r.copy() for r in matched])
        raise AssertionError(f"Unsupported mode: {self.mode}")


class FakeClient:
    def __init__(self, positions_rows):
        self.tables = {"positions": [r.copy() for r in positions_rows]}

    def table(self, name):
        return FakeQuery(self, name)


def _position(stop=98.0):
    return {
        "id": 1, "symbol": "X", "entry_date": "2026-10-06",
        "entry_price": 100.0, "realistic_entry_price": 100.0,
        "stop_price": stop, "status": "active",
        "max_close_since_entry": 101.0, "min_close_since_entry": 99.0,
    }


class TestGapAwareStopExecution(unittest.TestCase):
    def test_gap_through_fills_observed_open(self):
        self.assertEqual(positions._resolve_stop_loss_fill(95.0, 94.0, 98.0), ("gap_open", 95.0))

    def test_intraday_touch_fills_stop(self):
        self.assertEqual(positions._resolve_stop_loss_fill(100.0, 97.0, 98.0), ("stop_touch", 98.0))

    def test_untouched_stop_returns_none(self):
        self.assertIsNone(positions._resolve_stop_loss_fill(100.0, 99.0, 98.0))

    def test_triggered_stop_with_missing_open_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "open_raw is missing"):
            positions._resolve_stop_loss_fill(None, 97.0, 98.0)

    def test_check_exits_persists_gap_open_but_preserves_stop_loss_status(self):
        client = FakeClient([_position()])
        latest = pd.DataFrame([{
            "symbol": "X", "open_raw": 95.0, "low_raw": 94.0,
            "close_raw": 96.0, "ema20": 90.0,
        }])
        exits = positions.check_exits(
            client, latest, "2026-10-07",
            ["2026-10-06", "2026-10-07"],
        )
        stored = client.tables["positions"][0]
        self.assertEqual(stored["status"], "stop_loss")
        self.assertEqual(stored["exit_price"], 95.0)
        self.assertEqual(exits[0]["stop_fill_type"], "gap_open")
        self.assertAlmostEqual(exits[0]["pnl_pct"], -5.0)

    def test_check_exits_keeps_stop_price_for_intraday_touch(self):
        client = FakeClient([_position()])
        latest = pd.DataFrame([{
            "symbol": "X", "open_raw": 100.0, "low_raw": 97.0,
            "close_raw": 99.0, "ema20": 90.0,
        }])
        exits = positions.check_exits(
            client, latest, "2026-10-07",
            ["2026-10-06", "2026-10-07"],
        )
        stored = client.tables["positions"][0]
        self.assertEqual(stored["status"], "stop_loss")
        self.assertEqual(stored["exit_price"], 98.0)
        self.assertEqual(exits[0]["stop_fill_type"], "stop_touch")


if __name__ == "__main__":
    unittest.main()
