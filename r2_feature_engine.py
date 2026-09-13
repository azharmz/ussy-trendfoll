"""Adapter kecil: stock OHLCV dari R2, formula feature tetap milik feature_engine.py."""
from __future__ import annotations

import pandas as pd

import feature_engine as fe
from r2_ready import load_ready_dataset, to_feature_contract


def build_feature_store_from_r2(sector_map=None) -> dict:
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

    result["ready_manifest"] = manifest
    result["universe"] = universe
    return result
