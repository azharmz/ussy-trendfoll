from datetime import datetime, timedelta, timezone

import pandas as pd

from sector_cache import _load_cache


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args):
        return self

    def execute(self):
        return _Response(self.rows)


class _Client:
    def __init__(self, rows):
        self.rows = rows

    def table(self, _name):
        return _Query(self.rows)


def _row(symbol, updated_at):
    return {
        "symbol": symbol,
        "sector": "Technology",
        "industry": "Software",
        "sector_benchmark": "XLK",
        "updated_at": updated_at,
    }


def test_cache_miss_for_requested_universe_symbol():
    now = datetime.now(timezone.utc).isoformat()
    client = _Client([_row("AAPL", now)])

    assert _load_cache(client, ["AAPL", "RBRK"]) is None


def test_unrelated_stale_symbol_does_not_invalidate_requested_universe():
    fresh = datetime.now(timezone.utc).isoformat()
    stale = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    client = _Client([
        _row("AAPL", fresh),
        _row("RBRK", fresh),
        _row("OLD_SYMBOL", stale),
    ])

    result = _load_cache(client, ["AAPL", "RBRK"])

    assert result is not None
    assert result["symbol"].tolist() == ["AAPL", "RBRK"]


def test_requested_universe_cache_is_returned_in_requested_order():
    fresh = datetime.now(timezone.utc).isoformat()
    client = _Client([_row("RBRK", fresh), _row("AAPL", fresh)])

    result = _load_cache(client, ["AAPL", "RBRK"])

    assert result is not None
    assert result["symbol"].tolist() == ["AAPL", "RBRK"]
