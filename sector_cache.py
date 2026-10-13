"""
USSY TrendFoll — Sector Cache
==============================
Cache sector mapping di Supabase. Cache freshness dan cakupan simbol harus
divalidasi terhadap universe yang diminta caller; jumlah baris cache saja tidak
menjamin universe saat ini sudah tercakup.

Catatan: UNIVERSE dari feature_engine adalah universe statis legacy. Jalur
produksi R2 saat ini tidak memakai sector cache (include_sector=False).
Untuk universe dinamis, caller harus mengirim daftar simbol eksplisit.
"""

import math
import pandas as pd
from datetime import datetime, timezone

from feature_engine import build_sector_mapping, UNIVERSE

CACHE_MAX_AGE_DAYS = 30


def get_sector_map(supabase_client, universe: list = UNIVERSE, force_refresh: bool = False) -> pd.DataFrame:
    """Ambil sector mapping hanya jika cache segar dan mencakup semua simbol yang diminta."""
    requested = sorted({str(s).strip().upper() for s in universe if s is not None and str(s).strip()})
    if not requested:
        raise ValueError("Universe sector mapping kosong")

    if universe is UNIVERSE:
        print(
            "[sector_cache] PERINGATAN: memakai UNIVERSE statis legacy dari "
            "feature_engine. Kirim universe eksplisit untuk cakupan R2 terbaru."
        )

    if not force_refresh:
        cached = _load_cache(supabase_client, requested)
        if cached is not None:
            print(f"[sector_cache] Pakai cache ({len(cached)}/{len(requested)} ticker, segar dan lengkap).")
            return cached

    print(f"[sector_cache] Cache basi/tidak lengkap — refresh {len(requested)} ticker dari yfinance...")
    sector_map = build_sector_mapping(requested)
    _save_cache(supabase_client, sector_map)
    return sector_map


def _load_cache(supabase_client, universe: list) -> pd.DataFrame | None:
    resp = supabase_client.table("sector_cache").select("*").execute()
    rows = resp.data or []
    if not rows:
        print("[sector_cache] Cache kosong.")
        return None

    df = pd.DataFrame(rows)
    if "symbol" not in df.columns or "updated_at" not in df.columns:
        print("[sector_cache] Skema cache tidak valid.")
        return None

    df["_symbol_key"] = df["symbol"].astype(str).str.strip().str.upper()
    requested = set(universe)
    relevant = df[df["_symbol_key"].isin(requested)].copy()
    cached_symbols = set(relevant["_symbol_key"])
    missing = sorted(requested - cached_symbols)
    if missing:
        print(f"[sector_cache] Cache tidak mencakup {len(missing)}/{len(requested)} simbol: {missing[:20]}")
        return None

    # Age is calculated only for the requested symbols. Stale rows for unrelated
    # historical symbols must not force a refresh on every call.
    timestamps = pd.to_datetime(relevant["updated_at"], utc=True, errors="coerce")
    if timestamps.isna().any():
        print("[sector_cache] Timestamp cache tidak valid; refresh diperlukan.")
        return None
    age_days = (datetime.now(timezone.utc) - timestamps.min().to_pydatetime()).days
    if age_days > CACHE_MAX_AGE_DAYS:
        print(f"[sector_cache] Cache simbol yang diminta berumur {age_days} hari (> {CACHE_MAX_AGE_DAYS}), dianggap basi.")
        return None

    relevant = relevant.drop_duplicates("_symbol_key", keep="last").set_index("_symbol_key")
    # Return exactly the requested universe, in stable order, never unrelated stale rows.
    out = relevant.loc[universe, ["symbol", "sector", "industry", "sector_benchmark"]].reset_index(drop=True)
    return out


def _save_cache(supabase_client, sector_map: pd.DataFrame):
    now = datetime.now(timezone.utc).isoformat()

    # JSON payload tidak menerima IEEE NaN/Infinity. Normalisasi setiap
    # scalar secara eksplisit karena nilai dari yfinance/pandas dapat berupa
    # numpy scalar yang lolos dari normalisasi DataFrame biasa.
    def _json_safe(value):
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        if isinstance(value, (float, int)) and not math.isfinite(value):
            return None
        return value

    rows = [
        {
            "symbol": _json_safe(r["symbol"]),
            "sector": _json_safe(r["sector"]),
            "industry": _json_safe(r["industry"]),
            "sector_benchmark": _json_safe(r["sector_benchmark"]),
            "updated_at": now,
        }
        for _, r in sector_map.iterrows()
    ]

    # Upsert only: keep historical symbols in cache; callers receive only the
    # requested universe from _load_cache, so stale extras cannot mask gaps.
    supabase_client.table("sector_cache").upsert(rows, on_conflict="symbol").execute()
    print(f"[sector_cache] Cache diperbarui ({len(rows)} ticker).")
