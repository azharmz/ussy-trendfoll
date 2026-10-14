"""Contract checks for the PROB-017 public dashboard consumer."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_uses_fail_closed_canonical_rpc_not_raw_positions_endpoint():
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert 'sbAllRpc("get_canonical_position_history")' in html
    assert 'sbAll("positions?' not in html
    assert "Never query public.positions directly" in html


def test_canonical_rpc_migration_validates_duplicate_and_stale_ledger_groups():
    sql = (ROOT / "sql" / "migrate_prob017_canonical_reader_rpc.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE OR REPLACE FUNCTION public.get_canonical_position_history()" in sql
    assert "resolved_count" in sql
    assert "valid_count" in sql
    assert "rejected stale reconciliation" in sql
    assert "GRANT EXECUTE ON FUNCTION public.get_canonical_position_history() TO anon, authenticated" in sql
