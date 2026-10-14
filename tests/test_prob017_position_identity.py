"""Tests for the PROB-017 reconciliation ledger contract."""

import pytest

import positions


def _row(position_id, symbol="ANF", entry_date="2026-08-26", status="trend_exit"):
    return {
        "id": position_id,
        "symbol": symbol,
        "entry_date": entry_date,
        "status": status,
    }


def _resolution(canonical_id=19, excluded_ids=None, status="resolved"):
    return {
        "symbol": "ANF",
        "entry_date": "2026-08-26",
        "canonical_position_id": canonical_id,
        "excluded_position_ids": [18] if excluded_ids is None else excluded_ids,
        "resolution_status": status,
    }


def test_resolved_anf_duplicate_passes_and_canonical_reader_excludes_only_anomaly():
    rows = [
        _row(18, status="stop_loss"),
        _row(19, status="trend_exit"),
        _row(20, symbol="SHOP", entry_date="2026-10-12", status="active"),
    ]
    ledger = [_resolution()]

    assert positions._validate_position_identity_rows(rows, ledger) is True
    canonical = positions._canonical_position_rows(rows, ledger)
    assert [row["id"] for row in canonical] == [19, 20]


def test_unreconciled_duplicate_fails_closed():
    rows = [_row(18, status="stop_loss"), _row(19, status="trend_exit")]

    with pytest.raises(RuntimeError, match="preflight failed"):
        positions._validate_position_identity_rows(rows, [])


def test_review_required_ledger_does_not_silence_duplicate():
    rows = [_row(18, status="stop_loss"), _row(19, status="trend_exit")]

    with pytest.raises(RuntimeError, match="preflight failed"):
        positions._validate_position_identity_rows(
            rows, [_resolution(status="review_required")]
        )


def test_wrong_canonical_or_excluded_set_fails_closed():
    rows = [_row(18, status="stop_loss"), _row(19, status="trend_exit")]

    with pytest.raises(RuntimeError, match="preflight failed"):
        positions._validate_position_identity_rows(
            rows, [_resolution(canonical_id=999, excluded_ids=[18])]
        )

    with pytest.raises(RuntimeError, match="preflight failed"):
        positions._validate_position_identity_rows(
            rows, [_resolution(canonical_id=19, excluded_ids=[])]
        )


def test_resolved_ledger_must_match_current_source_group_exactly():
    rows = [_row(19, status="trend_exit")]

    with pytest.raises(RuntimeError, match="preflight failed"):
        positions._validate_position_identity_rows(rows, [_resolution()])
