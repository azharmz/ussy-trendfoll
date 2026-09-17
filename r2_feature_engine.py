"""Adapter kecil: stock OHLCV dari R2, formula feature tetap milik feature_engine.py."""
from __future__ import annotations

import pandas as pd

import feature_engine as fe
from benchmark_readiness import validate_spy_readiness
from r2_ready import load_ready_dataset, to_feature_contract
from r2_shared_ema import apply_shared_ema_terminal


def build_feature_store_from_r2(sector_map=None, ready=None, manifest=None) -> dict:
    if ready is None or manifest is None:
        ready, manifest = load_ready_dataset()

    raw_universe = to_feature_contract(ready)
    raw_universe["date"] = pd.to_datetime(raw_universe["date"]).astype("datetime64[ns]")
    universe = sorted(raw_universe["symbol"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready universe kosong")

    print(
        f"[R2] snapshot={manifest.get('snapshot_date')} "
        f"securities={len(universe)} rows={len(raw_universe)}"
    )

    original_download_universe = fe.download_universe
    original_download_raw_ohlcv = fe.download_raw_ohlcv

    def _download_raw_ohlcv_ns(*args, **kwargs):
        df = original_download_raw_ohlcv(*args, **kwargs)
        if not df.empty and "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
        return df

    try:
        # Hanya mengganti source raw saham. Benchmark/regime dan seluruh formula
        # feature tetap dieksekusi oleh feature_engine.build_feature_store().
        # Normalisasi resolusi datetime diperlukan di Pandas 3 agar merge_asof
        # tidak menolak pasangan datetime64[ns] vs datetime64[s].
        fe.download_universe = lambda symbols: raw_universe.copy()
        fe.download_raw_ohlcv = _download_raw_ohlcv_ns
        result = fe.build_feature_store(universe, sector_map=sector_map)
    finally:
        fe.download_universe = original_download_universe
        fe.download_raw_ohlcv = original_download_raw_ohlcv

    # FSE-007: RS is an exact-date SPY comparison. Fail closed before any
    # downstream decision if the global R2 T0 lacks an exact SPY observation.
    spy = result.get("benchmarks", {}).get(fe.MARKET_BENCHMARK)
    if spy is None or "date" not in spy.columns:
        raise RuntimeError("SPY benchmark unavailable for R2 readiness validation")
    benchmark_readiness = validate_spy_readiness(
        raw_universe["date"],
        spy["date"],
        as_of_date=raw_universe["date"].max(),
    )
    result["benchmark_readiness"] = benchmark_readiness
    print(
        "[benchmark readiness] exact SPY T0 verified: "
        f"as_of={benchmark_readiness['as_of_date'].date()}"
    )

    migrated, ema_report = apply_shared_ema_terminal(
        result["features"],
        ready,
        manifest,
    )
    result["features"] = migrated
    result["shared_ema_report"] = ema_report
    result["ready_manifest"] = manifest
    result["universe"] = universe
    print(
        "[shared EMA] canonical adj_close state applied to "
        f"{ema_report['terminal_rows_replaced']} terminal rows; "
        f"equivalence_verified={ema_report['equivalence_verified']}"
    )
    return result