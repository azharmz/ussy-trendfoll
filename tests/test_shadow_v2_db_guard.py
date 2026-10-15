import unittest

from shadow_v2_db_guard import (
    ShadowV2DatabaseGuardError,
    guard_shadow_v2_client,
)


class FakeQuery:
    def __init__(self, table):
        self.table_name = table
        self.calls = []

    def select(self, *args, **kwargs):
        self.calls.append(("select", args, kwargs))
        return self

    def eq(self, *args, **kwargs):
        self.calls.append(("eq", args, kwargs))
        return self

    def insert(self, *args, **kwargs):
        self.calls.append(("insert", args, kwargs))
        return self

    def update(self, *args, **kwargs):
        self.calls.append(("update", args, kwargs))
        return self

    def upsert(self, *args, **kwargs):
        self.calls.append(("upsert", args, kwargs))
        return self

    def delete(self, *args, **kwargs):
        self.calls.append(("delete", args, kwargs))
        return self

    def execute(self):
        self.calls.append(("execute", (), {}))
        return {"ok": True}


class FakeClient:
    def __init__(self):
        self.queries = []

    def table(self, name):
        query = FakeQuery(name)
        self.queries.append(query)
        return query


class TestShadowV2DatabaseGuard(unittest.TestCase):
    def setUp(self):
        self.raw = FakeClient()
        self.client = guard_shadow_v2_client(self.raw)

    def test_positions_are_readable(self):
        result = (self.client.table("positions").select("id,status")
                  .eq("status", "active").execute())
        self.assertEqual(result, {"ok": True})

    def test_positions_insert_is_blocked_before_execution(self):
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked insert"):
            self.client.table("positions").insert({"status": "closed"})
        self.assertEqual(self.raw.queries[0].calls, [])

    def test_positions_update_is_blocked(self):
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked update"):
            self.client.table("positions").update({"status": "closed"})
        self.assertEqual(self.raw.queries[0].calls, [])

    def test_unknown_table_is_blocked(self):
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked access"):
            self.client.table("alert_events")
        self.assertEqual(self.raw.queries, [])

    def test_shadow_table_insert_is_allowed(self):
        result = self.client.table("exit_candidate003_shadow").insert({"contract_version": "test"}).execute()
        self.assertEqual(result, {"ok": True})
        self.assertEqual([call[0] for call in self.raw.queries[0].calls], ["insert", "execute"])

    def test_shadow_session_insert_is_allowed_but_update_is_blocked(self):
        result = self.client.table("exit_candidate003_shadow_sessions").insert({"session_date": "2026-01-01"}).execute()
        self.assertEqual(result, {"ok": True})
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked update"):
            self.client.table("exit_candidate003_shadow_sessions").update({"close_raw": 1.0})

    def test_upsert_and_delete_are_blocked_even_on_shadow_tables(self):
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked upsert"):
            self.client.table("exit_candidate003_shadow").upsert({"id": 1})
        with self.assertRaisesRegex(ShadowV2DatabaseGuardError, "blocked delete"):
            self.client.table("exit_candidate003_shadow").delete()

    def test_guard_does_not_expose_raw_client(self):
        self.assertFalse(hasattr(self.client, "rpc"))
        self.assertFalse(hasattr(self.client, "auth"))


if __name__ == "__main__":
    unittest.main()
