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
parameter final Sprint 3, bukan aturan baru:
  1. stop_loss   : close_raw <= stop_price (entry_price - 2*ATR14 saat entry)
  2. trend_exit  : trend patah (ema_stack_aligned False, atau stage bukan Stage2)
  3. max_holding : 45 hari bursa sejak entry_date

Satu symbol cuma boleh punya 1 posisi "active" (unique index parsial di SQL) —
kalau simbol yang sudah exit breakout lagi nanti, itu jadi posisi baru terpisah.
"""

import pandas as pd
from datetime import date

ATR_STOP_MULTIPLIER = 2.0    # final Sprint 3, jangan diubah tanpa alasan
MAX_HOLDING_DAYS = 45        # final Sprint 3


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
        new_rows.append({
            "symbol": r["symbol"],
            "entry_date": pd.Timestamp(as_of_date).date().isoformat(),
            "entry_price": entry_price,
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

    feat_by_symbol = latest_features.set_index("symbol")
    trading_dates = pd.DatetimeIndex(sorted(pd.to_datetime(pd.Series(all_trading_dates)).unique()))
    exits = []

    for pos in active:
        symbol = pos["symbol"]
        if symbol not in feat_by_symbol.index:
            continue  # ticker tidak ada data hari ini (delisted/gap), skip

        row = feat_by_symbol.loc[symbol]
        close_raw = float(row["close_raw"])
        entry_date = pd.Timestamp(pos["entry_date"])
        days_held = _trading_days_between(entry_date, pd.Timestamp(as_of_date), trading_dates)

        exit_reason = None
        if close_raw <= float(pos["stop_price"]):
            exit_reason = "stop_loss"
        elif days_held >= MAX_HOLDING_DAYS:
            exit_reason = "max_holding"
        elif not _trend_still_intact(row):
            exit_reason = "trend_exit"

        if exit_reason:
            client.table("positions").update({
                "status": exit_reason,
                "exit_date": pd.Timestamp(as_of_date).date().isoformat(),
                "exit_price": close_raw,
                "days_held": int(days_held),
                "updated_at": pd.Timestamp.utcnow().isoformat(),
            }).eq("id", pos["id"]).execute()

            pnl_pct = (close_raw - float(pos["entry_price"])) / float(pos["entry_price"]) * 100
            exits.append({
                "symbol": symbol,
                "exit_reason": exit_reason,
                "entry_price": float(pos["entry_price"]),
                "exit_price": close_raw,
                "pnl_pct": pnl_pct,
                "days_held": int(days_held),
            })

    if exits:
        print(f"[positions] {len(exits)} posisi exit hari ini: "
              f"{', '.join(e['symbol'] for e in exits)}")
    return exits


def _trend_still_intact(row) -> bool:
    aligned = row.get("ema_stack_aligned")
    stage = row.get("stage")
    return bool(aligned) and stage == "Stage2"


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