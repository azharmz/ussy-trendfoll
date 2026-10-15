"""Fail-closed code-path guard for EXIT-CAND-003 Shadow v2.

This wrapper narrows the runner's intended Supabase client surface. It is NOT a
credential-level security boundary: a service-role key remains privileged if
used outside this wrapper. Do not claim database-enforced isolation from this
module alone.
"""
from __future__ import annotations

from typing import Any

READ_TABLES = frozenset({
    "positions",
    "exit_candidate003_shadow",
    "exit_candidate003_shadow_sessions",
})
WRITE_METHODS_BY_TABLE = {
    "exit_candidate003_shadow": frozenset({"insert", "update"}),
    "exit_candidate003_shadow_sessions": frozenset({"insert"}),
}


class ShadowV2DatabaseGuardError(RuntimeError):
    """Raised when a runner query exceeds the explicit Shadow v2 allow-list."""


class _GuardedQuery:
    def __init__(self, query: Any, table_name: str):
        self._query = query
        self._table_name = table_name

    def __getattr__(self, name: str):
        attr = getattr(self._query, name)
        if name in {"insert", "update", "upsert", "delete"}:
            allowed = WRITE_METHODS_BY_TABLE.get(self._table_name, frozenset())
            if name not in allowed:
                raise ShadowV2DatabaseGuardError(
                    f"Shadow v2 blocked {name} on table {self._table_name!r}"
                )

            def guarded_mutation(*args, **kwargs):
                return _GuardedQuery(attr(*args, **kwargs), self._table_name)

            return guarded_mutation
        if callable(attr):
            def chained(*args, **kwargs):
                result = attr(*args, **kwargs)
                # Query builder methods return the query object; preserve the guard.
                if result is self._query:
                    return self
                return result
            return chained
        return attr


class ShadowV2DatabaseGuard:
    """Expose only allow-listed tables and mutation methods to the v2 runner."""

    def __init__(self, client: Any):
        self._client = client

    def table(self, table_name: str):
        if table_name not in READ_TABLES:
            raise ShadowV2DatabaseGuardError(
                f"Shadow v2 blocked access to table {table_name!r}"
            )
        return _GuardedQuery(self._client.table(table_name), table_name)


def guard_shadow_v2_client(client: Any) -> ShadowV2DatabaseGuard:
    """Wrap a Supabase client before passing it to any Shadow v2 code."""
    return ShadowV2DatabaseGuard(client)
