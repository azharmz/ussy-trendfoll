"""Empirical benchmark freshness audit for the R2 production boundary.

Observational only. No production state, thresholds, or database rows are changed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from r2_ready import load_ready_dataset

BENCHMARKS = ["SPY", "QQQ", "^VIX", "XLK", "XLV", "XLY", "XLP", "XLE", "XLI", "XLB", "XLU", "XLC", "XLRE"]


def download(symbol: str) -> pd.DataFrame:
    raw = yf.Ticker(symbol).history(period="2y", auto_adjust=False, timeout=20)
    if raw.empty:
        return pd.DataFrame()
    idx = raw.index.tz_localize(None) if getattr(raw.index, "tz", None) is not None else raw.index
    return pd.DataFrame({"date": pd.to_datetime(idx).normalize(), "close": pd.to_numeric(raw["Close"], errors="coerce")}).dropna()


def main() -> None:
    ready, manifest = load_ready_dataset()
    r2_dates = pd.DatetimeIndex(sorted(pd.to_datetime(ready["date"]).dt.normalize().unique()))
    r2_latest = r2_dates.max()
    rows = []
    frames = {}
    for symbol in BENCHMARKS:
        try:
            df = download(symbol)
            frames[symbol] = df
            if df.empty:
                rows.append({"benchmark": symbol, "status": "EMPTY"})
                continue
            dates = pd.DatetimeIndex(df["date"].unique())
            rows.append({
                "benchmark": symbol,
                "status": "OK",
                "first_date": dates.min().date().isoformat(),
                "latest_date": dates.max().date().isoformat(),
                "latest_minus_r2_calendar_days": int((dates.max() - r2_latest).days),
                "has_exact_r2_latest": bool(r2_latest in dates),
                "r2_dates_missing_in_benchmark": int(len(r2_dates.difference(dates))),
                "benchmark_dates_not_in_r2": int(len(dates.difference(r2_dates))),
            })
        except Exception as exc:
            rows.append({"benchmark": symbol, "status": f"ERROR {type(exc).__name__}: {exc}"})

    detail = pd.DataFrame(rows)
    detail.to_csv("benchmark_freshness_audit.csv", index=False)

    spy = frames.get("SPY", pd.DataFrame())
    if spy.empty:
        raise RuntimeError("SPY unavailable; cannot audit decision-relevant benchmark boundary")
    spy_dates = pd.DatetimeIndex(spy["date"].unique())
    exact_missing = r2_dates.difference(spy_dates)
    prior_for_latest = spy.loc[spy["date"] <= r2_latest, "date"].max() if (spy["date"] <= r2_latest).any() else pd.NaT
    summary = {
        "status": "OBSERVATIONAL_ONLY_NO_PRODUCTION_CHANGE",
        "r2_snapshot_date": manifest.get("snapshot_date"),
        "r2_latest_market_date": r2_latest.date().isoformat(),
        "r2_distinct_dates": int(len(r2_dates)),
        "spy_latest_date": spy_dates.max().date().isoformat(),
        "spy_has_exact_r2_latest": bool(r2_latest in spy_dates),
        "spy_exact_date_missing_count_across_r2_window": int(len(exact_missing)),
        "spy_exact_date_missing_examples": [d.date().isoformat() for d in exact_missing[-20:]],
        "spy_prior_date_for_r2_latest": None if pd.isna(prior_for_latest) else prior_for_latest.date().isoformat(),
        "rs_exact_merge_latest_safe": bool(r2_latest in spy_dates),
        "regime_backward_asof_latest_source_date": None if pd.isna(prior_for_latest) else prior_for_latest.date().isoformat(),
        "benchmarks_checked": BENCHMARKS,
    }
    Path("benchmark_freshness_audit.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(detail.to_string(index=False))


if __name__ == "__main__":
    main()
