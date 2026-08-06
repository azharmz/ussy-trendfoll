# USSY TrendFoll — Daily Watchlist Pipeline

Pipeline harian: fetch OHLCV → hitung feature → hard filter → decision layer
(Investability/Tradability/Explainability) → simpan ke Supabase → notifikasi
Telegram. Dijalankan otomatis via GitHub Actions.

## Setup

### 1. Buat repo GitHub
Push folder ini ke repo baru (public atau private, keduanya bisa pakai GitHub
Actions gratis untuk repo kecil seperti ini).

### 2. Jalankan SQL schema
Buka Supabase project → SQL Editor → jalankan isi `sql/schema.sql`, lalu
`sql/schema_positions.sql` (tabel exit tracking).

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
`watchlist` di Supabase + pesan Telegram masuk.

### 5. Jadwal otomatis
Sudah di-set jalan Senin-Jumat jam 21:30 UTC (kira-kira 1.5 jam setelah
market close NYSE) di `.github/workflows/daily.yml`. Sesuaikan cron
expression itu kalau timing-nya kurang pas.

## Struktur file

- `feature_engine.py`, `hard_filter.py`, `decision_layer.py` — modul riset asli
  (Sprint 1-3 + Phase 2), dipakai apa adanya
- `sector_cache.py` — cache sector mapping di Supabase (refresh cuma kalau
  >30 hari, supaya tidak fetch ulang 197x tiap hari secara percuma)
- `database.py` — upsert hasil ke tabel `watchlist`
- `notify.py` — kirim ringkasan ke Telegram (skip diam-diam kalau
  token/chat ID belum di-set)
- `positions.py` — exit tracking: registrasi posisi baru otomatis saat
  tradability=PASS, cek harian 3 kondisi exit (stop_loss/trend_exit/
  max_holding), kirim alert Telegram terpisah dari watchlist harian
- `main.py` — orkestrator, dipanggil GitHub Actions

## Exit tracking (posisi otomatis)

Setiap ticker dengan `tradability_status == "PASS"` otomatis dicatat sebagai
posisi "active" (satu posisi aktif per symbol). Tiap hari, posisi aktif dicek
terhadap parameter final Sprint 3:

- **stop_loss**: harga close ≤ entry_price − 2×ATR14 (saat entry)
- **trend_exit**: trend patah (EMA stack tidak lagi aligned, atau stage bukan Stage2)
- **max_holding**: sudah 45 hari BURSA sejak entry (bukan hari kalender)

Begitu salah satu kondisi terpenuhi, posisi ditutup dan alert Telegram
terpisah dikirim (beda dari ringkasan watchlist harian) — supaya jelas mana
"kandidat baru" vs "saatnya keluar dari posisi lama". Histori lengkap
tersimpan di tabel `positions` (tidak overwrite), jadi bisa dipakai untuk
evaluasi performa live vs ekspektasi backtest nanti.


## Catatan penting

- **Runtime**: pipeline fetch histori penuh (`period="max"`) untuk 197 ticker
  tiap run — bisa makan beberapa menit. Test manual dulu (langkah 4) untuk
  tahu berapa lama sebelum mengandalkan jadwal otomatis.
- **Frontend web** belum termasuk di repo ini — itu langkah terpisah
  (dashboard baca dari tabel `watchlist` via Supabase anon key, read-only).
- Watchlist yang disimpan cuma kandidat dengan `investability_status >=
  NEAR_PASS` di tanggal terbaru — histori tetap tersimpan (insert per
  tanggal, bukan overwrite) untuk bahan kalibrasi confidence score nanti
  (Phase 3).
