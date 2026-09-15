import pandas as pd
import exit_candidate003_shadow as shadow


def test_shadow_contract_is_frozen():
    assert shadow.SHADOW_CONTRACT_VERSION == "exit-cand-003-shadow-v1"
    assert shadow.INITIAL_ATR_MULT == 2.0
    assert shadow.CHAND_PERIOD == 22
    assert shadow.CHAND_ATR_MULT == 3.0
    assert shadow.MAX_HOLDING_DAYS == 45


def test_chandelier_uses_wilder22_and_hh22():
    rows = []
    for i in range(30):
        close = 100.0 + i
        rows.append({
            "symbol": "X",
            "date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=i),
            "open_raw": close - 0.5,
            "high_raw": close + 1.0,
            "low_raw": close - 1.0,
            "close_raw": close,
        })
    out = shadow.add_frozen_shadow_features(pd.DataFrame(rows))
    assert out["shadow_chandelier"].iloc[:21].isna().all()
    assert out["shadow_chandelier"].iloc[21:].notna().all()
    expected = out["shadow_hh22"] - 3.0 * out["shadow_wilder_atr22"]
    pd.testing.assert_series_equal(out["shadow_chandelier"], expected, check_names=False)


def test_trading_day_counter_excludes_entry_date():
    dates = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"])
    assert shadow._trading_days_between("2026-01-05", "2026-01-07", dates) == 2
