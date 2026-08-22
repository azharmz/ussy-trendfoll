"""
USSY TrendFoll — Position & Exit Tracking
=============================================
Posisi dicatat OTOMATIS begitu kondisi entry PERSIS SAMA dengan yang dipakai
di backtest (portfolio_backtest()) yang sudah divalidasi Sprint 3 — supaya
forward-test ini apple-to-apple dengan backtest, bukan strategi yang beda:

  - hard_filter_status == "PASS"   (5 kriteria: trend+liquidity+rs+price+REGIME,
                                     non-compensatory — BUKAN cuma investability,
                                     yang sengaja TIDAK termasuk regime)
  - has_breakout == True
  - has_volume_confirmation == True
  (has_tight_structure TIDAK disyaratkan — terverifikasi dari data trade
  historis, has_tight_structure bervariasi True/False di 1302 trade backtest,
  jadi bukan syarat keras masuk backtest, cuma pembeda tier tradability
  PASS vs NEAR_PASS di decision_layer, bukan gate entry).

Koreksi dari versi sebelumnya: sempat pakai `tradability_status == "PASS"`
tanpa cek investability/regime sama sekali — itu SALAH, karena investability
dan tradability dihitung independen (bisa ada ticker investability FAIL tapi
tradability PASS), dan regime_status tidak pernah dicek. Diverifikasi ulang:
di 1302 trade backtest historis, regime_status SELALU PASS (0 trade lain) —
mengkonfirmasi backtest memang mensyaratkan hard_filter_status PASS penuh.

Tiap hari, posisi yang masih "active" dicek terhadap 3 kondisi exit — PERSIS
logika di portfolio_backtest.py (parameter final Sprint 3), diverifikasi
baris-per-baris terhadap kode aslinya:
  1. stop_loss   : low_raw <= stop_price (intraday LOW, BUKAN close) —
                   exit_price diasumsikan terisi PERSIS di stop_price, bukan
                   di close hari itu (asumsi fill konservatif dari backtest)
  2. max_holding : 45 hari bursa sejak entry_date, exit_price = close_raw
  3. trend_exit  : close_raw < ema20 (BUKAN ema_stack_aligned/stage — itu
                   kriteria Investability yang beda tujuan) — exit_price = close_raw

Koreksi dari versi sebelumnya: sempat pakai close_raw untuk cek stop_loss
(harusnya low_raw) dan ema_stack_aligned+stage untuk trend_exit (harusnya
close_raw<ema20, kriteria yang jauh lebih sederhana). Ditemukan dari audit
line-by-line terhadap ussy_swing_portfolio_backtest.py yang baru diupload —
sebelumnya saya belum pernah lihat file itu, jadi exit logic ditulis
berdasarkan asumsi, bukan verifikasi langsung ke kode aslinya.

Satu symbol cuma boleh punya 1 posisi "active" (unique index parsial di SQL) —
kalau simbol yang sudah exit breakout lagi nanti, itu jadi posisi baru terpisah.
"""

import pandas as pd
from datetime import date

ATR_STOP_MULTIPLIER = 2.0    # final Sprint 3, jangan diubah tanpa alasan
MAX_HOLDING_DAYS = 45        # final Sprint 3


def fill_realistic_entry_prices(client, latest: pd.DataFrame, as_of_date, all_trading_dates):
    """
    entry_price (close hari sinyal) match backtest, tapi TIDAK realistis
    dieksekusi manusia (notifikasi Telegram baru masuk setelah market tutup).
    realistic_entry_price = open_raw di HARI BURSA BERIKUTNYA setelah
    entry_date — baru bisa diisi 1 hari setelah posisi diregistrasi (begitu
    data open besok tersedia di run berikutnya), makanya fungsi ini jalan
    tiap hari dan cuma ngisi yang masih kosong DAN entry_date-nya persis
    kemarin (1 hari bursa sebelum as_of_date).

    DEFENSIVE CHECK: kalau `latest` punya baris duplikat untuk symbol yang
    sama (harusnya tidak pernah terjadi, tapi pernah ditemukan kasus
    realistic_entry_price ke-isi salah - misalnya kepilih High bukan Open),
    fungsi ini sekarang detect & log eksplisit alih-alih diam-diam pakai
    baris yang salah.
    """
    pending = client.table("positions").select("id, symbol, entry_date") \
        .is_("realistic_entry_price", "null").execute().data
    if not pending:
        return

    trading_dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(all_trading_dates)).unique()))
    idx_asof = trading_dates.searchsorted(pd.Timestamp(as_of_date))

    # Cek duplikat symbol di `latest` SEBELUM di-index -- kalau ada, log semua
    # baris duplikatnya supaya ketahuan datanya seperti apa.
    dup_symbols = latest["symbol"][latest["symbol"].duplicated(keep=False)].unique()
    if len(dup_symbols) > 0:
        print(f"[positions][WARN] Ditemukan {len(dup_symbols)} symbol duplikat di `latest` "
              f"tanggal {pd.Timestamp(as_of_date).date()}: {list(dup_symbols)}")
        for s in dup_symbols:
            dup_rows = latest[latest["symbol"] == s][["symbol", "date", "open_raw", "high_raw", "close_raw"]]
            print(f"[positions][WARN]   Baris duplikat untuk {s}:\n{dup_rows.to_string(index=False)}")

    feat_by_symbol = latest.drop_duplicates(subset="symbol", keep="first").set_index("symbol")

    filled = 0
    for p in pending:
        entry_date = pd.Timestamp(p["entry_date"])
        idx_entry = trading_dates.searchsorted(entry_date)
        if idx_asof - idx_entry != 1:
            continue  # bukan "hari berikutnya" dari entry_date, skip (belum waktunya / sudah lewat & data hilang)

        symbol = p["symbol"]
        if symbol not in feat_by_symbol.index:
            continue
        row = feat_by_symbol.loc[symbol]
        open_price = row.get("open_raw")
        if pd.isna(open_price):
            continue

        # Log eksplisit setiap kali diisi -- supaya kalau ada kasus aneh
        # lagi, log GitHub Actions langsung kasih bukti tanggal & nilai
        # yang dipakai, tidak perlu diagnosa manual seperti kasus CRSR.
        print(f"[positions] Isi realistic_entry_price {symbol}: entry_date={entry_date.date()}, "
              f"tanggal open dipakai={row.get('date')}, open_raw={open_price}, "
              f"high_raw={row.get('high_raw')} (pembanding, harus BEDA dari open_raw kecuali kebetulan)")

        client.table("positions").update({
            "realistic_entry_price": float(open_price),
        }).eq("id", p["id"]).execute()
        filled += 1

    if filled:
        print(f"[positions] {filled} realistic_entry_price terisi (open H+1).")


def register_new_positions(client, latest: pd.DataFrame, as_of_date):
    """
    latest: baris hari ini untuk SELURUH universe (bukan cuma watchlist
    candidates) — hasil decision_layer.compute_decision_layer() yang
    dibangun dari hard_filter.compute_hard_filter(), jadi punya kolom
    hard_filter_status, has_breakout, has_volume_confirmation.

    Insert posisi baru untuk symbol yang match kondisi entry backtest DAN
    belum punya posisi 'active' (unique index di SQL bakal reject percobaan
    insert duplikat juga, tapi kita cek dulu di sini supaya tidak spam
    error ke log).
    """
    entry_ready = latest[
        (latest["hard_filter_status"] == "PASS")
        & (latest["has_breakout"] == True)
        & (latest["has_volume_confirmation"] == True)
    ]
    if entry_ready.empty:
        return []

    existing_active = _get_active_symbols(client)
    new_rows = []
    for _, r in entry_ready.iterrows():
        if r["symbol"] in existing_active:
            continue  # sudah ada posisi aktif untuk symbol ini, skip
        entry_price = float(r["close_raw"])
        atr14 = float(r.get("atr14")) if pd.notna(r.get("atr14")) else None
        if atr14 is None:
            print(f"[positions] {r['symbol']}: atr14 kosong, skip registrasi posisi.")
            continue
        stop_price = entry_price - ATR_STOP_MULTIPLIER * atr14
        prev_close = float(r.get("prev_close")) if pd.notna(r.get("prev_close")) else None
        new_rows.append({
            "symbol": r["symbol"],
            "entry_date": pd.Timestamp(as_of_date).date().isoformat(),
            "entry_price": entry_price,
            "prev_close": prev_close,               # untuk metrik T-1->T0 momentum
            "max_close_since_entry": entry_price,    # basis awal MFE, sebelum ada data hari berikutnya
            "min_close_since_entry": entry_price,    # basis awal MAE
            "stop_price": stop_price,
            "status": "active",
        })

    if new_rows:
        client.table("positions").insert(new_rows).execute()
        print(f"[positions] {len(new_rows)} posisi baru diregistrasi: "
              f"{', '.join(r['symbol'] for r in new_rows)}")
    return new_rows


def check_exits(client, latest_features: pd.DataFrame, as_of_date, all_trading_dates):
    """
    latest_features: baris hari ini untuk SELURUH universe (bukan cuma
    kandidat) — hasil decision_layer.compute_decision_layer(), difilter ke
    as_of_date. Perlu kolom: symbol, close_raw, atr14, ema_stack_aligned, stage.

    all_trading_dates: array/Series tanggal bursa UNIK dari seluruh histori
    feature store (bukan cuma tanggal terbaru) — dipakai untuk hitung hari
    BURSA yang akurat antara entry_date dan as_of_date (45 hari kalender !=
    45 hari bursa, bedanya signifikan untuk threshold max_holding).

    Return: list dict posisi yang baru exit hari ini (untuk notifikasi).
    """
    active = _get_active_positions(client)
    if not active:
        return []

    feat_by_symbol = latest_features.drop_duplicates(subset="symbol", keep="first").set_index("symbol")
    trading_dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(all_trading_dates)).unique()))
    exits = []

    for pos in active:
        symbol = pos["symbol"]
        if symbol not in feat_by_symbol.index:
            continue  # ticker tidak ada data hari ini (delisted/gap), skip

        row = feat_by_symbol.loc[symbol]
        close_raw = float(row["close_raw"])
        low_raw = float(row["low_raw"])
        entry_date = pd.Timestamp(pos["entry_date"])
        days_held = _trading_days_between(entry_date, pd.Timestamp(as_of_date), trading_dates)

        exit_reason = exit_price = None
        if low_raw <= float(pos["stop_price"]):
            exit_reason, exit_price = "stop_loss", float(pos["stop_price"])
        elif days_held >= MAX_HOLDING_DAYS:
            exit_reason, exit_price = "max_holding", close_raw
        elif pd.notna(row.get("ema20")) and close_raw < float(row["ema20"]):
            exit_reason, exit_price = "trend_exit", close_raw

        # MFE/MAE: basis close harian sejak entry — TAPI di hari exit, pakai
        # exit_price (bukan close_raw penuh hari itu). Begitu stop tersentuh
        # intraday dan tereksekusi, posisi sudah selesai — pergerakan harga
        # SETELAH itu sampai closing bukan lagi pengalaman yang dialami,
        # jadi tidak boleh ikut memperdalam MAE. Untuk trend_exit/max_holding
        # ini tidak mengubah apapun (exit_price == close_raw hari itu),
        # cuma relevan buat stop_loss (exit_price = level stop, bisa beda
        # dari close hari itu).
        price_for_excursion = exit_price if exit_reason else close_raw
        prev_max = pos.get("max_close_since_entry")
        prev_min = pos.get("min_close_since_entry")
        new_max = max(float(prev_max), price_for_excursion) if prev_max is not None else price_for_excursion
        new_min = min(float(prev_min), price_for_excursion) if prev_min is not None else price_for_excursion

        if exit_reason:
            client.table("positions").update({
                "status": exit_reason,
                "exit_date": pd.Timestamp(as_of_date).date().isoformat(),
                "exit_price": exit_price,
                "mark_price": close_raw,
                "max_close_since_entry": new_max,
                "min_close_since_entry": new_min,
                "days_held": int(days_held),
                "updated_at": pd.Timestamp.utcnow().isoformat(),
            }).eq("id", pos["id"]).execute()

            pnl_pct = (exit_price - float(pos["entry_price"])) / float(pos["entry_price"]) * 100
            exits.append({
                "symbol": symbol,
                "exit_reason": exit_reason,
                "entry_price": float(pos["entry_price"]),
                "exit_price": exit_price,
                "pnl_pct": pnl_pct,
                "days_held": int(days_held),
            })
        else:
            # Masih active — tetap update mark_price + MFE/MAE supaya
            # floating PnL dan riwayat excursion kelihatan di dashboard,
            # meski belum exit.
            client.table("positions").update({
                "mark_price": close_raw,
                "max_close_since_entry": new_max,
                "min_close_since_entry": new_min,
                "updated_at": pd.Timestamp.utcnow().isoformat(),
            }).eq("id", pos["id"]).execute()

    if exits:
        print(f"[positions] {len(exits)} posisi exit hari ini: "
              f"{', '.join(e['symbol'] for e in exits)}")
    return exits


def _trading_days_between(entry_date, as_of_date, trading_dates: pd.DatetimeIndex) -> int:
    """Hitung hari BURSA antara entry_date dan as_of_date, pakai posisi index
    di kalender bursa asli (bukan estimasi kalender)."""
    idx_entry = trading_dates.searchsorted(entry_date)
    idx_asof = trading_dates.searchsorted(as_of_date)
    return max(int(idx_asof - idx_entry), 0)


def _get_active_positions(client):
    resp = client.table("positions").select("*").eq("status", "active").execute()
    return resp.data


def _get_active_symbols(client):
    return {p["symbol"] for p in _get_active_positions(client)}