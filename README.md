# USSY TrendFoll — Daily Watchlist & Paper Trading Pipeline

Pipeline harian: fetch OHLCV → hitung feature → hard filter → decision layer
(Investability/Tradability/Explainability) → simpan ke Supabase → notifikasi
Telegram → tracking posisi otomatis (paper trading, bukan eksekusi riil).
Dijalankan otomatis via GitHub Actions.

## Setup

### 1. Buat repo GitHub
Push folder ini ke repo baru.

### 2. Jalankan SQL schema
Buka Supabase project → SQL Editor → jalankan isi `sql/schema.sql`, lalu
`sql/schema_positions.sql` (tabel exit tracking). Keduanya aman dijalankan
ulang (idempotent).

Untuk database yang sudah memiliki posisi lama, jalankan juga
`sql/migrate_stop_anchor_filled.sql` satu kali. Migrasi ini idempotent dan
hanya mengubah stop posisi yang masih aktif.

### 3. Set GitHub Actions secrets
Repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Nilai |
|---|---|
| `SUPABASE_URL` | `https://rggtylvlrzzesrtumqzj.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | dari Supabase → Settings → API → `service_role` key |
| `TELEGRAM_BOT_TOKEN` | token bot dari @BotFather |
| `TELEGRAM_CHAT_ID` | chat ID tujuan notifikasi |

### 4. Test manual dulu sebelum andalkan cron
Tab **Actions** di repo → pilih workflow "USSY TrendFoll — Daily Watchlist" →
**Run workflow** (trigger manual via `workflow_dispatch`). Cek log-nya:
runtime total, ada ticker yang gagal fetch atau tidak, dan cek tabel
`watchlist`/`positions` di Supabase + pesan Telegram masuk.

### 5. Jadwal otomatis
Sudah di-set jalan Senin-Jumat jam 22:30 UTC di `.github/workflows/daily.yml`
(minimal 1,5 jam setelah market close saat DST maupun non-DST).

## Struktur file

- `feature_engine.py`, `hard_filter.py`, `decision_layer.py` — modul riset asli
  (Sprint 1-3 + Phase 2), dipakai apa adanya
- `sector_cache.py` — cache sector mapping di Supabase (refresh cuma kalau
  >30 hari)
- `database.py` — upsert hasil ke tabel `watchlist`
- `notify.py` — kirim ringkasan watchlist harian + alert exit posisi ke
  Telegram (skip diam-diam kalau token/chat ID belum di-set)
- `positions.py` — exit tracking: registrasi posisi baru otomatis, cek
  harian 3 kondisi exit, isi realistic_entry_price (open H+1), update
  mark_price + MFE/MAE tiap hari
- `backtests/` — notebook eksperimen; tidak dipakai pipeline produksi
- `main.py` — orkestrator, dipanggil GitHub Actions

## Kondisi masuk Posisi Aktif

```
hard_filter_status == "PASS"      # 5 kriteria: Trend+Liquidity+RS+Price+Regime
AND has_breakout == True           # close_raw > prev_pivot_high
AND has_volume_confirmation == True  # breakout_volume_percentile >= 80
```
`has_tight_structure` TIDAK disyaratkan — diverifikasi ke `portfolio_backtest.py`
asli, bukan syarat keras masuk backtest.

## Exit tracking (persis parameter final Sprint 3)

- **stop_loss**: `low_raw <= stop_price` (intraday low, bukan close) —
  exit_price = stop_price (asumsi fill persis di level stop)
- **stop anchor**: `realistic_entry_price (open H+1) - 2 × ATR14 T0`.
  ATR dibekukan dari hari sinyal; stop diperbarui setelah open H+1 tersedia
  dan sebelum pengecekan exit pada hari tersebut.
- **max_holding**: 45 hari BURSA sejak entry (hari entry = 0)
- **trend_exit**: `close_raw < ema20`

Satu symbol cuma boleh punya 1 posisi `active` (unique index parsial di SQL).

## Kolom harga di tabel `positions`

- `entry_price` ("Trigger") — close hari sinyal, match backtest tapi tidak
  realistis dieksekusi (notifikasi baru masuk setelah market tutup)
- `realistic_entry_price` ("Entry") — open hari bursa BERIKUTNYA, terisi
  otomatis 1 hari setelah entry_date
- `atr14_at_entry` — ATR14 pada hari sinyal T0, disimpan agar stop selalu
  dapat diaudit dan dihitung dari harga Entry
- `mark_price` — harga terkini, di-update tiap run selama posisi masih active
- `prev_close`, `max_close_since_entry`, `min_close_since_entry` — untuk
  metrik Momentum T-1→T0 dan MFE/MAE (dihitung sejak Entry)

Floating PnL & metrik lain di dashboard basisnya **realistic_entry_price**,
fallback ke `entry_price` (ditandai `*`) kalau belum terisi.

## Cap 20 posisi & modal (sengaja TIDAK diimplementasikan)

`portfolio_backtest.py` membatasi 20 posisi bersamaan + cek kecukupan modal.
`positions.py` di sini **unlimited** — keputusan sadar, karena tabel
`positions` untuk tracking semua sinyal valid (paper trading/forward-test),
bukan simulasi portfolio dengan modal terbatas.
