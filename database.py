"""
USSY TrendFoll — Database (Supabase)
======================================
Simpan hasil decision layer harian ke tabel `watchlist`. Skema tabel di
`sql/schema.sql`.

Kredensial diambil dari environment variable (diset sebagai GitHub Actions
secret), TIDAK di-hardcode di sini:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
"""

import os
import pandas as pd
from supabase import create_client

WATCHLIST_COLS = [
    "symbol", "date", "close_raw",
    "investability_status", "tradability_status",
    "has_breakout", "has_volume_confirmation", "has_tight_structure",
    "regime_status", "market_regime",
]

WATCHLIST_HISTORY_SELECT = (
    "symbol,date,close_raw,investability_status,tradability_status,"
    "has_breakout,has_volume_confirmation,has_tight_structure,"
    "regime_status,market_regime,explanation_text"
)


def get_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def get_previous_watchlist(supabase_client, as_of_date) -> pd.DataFrame:
    """Ambil snapshot watchlist terbaru yang tanggalnya < as_of_date.

    Query tanggal dilakukan terpisah supaya kita selalu membandingkan seluruh
    snapshot hari bursa sebelumnya, bukan satu row/ticker acak.
    """
    date_str = pd.Timestamp(as_of_date).date().isoformat()
    latest_prior = (
        supabase_client.table("watchlist")
        .select("date")
        .lt("date", date_str)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    rows = latest_prior.data or []
    if not rows:
        return pd.DataFrame()

    previous_date = rows[0]["date"]
    snapshot = (
        supabase_client.table("watchlist")
        .select("symbol,date,close_raw,investability_status,tradability_status,has_breakout,has_volume_confirmation,has_tight_structure,regime_status,market_regime")
        .eq("date", previous_date)
        .execute()
    )
    return pd.DataFrame(snapshot.data or [])


def get_watchlist_history(supabase_client, page_size: int = 1000) -> pd.DataFrame:
    """Ambil seluruh histori watchlist secara paginated.

    `watchlist` memang menyimpan satu row per (symbol, date), jadi kandidat yang
    hilang dari snapshot terbaru tidak hilang dari database. Fungsi ini menjadi
    sumber persistent candidate lifecycle tanpa membuat tabel baru.
    """
    rows = []
    start = 0
    while True:
        resp = (
            supabase_client.table("watchlist")
            .select(WATCHLIST_HISTORY_SELECT)
            .order("date", desc=False)
            .order("symbol", desc=False)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = resp.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["symbol", "date"]).reset_index(drop=True)


def upsert_watchlist(supabase_client, decision_df: pd.DataFrame, explanations: dict):
    """
    decision_df: hasil compute_decision_layer(), sudah difilter ke tanggal
      terbaru + investability minimal NEAR_PASS (baris yang layak masuk watchlist).
    explanations: dict {symbol: markdown_checklist_string} dari explain_candidate(),
      disimpan sebagai explanation_text supaya frontend/Telegram tidak perlu
      menghitung ulang checklist-nya.
    """
    if decision_df.empty:
        print("[database] Tidak ada kandidat untuk disimpan hari ini.")
        return

    rows = []
    for _, r in decision_df.iterrows():
        row = {c: (r[c] if c in r and pd.notna(r[c]) else None) for c in WATCHLIST_COLS}
        row["date"] = pd.Timestamp(row["date"]).date().isoformat()
        row["explanation_text"] = explanations.get(r["symbol"], "")
        rows.append(row)

    supabase_client.table("watchlist").upsert(rows, on_conflict="symbol,date").execute()
    print(f"[database] {len(rows)} baris watchlist di-upsert.")
