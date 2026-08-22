"""
USSY TrendFoll — One-Time Backfill Historical Data
=====================================================
SEKALI JALAN SAJA. Perbaiki data historis yang salah/kosong di tabel
`positions`, dengan fetch ulang OHLCV asli dari yfinance (bukan tebakan):

1. CRSR: realistic_entry_price salah (14.978, seharusnya 14.86 — bug lama
   yang sudah diperbaiki di kode produksi) + max/min_close_since_entry
   masih NULL (posisi diregistrasi sebelum fitur MFE/MAE ada).
2. FSLY, AME, ANET (dan posisi lain yang diregistrasi sebelum fitur MFE/MAE
   ada): max/min_close_since_entry degenerate (sama persis dengan PnL exit)
   karena tracking-nya baru mulai di hari terakhir, bukan dari entry.

Cara kerja: untuk SETIAP baris di tabel `positions`, fetch ulang histori
harga symbol itu dari yfinance (entry_date - 10 hari sampai exit_date + 5
hari, atau sampai hari ini kalau masih active), lalu hitung ulang:
  - prev_close       : close T-1 (hari bursa sebelum entry_date)
  - realistic_entry_price : open hari bursa BERIKUTNYA setelah entry_date
  - max/min_close_since_entry : rentang close dari entry_date (mulai dari
    entry_price, yang memang == close T0) sampai exit_date (atau hari ini)

HANYA overwrite realistic_entry_price kalau beda signifikan (>0.5%) dari
yang sudah ada, supaya tidak mengubah data yang sudah benar tanpa alasan.

SETELAH DIJALANKAN SEKALI DAN SUKSES: hapus file ini dan workflow-nya
(.github/workflows/one_time_backfill.yml) dari repo — tidak perlu jadi
bagian permanen pipeline.
"""

import os
import time
import pandas as pd
import yfinance as yf
from supabase import create_client


def get_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def backfill():
    client = get_client()
    positions = client.table("positions").select("*").execute().data
    print(f"Total posisi ditemukan: {len(positions)}")

    for pos in positions:
        symbol = pos["symbol"]
        entry_date = pd.Timestamp(pos["entry_date"])
        end_date = pd.Timestamp(pos["exit_date"]) if pos.get("exit_date") else pd.Timestamp.today()

        fetch_start = entry_date - pd.Timedelta(days=10)
        fetch_end = end_date + pd.Timedelta(days=5)

        try:
            hist = yf.Ticker(symbol).history(
                start=fetch_start.strftime("%Y-%m-%d"),
                end=fetch_end.strftime("%Y-%m-%d"),
                auto_adjust=False,
            )
        except Exception as e:
            print(f"[SKIP] {symbol} (id={pos['id']}): gagal fetch ({type(e).__name__}: {e})")
            continue

        if hist.empty:
            print(f"[SKIP] {symbol} (id={pos['id']}): data kosong dari yfinance")
            continue

        hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
        hist = hist.sort_index()
        trading_dates = hist.index

        # prev_close: close di hari bursa SEBELUM entry_date
        prior_dates = trading_dates[trading_dates < entry_date]
        prev_close = float(hist.loc[prior_dates[-1], "Close"]) if len(prior_dates) > 0 else None

        # realistic_entry_price: open di hari bursa BERIKUTNYA setelah entry_date
        next_dates = trading_dates[trading_dates > entry_date]
        realistic_entry_price = float(hist.loc[next_dates[0], "Open"]) if len(next_dates) > 0 else None

        # max/min close sejak entry: mulai dari entry_price (= close T0),
        # lalu tiap close harian sampai end_date (exit_date atau hari ini)
        period_dates = trading_dates[(trading_dates > entry_date) & (trading_dates <= end_date)]
        # Sama seperti fix di positions.py: di hari exit, pakai exit_price
        # (bukan close hari itu) — begitu stop tersentuh & tereksekusi,
        # pergerakan harga setelahnya bukan lagi pengalaman yang dialami.
        closes_in_period = [float(pos["entry_price"])]
        exit_date_only = end_date.normalize() if pos.get("exit_date") else None
        for d in period_dates:
            if exit_date_only is not None and d.normalize() == exit_date_only and pos.get("exit_price") is not None:
                closes_in_period.append(float(pos["exit_price"]))
            else:
                closes_in_period.append(float(hist.loc[d, "Close"]))

        max_close = max(closes_in_period)
        min_close = min(closes_in_period)

        update = {}

        if prev_close is not None and pd.isna(pos.get("prev_close")):
            update["prev_close"] = prev_close

        if realistic_entry_price is not None:
            existing = pos.get("realistic_entry_price")
            if existing is None or abs(existing - realistic_entry_price) / realistic_entry_price > 0.005:
                update["realistic_entry_price"] = realistic_entry_price

        existing_max = pos.get("max_close_since_entry")
        existing_min = pos.get("min_close_since_entry")
        if existing_max is None or abs(existing_max - max_close) > 0.005:
            update["max_close_since_entry"] = max_close
        if existing_min is None or abs(existing_min - min_close) > 0.005:
            update["min_close_since_entry"] = min_close

        if update:
            client.table("positions").update(update).eq("id", pos["id"]).execute()
            print(f"[FIXED] {symbol} (id={pos['id']}): {update}")
        else:
            print(f"[OK]    {symbol} (id={pos['id']}): sudah benar, tidak ada perubahan")

        time.sleep(0.3)  # sopan ke yfinance, jangan spam request

    print("\nSelesai. Cek tabel `positions` di Supabase untuk verifikasi.")


if __name__ == "__main__":
    backfill()