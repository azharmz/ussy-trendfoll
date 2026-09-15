import unittest
from types import SimpleNamespace

import pandas as pd
import exit_candidate003_shadow as shadow


class _FakeQuery:
    def __init__(self, client, table):
        self.client, self.table = client, table
        self.filters = {}
        self.payload = None
        self.mode = None

    def select(self, *_): self.mode = "select"; return self
    def eq(self, key, value): self.filters[key] = value; return self
    def insert(self, payload): self.mode = "insert"; self.payload = dict(payload); return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table, [])
        if self.mode == "select":
            data = [r.copy() for r in rows if all(str(r.get(k)) == str(v) for k, v in self.filters.items())]
            return SimpleNamespace(data=data)
        if self.mode == "insert":
            row = self.payload.copy()
            row.setdefault("id", len(rows) + 1)
            rows.append(row)
            return SimpleNamespace(data=[row.copy()])
        raise AssertionError("unsupported fake query")


class _FakeClient:
    def __init__(self): self.rows = {}
    def table(self, name): return _FakeQuery(self, name)


def _row(open_=105.0, high=110.0, low=100.0, close=108.0, ema20=100.0, chand=106.0):
    return pd.Series({
        "open_raw": open_, "high_raw": high, "low_raw": low, "close_raw": close,
        "ema20": ema20, "shadow_hh22": 112.0, "shadow_wilder_atr22": 2.0,
        "shadow_chandelier": chand,
    })


def _state(operative=102.0):
    return {
        "id": 7, "position_id": 11, "symbol": "X", "shadow_entry_date": "2026-01-05",
        "shadow_entry_price": 104.0, "initial_stop": 100.0, "operative_stop": operative,
    }


class TestExitCandidate003Shadow(unittest.TestCase):
    def setUp(self):
        self.dates = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"])
        self.today = pd.Timestamp("2026-01-07")

    def test_shadow_contract_is_frozen(self):
        self.assertEqual(shadow.SHADOW_CONTRACT_VERSION, "exit-cand-003-shadow-v1")
        self.assertEqual(shadow.INITIAL_ATR_MULT, 2.0)
        self.assertEqual(shadow.CHAND_PERIOD, 22)
        self.assertEqual(shadow.CHAND_ATR_MULT, 3.0)
        self.assertEqual(shadow.MAX_HOLDING_DAYS, 45)

    def test_chandelier_uses_wilder22_and_hh22(self):
        rows = []
        for i in range(30):
            close = 100.0 + i
            rows.append({"symbol": "X", "date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
                         "open_raw": close - .5, "high_raw": close + 1, "low_raw": close - 1,
                         "close_raw": close})
        out = shadow.add_frozen_shadow_features(pd.DataFrame(rows))
        self.assertTrue(out["shadow_chandelier"].iloc[:21].isna().all())
        self.assertTrue(out["shadow_chandelier"].iloc[21:].notna().all())
        expected = out["shadow_hh22"] - 3.0 * out["shadow_wilder_atr22"]
        pd.testing.assert_series_equal(out["shadow_chandelier"], expected, check_names=False)

    def test_trading_day_counter_excludes_entry_date(self):
        self.assertEqual(shadow._trading_days_between("2026-01-05", "2026-01-07", self.dates), 2)

    def test_gap_has_priority_and_fills_open(self):
        update, ev = shadow._evaluate_session(_state(102), _row(open_=99, high=106, low=98, close=104), self.today, self.dates)
        self.assertEqual(ev["hypothetical_exit_reason"], "risk_stop_gap")
        self.assertEqual(ev["hypothetical_exit_price"], 99.0)
        self.assertEqual(update["status"], "exited")

    def test_touch_without_gap_fills_operative_stop(self):
        _, ev = shadow._evaluate_session(_state(102), _row(open_=104, high=108, low=101, close=106), self.today, self.dates)
        self.assertEqual(ev["hypothetical_exit_reason"], "risk_stop_touch")
        self.assertEqual(ev["hypothetical_exit_price"], 102.0)

    def test_survivor_records_current_and_next_stop_without_same_day_lookahead(self):
        update, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108, chand=106), self.today, self.dates)
        self.assertIsNone(ev["hypothetical_exit_reason"])
        self.assertEqual(ev["operative_stop_before"], 102.0)
        self.assertEqual(ev["shadow_chandelier"], 106.0)
        self.assertEqual(ev["next_operative_stop"], 106.0)
        self.assertEqual(update["operative_stop"], 106.0)
        self.assertTrue(ev["chandelier_arms_next_session"])

    def test_identical_session_replay_is_idempotent(self):
        client = _FakeClient()
        _, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108), self.today, self.dates)
        self.assertEqual(shadow._persist_session_evidence(client, ev), "inserted")
        self.assertEqual(shadow._persist_session_evidence(client, ev), "replay_identical")
        self.assertEqual(len(client.rows[shadow.SESSION_LEDGER_TABLE]), 1)

    def test_divergent_duplicate_evidence_is_rejected(self):
        client = _FakeClient()
        _, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108), self.today, self.dates)
        shadow._persist_session_evidence(client, ev)
        divergent = dict(ev)
        divergent["close_raw"] = 107.0
        with self.assertRaisesRegex(RuntimeError, "divergent CAND-003 session evidence"):
            shadow._persist_session_evidence(client, divergent)

    def test_production_comparison_is_not_input_to_shadow_decision(self):
        update1, ev1 = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108), self.today, self.dates)
        update2, ev2 = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108), self.today, self.dates)
        ev1.update({"production_status": "open", "production_exit_date": None, "production_exit_price": None})
        ev2.update({"production_status": "closed", "production_exit_date": "2026-01-07", "production_exit_price": 50.0})
        self.assertEqual(update1, update2)
        self.assertEqual(ev1["hypothetical_exit_reason"], ev2["hypothetical_exit_reason"])
        self.assertEqual(ev1["next_operative_stop"], ev2["next_operative_stop"])


if __name__ == "__main__":
    unittest.main()
