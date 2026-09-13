import pandas as pd

from near_trigger_shadow import add_near_trigger_shadow


def _row(**overrides):
    base = {
        "investability_status": "PASS",
        "has_breakout": False,
        "prev_pivot_high": 100.0,
        "close_raw": 99.0,
        "atr14": 2.0,
    }
    base.update(overrides)
    return base


def test_shadow_true_inside_0_60_atr():
    df = pd.DataFrame([_row()])  # distance = 1 / 2 = 0.50 ATR
    out = add_near_trigger_shadow(df)
    assert bool(out.loc[0, "near_trigger_shadow"]) is True


def test_shadow_false_when_too_far():
    df = pd.DataFrame([_row(close_raw=98.0)])  # distance = 2 / 2 = 1.00 ATR
    out = add_near_trigger_shadow(df)
    assert bool(out.loc[0, "near_trigger_shadow"]) is False


def test_shadow_false_after_breakout():
    df = pd.DataFrame([_row(close_raw=101.0, has_breakout=True)])
    out = add_near_trigger_shadow(df)
    assert bool(out.loc[0, "near_trigger_shadow"]) is False


def test_shadow_false_when_not_investable():
    df = pd.DataFrame([_row(investability_status="FAIL")])
    out = add_near_trigger_shadow(df)
    assert bool(out.loc[0, "near_trigger_shadow"]) is False
