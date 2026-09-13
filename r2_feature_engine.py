"""TrendFoll feature-store adapter using USSY R2 ready OHLCV for stocks.

Only the stock universe/OHLCV source changes. Existing benchmark/regime and
feature formulas remain in feature_engine.py so the strategy methodology is
not changed by this migration.
"""
from __future__ import annotations

import pandas as pd

import feature_engine as fe
from r2_ready import load_ready_dataset, to_feature_contract


def build_feature_store_from_r2(sector_map: pd.DataFrame = None) -> dict:
    ready, manifest = load_ready_dataset()
    raw_universe = to_feature_contract(ready)
    universe = sorted(raw_universe["symbol"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready dataset contains no symbols")

    print(
        f"[R2] ready snapshot={manifest.get('snapshot_date')} "
        f"securities={manifest.get('securities')} rows={manifest.get('rows')}"
    )

    # Keep legacy benchmark feeds unchanged in this migration. They drive
    # market/volatility regime and sector-relative-strength calculations.
    print("[1/6] Universe OHLCV: trusted R2 ready dataset")
    print("[2/6] Download benchmark OHLCV (SPY, QQQ, VIX, Sector ETFs)...")
    sector_etfs = sorted({v for v in fe.SECTOR_BENCHMARK_MAP.values() if v is not None})
    benchmark_tickers = [
        fe.MARKET_BENCHMARK,
        fe.SECONDARY_MARKET_BENCHMARK,
        fe.VOLATILITY_BENCHMARK,
    ] + sector_etfs
    benchmarks = {t: fe.download_raw_ohlcv(t) for t in benchmark_tickers}

    if sector_map is not None:
        print("[3/6] Sector mapping: pakai cache yang sudah disediakan...")
        # Ignore stale cache rows outside the currently ready universe.
        sector_map = sector_map[sector_map["symbol"].isin(universe)].copy()
    else:
        print("[3/6] Sector mapping (yfinance .info)...")
        sector_map = fe.build_sector_mapping(universe)

    print("[4/6] Hitung feature Regime dari benchmark...")
    regime_df = fe.compute_market_regime(benchmarks[fe.MARKET_BENCHMARK])
    vol_regime_df = fe.compute_volatility_regime(benchmarks[fe.VOLATILITY_BENCHMARK])
    regime_df = regime_df.merge(vol_regime_df, on="date", how="left")

    spy_ret = benchmarks[fe.MARKET_BENCHMARK].sort_values("date").reset_index(drop=True)
    spy_ret["spy_return_63d"] = fe.compute_return_n(spy_ret)
    spy_ret_lookup = spy_ret[["date", "spy_return_63d"]]

    sector_returns = {}
    for etf in sector_etfs:
        etf_df = benchmarks[etf].sort_values("date").reset_index(drop=True)
        etf_df["sector_return_63d"] = fe.compute_return_n(etf_df)
        sector_returns[etf] = etf_df[["date", "sector_return_63d"]]

    print("[5/6] Hitung feature per ticker (Trend, RS, Structure, Volume)...")
    all_features = []
    for symbol, group in raw_universe.groupby("symbol"):
        df = group.sort_values("date").reset_index(drop=True)
        df = fe.compute_ema_features(df)
        df = fe.compute_structure_features(df)
        df = fe.compute_volume_features(df)

        df["return_63d"] = fe.compute_return_n(df)
        df = df.merge(spy_ret_lookup, on="date", how="left")
        df["rs_spy"] = df["return_63d"] - df["spy_return_63d"]

        bench = sector_map.loc[sector_map["symbol"] == symbol, "sector_benchmark"].values
        bench = bench[0] if len(bench) else None
        df["sector_benchmark"] = bench
        if bench in sector_returns:
            df = df.merge(sector_returns[bench], on="date", how="left")
            df["rs_sector"] = df["return_63d"] - df["sector_return_63d"]
        else:
            df["sector_return_63d"] = None
            df["rs_sector"] = None

        weekly_rs = df.set_index("date")["rs_spy"].resample("W-FRI").last()
        persistence = fe.compute_rs_persistence_weeks(weekly_rs)
        persistence_df = pd.DataFrame({
            "date": persistence.index,
            "rs_spy_persistence_weeks": persistence.values,
        })
        weekly_stage = fe.compute_weekly_stage_features(df)

        df = df.merge(persistence_df, on="date", how="left")
        df = pd.merge_asof(
            df.sort_values("date"), weekly_stage.sort_values("date"),
            on="date", direction="backward",
        )
        df = pd.merge_asof(
            df.sort_values("date"), regime_df.sort_values("date"),
            on="date", direction="backward",
        )

        # Preserve legacy best-effort earnings field; it does not affect R2
        # readiness and is intentionally outside this data-source migration.
        df["days_to_next_earnings"] = None
        try:
            latest_date = df["date"].max()
            df.loc[df["date"] == latest_date, "days_to_next_earnings"] = (
                fe.compute_days_to_next_earnings(symbol, latest_date)
            )
        except Exception:
            pass

        all_features.append(df)

    if not all_features:
        raise RuntimeError("No feature rows produced from R2 ready dataset")
    feature_store = pd.concat(all_features, ignore_index=True)
    print("[6/6] Selesai. Feature Store shape:", feature_store.shape)

    return {
        "raw": raw_universe,
        "features": feature_store,
        "sector_map": sector_map,
        "benchmarks": benchmarks,
        "ready_manifest": manifest,
        "universe": universe,
    }
