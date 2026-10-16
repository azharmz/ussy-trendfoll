"""Credential-level, read-only boundary checks for EXIT-CAND-003 Shadow v2."""
from __future__ import annotations
import os
import sys
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import InsufficientPrivilege

EXPECTED_ROLE = "ussy_shadow_v2_runner"
SHADOW_TABLE = "public.exit_candidate003_shadow"
SESSION_TABLE = "public.exit_candidate003_shadow_sessions"
POSITIONS_TABLE = "public.positions"


def connect():
    url = os.environ.get("SHADOW_V2_DATABASE_URL")
    if not url:
        raise RuntimeError("Missing SHADOW_V2_DATABASE_URL")
    return psycopg.connect(url, row_factory=dict_row, connect_timeout=15)


def check_denied(sql: str, label: str) -> None:
    # Each denied statement runs in its own connection/transaction and is rolled back.
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    except InsufficientPrivilege:
        print(f"PASS denied: {label}")
        return
    raise RuntimeError(f"SECURITY FAILURE: operation was not denied: {label}")


def main() -> int:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT current_user AS current_user,
                          r.rolsuper, r.rolcreatedb, r.rolcreaterole, r.rolbypassrls, r.rolinherit
                   FROM pg_roles r WHERE r.rolname = current_user"""
            )
            role = cur.fetchone()
            if not role or role["current_user"] != EXPECTED_ROLE:
                raise RuntimeError(f"Wrong database role: expected {EXPECTED_ROLE}, got {role}")
            if any(role[k] for k in ("rolsuper", "rolcreatedb", "rolcreaterole", "rolbypassrls", "rolinherit")):
                raise RuntimeError(f"Role has unexpected elevated flags: {role}")
            cur.execute(
                """SELECT COALESCE(array_agg(parent.rolname), ARRAY[]::text[]) AS memberships
                   FROM pg_auth_members m
                   JOIN pg_roles member ON member.oid = m.member
                   JOIN pg_roles parent ON parent.oid = m.roleid
                   WHERE member.rolname = current_user"""
            )
            memberships = cur.fetchone()["memberships"]
            if memberships:
                raise RuntimeError(f"Runner has unexpected role memberships: {memberships}")

            cur.execute(
                """SELECT
                     has_table_privilege(current_user, %s, 'SELECT') AS positions_select,
                     has_table_privilege(current_user, %s, 'INSERT') AS positions_insert,
                     has_table_privilege(current_user, %s, 'UPDATE') AS positions_update,
                     has_table_privilege(current_user, %s, 'DELETE') AS positions_delete,
                     has_table_privilege(current_user, %s, 'TRUNCATE') AS positions_truncate,
                     has_table_privilege(current_user, %s, 'SELECT') AS shadow_select,
                     has_table_privilege(current_user, %s, 'INSERT') AS shadow_insert,
                     has_table_privilege(current_user, %s, 'UPDATE') AS shadow_update,
                     has_table_privilege(current_user, %s, 'DELETE') AS shadow_delete,
                     has_table_privilege(current_user, %s, 'INSERT') AS sessions_insert,
                     has_table_privilege(current_user, %s, 'UPDATE') AS sessions_update,
                     has_table_privilege(current_user, %s, 'DELETE') AS sessions_delete""",
                (POSITIONS_TABLE, POSITIONS_TABLE, POSITIONS_TABLE, POSITIONS_TABLE, POSITIONS_TABLE,
                 SHADOW_TABLE, SHADOW_TABLE, SHADOW_TABLE, SHADOW_TABLE,
                 SESSION_TABLE, SESSION_TABLE, SESSION_TABLE),
            )
            grants = cur.fetchone()
            expected = {
                "positions_select": True, "positions_insert": False, "positions_update": False,
                "positions_delete": False, "positions_truncate": False,
                "shadow_select": True, "shadow_insert": True, "shadow_update": True,
                "shadow_delete": False, "sessions_insert": True, "sessions_update": False,
                "sessions_delete": False,
            }
            if dict(grants) != expected:
                raise RuntimeError(f"Unexpected effective grants: {dict(grants)}")
            print(f"PASS authenticated as {EXPECTED_ROLE}; no elevated flags or memberships")
            print("PASS effective table grants match least-privilege contract")

            # Verify read access and RLS visibility without modifying any row.
            cur.execute("SELECT count(*) AS visible_positions FROM public.positions")
            visible_positions = cur.fetchone()["visible_positions"]
            cur.execute(
                "SELECT count(*) AS visible_v2 FROM public.exit_candidate003_shadow WHERE contract_version = %s",
                ("exit-cand-003-shadow-v2",),
            )
            visible_v2 = cur.fetchone()["visible_v2"]
            cur.execute(
                "SELECT count(*) AS visible_v2_sessions FROM public.exit_candidate003_shadow_sessions WHERE contract_version = %s",
                ("exit-cand-003-shadow-v2",),
            )
            visible_sessions = cur.fetchone()["visible_v2_sessions"]
            print(f"PASS SELECT/RLS reads: positions={visible_positions}, v2={visible_v2}, v2_sessions={visible_sessions}")

    check_denied("UPDATE public.positions SET status = status WHERE false", "UPDATE positions")
    check_denied("DELETE FROM public.positions WHERE false", "DELETE positions")
    check_denied("DELETE FROM public.exit_candidate003_shadow WHERE false", "DELETE Shadow rows")
    check_denied("UPDATE public.exit_candidate003_shadow_sessions SET contract_version = contract_version WHERE false",
                 "UPDATE Shadow sessions")
    print("PASS all credential-level negative checks; no data rows were changed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[shadow-v2-security] FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
