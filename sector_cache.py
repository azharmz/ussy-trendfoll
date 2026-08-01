"""
USSY TrendFoll — Sector Cache
==============================
Sector suatu perusahaan nyaris tidak pernah berubah harian. Fetch ulang
sector mapping tiap hari (197 panggilan yfinance .info) itu request yang
terbuang percuma dan cuma menambah runtime tanpa manfaat.

Strategi: sector map disimpan di tabel `sector_cache` Supabase. Tiap run
harian, cek dulu apakah cache masih ada dan belum terlalu basi (default:
30 hari). Kalau masih segar, pakai cache. Kalau basi/kosong, fetch ulang
lewat feature_engine.build_sector_mapping() dan overwrite cache.
"""

import pandas as pd
from datetime import datetime, timedelta, timezone

from feature_engine import build_sector_mapping, UNIVERSE

CACHE_MAX_AGE_DAYS = 30


def get_sector_map(supabase_client, universe: list = UNIVERSE, force_refresh: bool = False) -> pd.DataFrame:
    """Ambil sector mapping — dari cache Supabase kalau masih segar, atau fetch baru."""
    if not force_refresh:
        cached = _load_cache(supabase_client)
        if cached is not None:
            print(f"[sector_cache] Pakai cache ({len(cached)} ticker, masih segar).")
            return cached

    print("[sector_cache] Cache kosong/basi — fetch ulang dari yfinance...")
    sector_map = build_sector_mapping(universe)
    _save_cache(supabase_client, sector_map)
    return sector_map


def _load_cache(supabase_client) -> pd.DataFrame:
    resp = supabase_client.table("sector_cache").select("*").execute()
    rows = resp.data
    if not rows:
        return None

    df = pd.DataFrame(rows)
    oldest_update = pd.to_datetime(df["updated_at"]).min()
    if oldest_update.tzinfo is None:
        oldest_update = oldest_update.tz_localize("UTC")
    age_days = (datetime.now(timezone.utc) - oldest_update).days
    if age_days > CACHE_MAX_AGE_DAYS:
        print(f"[sector_cache] Cache berumur {age_days} hari (> {CACHE_MAX_AGE_DAYS}), dianggap basi.")
        return None

    return df[["symbol", "sector", "industry", "sector_benchmark"]]


def _save_cache(supabase_client, sector_map: pd.DataFrame):
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "symbol": r["symbol"],
            "sector": r["sector"],
            "industry": r["industry"],
            "sector_benchmark": r["sector_benchmark"],
            "updated_at": now,
        }
        for _, r in sector_map.iterrows()
    ]
    # upsert per batch (Supabase python client handles list upsert in one call)
    supabase_client.table("sector_cache").upsert(rows, on_conflict="symbol").execute()
    print(f"[sector_cache] Cache diperbarui ({len(rows)} ticker).")
