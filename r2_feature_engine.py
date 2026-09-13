"""Adapter kecil: stock OHLCV dari R2, formula feature tetap milik feature_engine.py."""
from __future__ import annotations

import feature_engine as fe
from r2_ready import load_ready_dataset, to_feature_contract


def build_feature_store_from_r2(sector_map=None) -> dict:
    ready, manifest = load_ready_dataset()
    raw_universe = to_feature_contract(ready)
    universe = sorted(raw_universe["symbol"].dropna().unique().tolist())
    if not universe:
        raise RuntimeError("R2 ready universe kosong")

    print(
        f"[R2] snapshot={manifest.get('snapshot_date')} "
        f"securities={len(universe)} rows={len(raw_universe)}"
    )

    original_download_universe = fe.download_universe
    try:
        # Hanya mengganti source raw saham. Benchmark/regime dan seluruh formula
        # feature tetap dieksekusi oleh feature_engine.build_feature_store().
        fe.download_universe = lambda symbols: raw_universe.copy()
        result = fe.build_feature_store(universe, sector_map=sector_map)
    finally:
        fe.download_universe = original_download_universe

    result["ready_manifest"] = manifest
    result["universe"] = universe
    return result
