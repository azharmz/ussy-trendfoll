from run_prob019_cctg_lineage_audit import extract_matches


def test_extract_matches_selects_cctg_by_security_id_or_ticker():
    payload = {
        "created_at": "2026-10-01T00:00:00Z",
        "snapshot_date": "2026-10-01",
        "force": True,
        "results": [
            {"security_id": "KYG1993R1184", "ticker": "OLD", "status": "uploaded", "rows": 900},
            {"security_id": "OTHER", "ticker": "CCTG", "status": "uploaded", "rows": 901},
            {"security_id": "OTHER2", "ticker": "OTHER", "status": "skipped"},
        ],
    }

    matches = extract_matches(payload, "history/manifests/bootstrap/2026-10-01/run-test.json")

    assert len(matches) == 2
    assert all(item["force"] is True for item in matches)
    assert {item["status"] for item in matches} == {"uploaded"}


def test_extract_matches_returns_empty_for_unrelated_manifest():
    payload = {"results": [{"security_id": "OTHER", "ticker": "OTHER", "status": "skipped"}]}
    assert extract_matches(payload, "unrelated.json") == []
