import pandas as pd

from trend_filter_candidate import add_sma_struct_features, compute_sma_struct_features


def _history(symbol: str, closes):
    return pd.DataFrame({
        "symbol": symbol,
        "date": pd.date_range("2025-01-01", periods=len(closes), freq="D"),
        "close_raw": closes,
    })


def test_not_evaluable_before_200_bars():
    df = compute_sma_struct_features(_history("AAA", list(range(1, 200))))
    assert not df["tf_sma_struct_evaluable"].any()
    assert not df["tf_sma_struct_pass"].any()


def test_passes_clean_uptrend_after_200_bars():
    df = compute_sma_struct_features(_history("AAA", list(range(1, 221))))
    row = df.iloc[-1]
    assert bool(row["tf_sma_struct_evaluable"])
    assert row["close_raw"] > row["sma50"] > row["sma200"]
    assert bool(row["tf_sma_struct_pass"])


def test_candidate_uses_exact_finite_windows():
    closes = list(range(1, 321))
    full = compute_sma_struct_features(_history("AAA", closes))
    truncated = compute_sma_struct_features(_history("AAA", closes[-300:]))

    assert full.iloc[-1]["sma50"] == truncated.iloc[-1]["sma50"]
    assert full.iloc[-1]["sma200"] == truncated.iloc[-1]["sma200"]
    assert bool(full.iloc[-1]["tf_sma_struct_pass"]) == bool(truncated.iloc[-1]["tf_sma_struct_pass"])


def test_multi_symbol_calculation_does_not_mix_histories():
    up = _history("UP", list(range(1, 221)))
    down = _history("DOWN", list(range(220, 0, -1)))
    out = add_sma_struct_features(pd.concat([up, down], ignore_index=True))

    last = out.groupby("symbol").tail(1).set_index("symbol")
    assert bool(last.loc["UP", "tf_sma_struct_pass"])
    assert not bool(last.loc["DOWN", "tf_sma_struct_pass"])
