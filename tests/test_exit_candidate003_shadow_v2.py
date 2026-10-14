import unittest
from types import SimpleNamespace

import pandas as pd
import exit_candidate003_shadow_v2 as shadow


def _row(open_=105.0, high=110.0, low=100.0, close=108.0, ema20=100.0, chand=106.0):
    return pd.Series({"open_raw": open_, "high_raw": high, "low_raw": low, "close_raw": close,
                      "ema20": ema20, "shadow_hh22": 112.0, "shadow_wilder_atr22": 2.0,
                      "shadow_chandelier": chand})


def _state(operative=102.0):
    return {"id": 7, "position_id": 11, "symbol": "X", "shadow_entry_date": "2026-01-05",
            "shadow_entry_price": 104.0, "initial_stop": 100.0, "operative_stop": operative}


class _FakeQuery:
    def __init__(self, client, table):
        self.client, self.table = client, table
        self.filters = {}
        self.payload = None
        self.mode = None
    def select(self, *_): self.mode = "select"; return self
    def eq(self, key, value): self.filters[key] = value; return self
    def insert(self, payload): self.mode = "insert"; self.payload = payload; return self
    def execute(self):
        rows = self.client.rows.setdefault(self.table, [])
        if self.mode == "select":
            data = [r.copy() for r in rows if all(str(r.get(k)) == str(v) for k, v in self.filters.items())]
            return SimpleNamespace(data=data)
        if self.mode == "insert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            out = []
            for payload in payloads:
                row = dict(payload); row.setdefault("id", len(rows) + 1); rows.append(row); out.append(row.copy())
            return SimpleNamespace(data=out)
        raise AssertionError("unsupported fake query")


class _FakeClient:
    def __init__(self): self.rows = {}
    def table(self, name): return _FakeQuery(self, name)


class TestExitCandidate003ShadowV2(unittest.TestCase):
    def setUp(self):
        self.dates = pd.bdate_range("2026-01-05", periods=70)
        self.today = self.dates[-1]

    def test_contract_is_v2_and_has_no_time_cap_constant(self):
        self.assertEqual(shadow.SHADOW_CONTRACT_VERSION, "exit-cand-003-shadow-v2")
        self.assertFalse(hasattr(shadow, "MAX_HOLDING_DAYS"))

    def test_60_sessions_does_not_exit_due_to_time(self):
        s = _state(operative=90.0)
        s["initial_stop"] = 80.0
        s["shadow_entry_date"] = str(self.dates[0].date())
        update, ev = shadow._evaluate_session(s, _row(open_=105, high=110, low=100, close=108, ema20=100, chand=95),
                                              self.today, self.dates)
        self.assertIsNone(ev["hypothetical_exit_reason"])
        self.assertNotIn("status", update)
        self.assertEqual(update["days_observed"], 70)

    def test_gap_has_priority_and_fills_open(self):
        update, ev = shadow._evaluate_session(_state(102), _row(open_=99, high=106, low=98, close=104),
                                              pd.Timestamp("2026-01-07"), self.dates[:3])
        self.assertEqual(ev["hypothetical_exit_reason"], "risk_stop_gap")
        self.assertEqual(ev["hypothetical_exit_price"], 99.0)
        self.assertEqual(update["status"], "exited")

    def test_touch_without_gap_fills_operative_stop(self):
        _, ev = shadow._evaluate_session(_state(102), _row(open_=104, high=108, low=101, close=106),
                                         pd.Timestamp("2026-01-07"), self.dates[:3])
        self.assertEqual(ev["hypothetical_exit_reason"], "risk_stop_touch")
        self.assertEqual(ev["hypothetical_exit_price"], 102.0)

    def test_ema20_exit_at_close_when_no_stop(self):
        state = _state(90)
        state["initial_stop"] = 80.0
        _, ev = shadow._evaluate_session(state, _row(open_=104, high=108, low=85, close=99, ema20=100),
                                         pd.Timestamp("2026-01-07"), self.dates[:3])
        self.assertEqual(ev["hypothetical_exit_reason"], "trend_exit")
        self.assertEqual(ev["hypothetical_exit_price"], 99.0)

    def test_chandelier_arms_next_session_and_stop_never_decreases(self):
        update, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108, chand=106),
                                              pd.Timestamp("2026-01-07"), self.dates[:3])
        self.assertIsNone(ev["hypothetical_exit_reason"])
        self.assertEqual(ev["operative_stop_before"], 102.0)
        self.assertEqual(ev["next_operative_stop"], 106.0)
        self.assertEqual(update["operative_stop"], 106.0)

    def test_identical_session_replay_is_idempotent(self):
        client = _FakeClient()
        _, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108),
                                         pd.Timestamp("2026-01-07"), self.dates[:3])
        self.assertEqual(shadow._persist_session_evidence(client, ev), "inserted")
        self.assertEqual(shadow._persist_session_evidence(client, ev), "replay_identical")
        self.assertEqual(len(client.rows[shadow.SESSION_LEDGER_TABLE]), 1)

    def test_divergent_duplicate_evidence_fails_closed(self):
        client = _FakeClient()
        _, ev = shadow._evaluate_session(_state(102), _row(open_=105, high=110, low=103, close=108),
                                         pd.Timestamp("2026-01-07"), self.dates[:3])
        shadow._persist_session_evidence(client, ev)
        divergent = dict(ev); divergent["close_raw"] = 107.0
        with self.assertRaisesRegex(RuntimeError, "divergent CAND-003 session evidence"):
            shadow._persist_session_evidence(client, divergent)


if __name__ == "__main__":
    unittest.main()
