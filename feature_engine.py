"""
USSY Swing — Feature Engine
============================
Deliverable #3 — Sprint 1 (Phase 1A: Data Foundation)

Menghitung seluruh feature yang didefinisikan di `ussy-swing-feature-registry.md`
dari raw OHLCV (yfinance), sesuai kontrak kolom di `ussy-swing-data-dictionary.md`.

Dijalankan di Google Colab. Output: Feature Store (Parquet), satu baris per
(symbol, date), siap dipakai Phase 1B (Regime, Hard Filter, Backtest).

PRINSIP:
- Belum ada BUY/SELL/Score/Rank di sini. Murni feature (fakta dari data).
- Data mentah ditarik SEKALI (period="max"). lookback_years adalah parameter
  backtest di Phase 1B, bukan parameter ingestion di sini.
- Formula `base_length_days` dan `vcp_tightness` adalah STARTING POINT,
  ditandai eksplisit sebagai kandidat iterasi setelah backtest pertama.
"""

import time
import numpy as np
import pandas as pd
import yfinance as yf

# ============================================================
# 1. CONFIG — Universe & Benchmark (sesuai Data Dictionary)
# ============================================================

UNIVERSE = [
    "AAPL", "ABT", "ACAD", "ACM", "ADBE", "ADPT", "ADSK", "AEM",
    "AKAM", "ALB", "ALC", "ALGN", "ALLE", "ALNY", "AMAT", "AMD",
    "AME", "AMPL", "ANET", "ANF", "AOS", "APD", "ASAN", "ASML",
    "ASND", "AVGO", "AZN", "AZO", "BB", "BBY", "BDX", "BHP",
    "BIIB", "BIRD", "BOX", "BRZE", "BSX", "CAH", "CDNS", "CDW",
    "CELH", "CF", "CHD", "CHRW", "CL", "CLX", "CNI", "CNQ",
    "CPNG", "CPRI", "CRL", "CRM", "CROX", "CRSR", "CRWD", "CSCO",
    "CSX", "CTAS", "CVX", "DASH", "DD", "DDOG", "DECK", "DHI",
    "DHR", "DOCU", "DOV", "DXCM", "ECL", "EL", "EMR", "ENPH",
    "ENTG", "EOG", "EPAM", "EQIX", "EXPD", "FFIV", "FIGS", "FIVN",
    "FIZZ", "FRSH", "FSLR", "FSLY", "FTNT", "GDDY", "GILD", "GLW",
    "GPC", "GPRO", "GRMN", "GSK", "GTLB", "HAL", "HD", "HNST",
    "HSY", "HUBS", "IDXX", "ILMN", "INCY", "ISRG", "IT", "ITW",
    "JBHT", "JCI", "JMIA", "JNJ", "KEYS", "KLAC", "KLTR", "KMB",
    "KO", "LEN", "LEVI", "LIN", "LLY", "LOGI", "LOW", "LRCX",
    "LULU", "MCHP", "MCK", "MDB", "MDT", "MKC", "MMM", "MNST",
    "MRK", "MRVL", "MSI", "MU", "NEGG", "NKE", "NOW", "NTAP",
    "NUE", "NVDA", "NVS", "ODFL", "OKTA", "OTIS", "PANW", "PATH",
    "PG", "PHM", "PLUG", "PPG", "PWR", "QCOM", "RBLX", "RL",
    "RMD", "ROK", "ROST", "SAP", "SBUX", "SEDG", "SHOP", "SLB",
    "SNOW", "SNPS", "SNY", "STM", "STX", "SU", "SWKS", "TDUP",
    "TEAM", "TECH", "TER", "TJX", "TPR", "TSCO", "TSLA", "TSM",
    "TTD", "TWLO", "TXG", "TXN", "UBER", "ULTA", "UMC", "UNP",
    "UPS", "VLO", "VRSN", "VRTX", "WDC", "WIX", "WM", "WMS",
    "WSM", "XOM", "XYL", "ZS", "ZTS",
]

MARKET_BENCHMARK = "SPY"
SECONDARY_MARKET_BENCHMARK = "QQQ"
VOLATILITY_BENCHMARK = "^VIX"

# yfinance `.info["sector"]` pakai penamaan sendiri (bukan persis label GICS
# di Data Dictionary) — mapping di bawah ini sudah disesuaikan ke istilah
# yfinance. Kalau ada sector baru yang muncul dan tidak ada di sini,
# get_sector_benchmark() akan return None dan dicatat sebagai unmapped.
SECTOR_BENCHMARK_MAP = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Utilities": "XLU",
    "Communication Services": "XLC",
    "Real Estate": "XLRE",
    "Financial Services": None,  # excluded dari universe per Data Dictionary
    "Financial": None,
}

HISTORY_PERIOD = "max"  # ingestion sekali, lookback_years jadi parameter backtest (Phase 1B)
RS_LOOKBACK_DAYS = 63   # ~3 bulan trading days, dipakai untuk return_63d
VOLUME_LOOKBACK_DAYS = 50
ATR_PERIOD = 14
ADX_PERIOD = 14


# ============================================================
# 2. DATA INGESTION — sesuai kontrak Data Dictionary
# ============================================================

def download_raw_ohlcv(ticker: str, period: str = HISTORY_PERIOD, timeout: int = 15) -> pd.DataFrame:
    """Tarik OHLCV mentah dan rename ke kontrak kolom Data Dictionary.
    timeout: batas waktu (detik) per request — TANPA ini, yfinance bisa hang
    tanpa batas kalau Yahoo Finance tidak merespons (tidak error, diam saja)."""
    raw = yf.Ticker(ticker).history(period=period, auto_adjust=False, timeout=timeout)
    if raw.empty:
        return pd.DataFrame()

    df = pd.DataFrame({
        "date": raw.index.tz_localize(None) if raw.index.tz is not None else raw.index,
        "symbol": ticker,
        "open_raw": raw["Open"].values,
        "high_raw": raw["High"].values,
        "low_raw": raw["Low"].values,
        "close_raw": raw["Close"].values,
        "close_adj": raw["Adj Close"].values,
        "volume_raw": raw["Volume"].values,
        "dividends": raw["Dividends"].values if "Dividends" in raw.columns else 0.0,
        "stock_splits": raw["Stock Splits"].values if "Stock Splits" in raw.columns else 0.0,
    })
    return df.reset_index(drop=True)


def download_universe(ticker_list, pause_seconds: float = 0.3, timeout: int = 15) -> pd.DataFrame:
    """Loop seluruh universe. pause_seconds untuk menghindari rate-limit yfinance.
    Print SEBELUM setiap ticker diproses — supaya kalau macet, kelihatan persis
    macetnya di ticker mana (bukan diam total seperti versi sebelumnya)."""
    frames = []
    failed = []
    for i, t in enumerate(ticker_list):
        print(f"  [{i + 1}/{len(ticker_list)}] Downloading {t}...", end=" ", flush=True)
        try:
            df = download_raw_ohlcv(t, timeout=timeout)
            if df.empty:
                print("KOSONG")
                failed.append(t)
            else:
                print(f"OK ({len(df)} baris)")
                frames.append(df)
        except Exception as e:
            print(f"GAGAL: {type(e).__name__}: {e}")
            failed.append(t)
        time.sleep(pause_seconds)

    if failed:
        print(f"\n[INFO] {len(failed)} ticker gagal/kosong: {failed}")

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# 3. SECTOR MAPPING (untuk RS_SECTOR)
# ============================================================

import signal


class _TimeoutException(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _TimeoutException()


def get_sector_benchmark(ticker: str, timeout_seconds: int = 15) -> dict:
    """Ambil sector/industry dari yfinance .info, map ke Sector Benchmark.
    CATATAN: .info/get_info() TIDAK punya parameter timeout bawaan di yfinance
    0.2.66 (beda dengan history() yang punya timeout default 10 detik) — kalau
    Yahoo lambat merespons, request ini bisa hang tanpa batas. Karena itu kita
    paksa timeout manual pakai signal.alarm (hanya jalan di Linux/main thread,
    aman untuk Colab)."""
    sector, industry = None, None
    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_seconds)
        try:
            info = yf.Ticker(ticker).get_info()
            sector = info.get("sector")
            industry = info.get("industry")
        finally:
            signal.alarm(0)  # matikan alarm begitu selesai (sukses ataupun gagal)
    except _TimeoutException:
        print(f"[WARN] TIMEOUT ({timeout_seconds}s) mengambil info untuk {ticker} — dilewati.")
    except Exception as e:
        print(f"[WARN] Gagal ambil info sector untuk {ticker}: {type(e).__name__}: {e}")

    benchmark = SECTOR_BENCHMARK_MAP.get(sector)
    if sector is not None and sector not in SECTOR_BENCHMARK_MAP:
        print(f"[INFO] Sector '{sector}' ({ticker}) belum ada di SECTOR_BENCHMARK_MAP — perlu ditambahkan manual.")

    return {"symbol": ticker, "sector": sector, "industry": industry, "sector_benchmark": benchmark}


def build_sector_mapping(ticker_list, pause_seconds: float = 0.3) -> pd.DataFrame:
    rows = []
    for i, t in enumerate(ticker_list):
        print(f"  [{i + 1}/{len(ticker_list)}] Sector mapping {t}...", end=" ", flush=True)
        row = get_sector_benchmark(t)
        print("OK" if row["sector"] else "KOSONG/GAGAL")
        rows.append(row)
        time.sleep(pause_seconds)
    return pd.DataFrame(rows)


# ============================================================
# 4. FEATURE FUNCTIONS — dihitung per simbol (df sorted by date ascending)
# ============================================================

# ---- Regime (dihitung terpisah dari benchmark, lihat build_regime_features) ----

def compute_market_regime(bench_df: pd.DataFrame) -> pd.DataFrame:
    """bench_df: OHLCV benchmark (mis. SPY), sudah punya close_raw."""
    df = bench_df.copy().sort_values("date").reset_index(drop=True)
    df["spy_ma50"] = df["close_raw"].rolling(50).mean()
    df["spy_ma200"] = df["close_raw"].rolling(200).mean()

    def classify(row):
        if pd.isna(row["spy_ma50"]) or pd.isna(row["spy_ma200"]):
            return None
        if row["close_raw"] > row["spy_ma50"] > row["spy_ma200"]:
            return "Bullish"
        if row["close_raw"] < row["spy_ma50"] < row["spy_ma200"]:
            return "Bearish"
        return "Neutral"

    df["market_regime"] = df.apply(classify, axis=1)
    return df[["date", "spy_ma50", "spy_ma200", "market_regime"]]


def compute_volatility_regime(vix_df: pd.DataFrame, window_days: int = 252) -> pd.DataFrame:
    df = vix_df.copy().sort_values("date").reset_index(drop=True)
    df["vix_close"] = df["close_raw"]
    df["_p80"] = df["vix_close"].rolling(window_days).quantile(0.8)
    df["_p20"] = df["vix_close"].rolling(window_days).quantile(0.2)

    def classify(row):
        if pd.isna(row["_p80"]) or pd.isna(row["_p20"]):
            return None
        if row["vix_close"] > row["_p80"]:
            return "High"
        if row["vix_close"] < row["_p20"]:
            return "Low"
        return "Normal"

    df["volatility_regime"] = df.apply(classify, axis=1)
    return df[["date", "volatility_regime"]]


# ---- Trend ----

def compute_ema_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["ema20"] = df["close_raw"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close_raw"].ewm(span=50, adjust=False).mean()
    df["ema150"] = df["close_raw"].ewm(span=150, adjust=False).mean()
    df["ema200"] = df["close_raw"].ewm(span=200, adjust=False).mean()
    df["ema_stack_aligned"] = (
        (df["close_raw"] > df["ema20"])
        & (df["ema20"] > df["ema50"])
        & (df["ema50"] > df["ema150"])
        & (df["ema150"] > df["ema200"])
    )
    df["pct_off_52w_high"] = (
        (df["close_raw"] - df["high_raw"].rolling(252, min_periods=20).max())
        / df["high_raw"].rolling(252, min_periods=20).max() * 100
    )
    return df


def compute_weekly_stage_features(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily -> weekly (canonical timeframe = Daily, Weekly diturunkan darinya)."""
    daily = df.sort_values("date").set_index("date")
    weekly_close = daily["close_raw"].resample("W-FRI").last()

    ma30w = weekly_close.rolling(30).mean()
    slope = pd.Series(index=ma30w.index, dtype=object)
    for i in range(2, len(ma30w)):
        a, b, c = ma30w.iloc[i - 2], ma30w.iloc[i - 1], ma30w.iloc[i]
        if pd.isna(a) or pd.isna(b) or pd.isna(c):
            slope.iloc[i] = None
        elif c > b > a:
            slope.iloc[i] = "Up"
        elif c < b < a:
            slope.iloc[i] = "Down"
        else:
            slope.iloc[i] = "Flat"

    def stage_of(price, ma, sl):
        if pd.isna(ma) or sl is None:
            return None
        if price > ma and sl == "Up":
            return "Stage2"
        if price < ma and sl == "Down":
            return "Stage4"
        if price > ma and sl in ("Flat", "Down"):
            return "Stage3"
        return "Stage1"

    stage = pd.Series(
        [stage_of(weekly_close.iloc[i], ma30w.iloc[i], slope.iloc[i]) for i in range(len(ma30w))],
        index=ma30w.index,
    )

    weekly_df = pd.DataFrame({
        "date": ma30w.index,
        "ma30w": ma30w.values,
        "ma30w_slope": slope.values,
        "stage": stage.values,
    })
    # Forward-fill ke tanggal harian supaya bisa join balik ke feature store daily
    return weekly_df


# ---- Relative Strength ----

def compute_return_n(df: pd.DataFrame, n: int = RS_LOOKBACK_DAYS, col: str = "close_adj") -> pd.Series:
    return df[col] / df[col].shift(n) - 1


def compute_rs_persistence_weeks(rs_weekly: pd.Series) -> pd.Series:
    """Hitung berapa minggu berturut-turut RS positif & naik dibanding minggu sebelumnya."""
    result = []
    streak = 0
    prev = None
    for val in rs_weekly:
        if pd.isna(val):
            streak = 0
        elif prev is not None and val > prev and val > 0:
            streak += 1
        elif val > 0:
            streak = 1
        else:
            streak = 0
        result.append(streak)
        prev = val
    return pd.Series(result, index=rs_weekly.index)


# ---- Structure ----

def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    high, low, close = df["high_raw"], df["low_raw"], df["close_raw"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder's smoothing (EMA dengan alpha = 1/period)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def compute_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.Series:
    high, low, close = df["high_raw"], df["low_raw"], df["close_raw"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = compute_atr(df, period=1) * 1  # true range mentah (period=1 -> tanpa smoothing tambahan)
    atr_smooth = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr_smooth
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / period, adjust=False).mean() / atr_smooth

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return adx


def compute_structure_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["atr14"] = compute_atr(df, ATR_PERIOD)
    df["atr_pct"] = df["atr14"] / df["close_raw"] * 100
    df["atr_percentile_63d"] = df["atr14"].rolling(63, min_periods=20).apply(
        lambda x: (x <= x.iloc[-1]).mean() * 100, raw=False
    )
    df["adx14"] = compute_adx(df, ADX_PERIOD)

    # --- v2: LOCAL HIGH ANCHOR + NO-NEW-HIGH STREAK (Pendekatan 3) ---
    # Menggantikan v1 (band % dari rolling max window tetap) yang terbukti gagal
    # membedakan base vs uptrend biasa (lihat catatan validasi visual).
    #
    # Algoritma per hari t (scan mundur):
    #   1. anchor_high mulai dari high_raw[t] (hari ini).
    #   2. Melangkah mundur: kalau high_raw[i] > anchor_high, PERLUAS anchor_high
    #      ke nilai itu (base ceiling bisa naik kalau ada wiggle ke atas dalam base).
    #   3. Berhenti begitu low_raw[i] jatuh di bawah band toleransi dari anchor_high
    #      saat itu — titik itu dianggap di luar base (base baru mulai setelah i).
    #   4. base_length_days = jumlah hari mundur sebelum berhenti.
    #
    # Ini memperbaiki bug v1: anchor sekarang DINAMIS (mengikut highest high dalam
    # base itu sendiri), bukan window tetap yang bisa "mengingat" puncak lama tidak
    # relevan dari sebelum konsolidasi dimulai.
    def local_high_anchor_base_length(high_arr, low_arr, band_pct=0.08, max_lookback=120):
        n = len(high_arr)
        result = np.full(n, np.nan)
        for t in range(n):
            if t < 5:  # butuh minimal beberapa hari histori
                continue
            anchor_high = high_arr[t]
            length = 0
            lookback_limit = min(t, max_lookback)
            for back in range(1, lookback_limit + 1):
                i = t - back
                if high_arr[i] > anchor_high:
                    anchor_high = high_arr[i]
                band_low = anchor_high * (1 - band_pct)
                if low_arr[i] < band_low:
                    break
                length = back
            result[t] = length
        return result

    df["base_length_days"] = local_high_anchor_base_length(
        df["high_raw"].values, df["low_raw"].values, band_pct=0.08, max_lookback=120
    )

    # vcp_tightness: starting point — makin tinggi atr_percentile_63d menurun
    # dari waktu ke waktu (kontraksi), makin tinggi skor. Placeholder sederhana:
    # inverse dari atr_percentile_63d (percentile rendah = volatilitas mengecil = tightness tinggi).
    df["vcp_tightness"] = 100 - df["atr_percentile_63d"]

    df["pivot_high"] = df["high_raw"].rolling(60, min_periods=20).max()
    df["pct_from_pivot"] = (df["close_raw"] - df["pivot_high"]) / df["pivot_high"] * 100

    return df


# ---- Volume ----

def compute_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["avg_volume_50d"] = df["volume_raw"].rolling(VOLUME_LOOKBACK_DAYS, min_periods=20).mean()
    df["avg_volume_10d"] = df["volume_raw"].rolling(10, min_periods=5).mean()
    df["volume_ratio"] = df["volume_raw"] / df["avg_volume_50d"]
    df["volume_dry_up"] = df["avg_volume_10d"] < (df["avg_volume_50d"] * 0.7)
    df["breakout_volume_percentile"] = df["volume_raw"].rolling(50, min_periods=20).apply(
        lambda x: (x <= x.iloc[-1]).mean() * 100, raw=False
    )
    return df


# ---- Risk ----

def compute_days_to_next_earnings(ticker: str, as_of_date: pd.Timestamp) -> int:
    """Best-effort: yfinance calendar tidak selalu tersedia/reliable untuk semua ticker."""
    try:
        cal = yf.Ticker(ticker).calendar
        if cal is None or (hasattr(cal, "empty") and cal.empty):
            return None
        earnings_date = cal.get("Earnings Date")
        if earnings_date is None:
            return None
        next_date = earnings_date[0] if isinstance(earnings_date, list) else earnings_date
        return (pd.Timestamp(next_date) - as_of_date).days
    except Exception:
        return None


# ============================================================
# 5. MAIN PIPELINE — gabungkan semua feature jadi Feature Store
# ============================================================

def build_feature_store(universe: list, sector_map: pd.DataFrame = None) -> dict:
    """
    Return dict berisi:
      - 'raw'      : raw OHLCV seluruh universe (kontrak Data Dictionary)
      - 'features' : feature store lengkap (per symbol, per date, semua 33 feature)
      - 'sector_map': mapping ticker -> sector benchmark
      - 'benchmarks': dict raw OHLCV benchmark (SPY, QQQ, VIX, 10 sector ETF)

    sector_map: kalau sudah di-fetch sebelumnya (mis. dari cache produksi via
    sector_cache.get_sector_map()), lewatkan di sini supaya tidak fetch ulang.
    Kalau None, fetch baru seperti biasa (perilaku Sprint 1 original).
    """
    print("[1/6] Download universe OHLCV (period=max)...")
    raw_universe = download_universe(universe)

    print("[2/6] Download benchmark OHLCV (SPY, QQQ, VIX, Sector ETFs)...")
    sector_etfs = sorted({v for v in SECTOR_BENCHMARK_MAP.values() if v is not None})
    benchmark_tickers = [MARKET_BENCHMARK, SECONDARY_MARKET_BENCHMARK, VOLATILITY_BENCHMARK] + sector_etfs
    benchmarks = {t: download_raw_ohlcv(t) for t in benchmark_tickers}

    if sector_map is not None:
        print("[3/6] Sector mapping: pakai yang sudah disediakan (cache)...")
    else:
        print("[3/6] Sector mapping (yfinance .info)...")
        sector_map = build_sector_mapping(universe)

    print("[4/6] Hitung feature Regime dari benchmark...")
    regime_df = compute_market_regime(benchmarks[MARKET_BENCHMARK])
    vol_regime_df = compute_volatility_regime(benchmarks[VOLATILITY_BENCHMARK])
    regime_df = regime_df.merge(vol_regime_df, on="date", how="left")

    spy_ret = benchmarks[MARKET_BENCHMARK].sort_values("date").reset_index(drop=True)
    spy_ret["spy_return_63d"] = compute_return_n(spy_ret)
    spy_ret_lookup = spy_ret[["date", "spy_return_63d"]]

    sector_returns = {}
    for etf in sector_etfs:
        etf_df = benchmarks[etf].sort_values("date").reset_index(drop=True)
        etf_df["sector_return_63d"] = compute_return_n(etf_df)
        sector_returns[etf] = etf_df[["date", "sector_return_63d"]]

    print("[5/6] Hitung feature per ticker (Trend, RS, Structure, Volume)...")
    all_features = []
    for symbol, group in raw_universe.groupby("symbol"):
        df = group.sort_values("date").reset_index(drop=True)

        df = compute_ema_features(df)
        df = compute_structure_features(df)
        df = compute_volume_features(df)

        df["return_63d"] = compute_return_n(df)
        df = df.merge(spy_ret_lookup, on="date", how="left")
        df["rs_spy"] = df["return_63d"] - df["spy_return_63d"]

        bench_ticker = sector_map.loc[sector_map["symbol"] == symbol, "sector_benchmark"].values
        bench_ticker = bench_ticker[0] if len(bench_ticker) else None
        df["sector_benchmark"] = bench_ticker
        if bench_ticker in sector_returns:
            df = df.merge(sector_returns[bench_ticker], on="date", how="left")
            df["rs_sector"] = df["return_63d"] - df["sector_return_63d"]
        else:
            df["sector_return_63d"] = None
            df["rs_sector"] = None

        # RS persistence dihitung di level weekly
        weekly_rs = df.set_index("date")["rs_spy"].resample("W-FRI").last()
        persistence = compute_rs_persistence_weeks(weekly_rs)
        persistence_df = pd.DataFrame({
            "date": persistence.index,
            "rs_spy_persistence_weeks": persistence.values,
        })

        # Weekly stage features (MA30W, slope, Stage)
        weekly_stage = compute_weekly_stage_features(df)

        df = df.merge(persistence_df, on="date", how="left")
        df = pd.merge_asof(
            df.sort_values("date"),
            weekly_stage.sort_values("date"),
            on="date",
            direction="backward",
        )
        df = pd.merge_asof(
            df.sort_values("date"),
            regime_df.sort_values("date"),
            on="date",
            direction="backward",
        )

        # Risk: earnings date (opsional, best-effort, hanya untuk baris terakhir/current)
        df["days_to_next_earnings"] = None
        try:
            latest_date = df["date"].max()
            df.loc[df["date"] == latest_date, "days_to_next_earnings"] = compute_days_to_next_earnings(
                symbol, latest_date
            )
        except Exception:
            pass

        all_features.append(df)

    feature_store = pd.concat(all_features, ignore_index=True)

    print("[6/6] Selesai. Feature Store shape:", feature_store.shape)

    return {
        "raw": raw_universe,
        "features": feature_store,
        "sector_map": sector_map,
        "benchmarks": benchmarks,
    }


def save_feature_store(result: dict, output_dir: str = "."):
    """Simpan ke Parquet — Feature Store immutable, layer lain hanya membaca."""
    result["raw"].to_parquet(f"{output_dir}/ussy_swing_raw_ohlcv.parquet", index=False)
    result["features"].to_parquet(f"{output_dir}/ussy_swing_feature_store.parquet", index=False)
    result["sector_map"].to_parquet(f"{output_dir}/ussy_swing_sector_map.parquet", index=False)

    # Simpan benchmark OHLCV (SPY, QQQ, VIX, Sector ETF) terpisah — dibutuhkan
    # sebagai kalender referensi trading day di Acceptance Test (no_missing_trading_days),
    # dan tidak termasuk di raw_ohlcv (yang murni 197 ticker universe).
    benchmark_frames = []
    for ticker, df in result["benchmarks"].items():
        if not df.empty:
            benchmark_frames.append(df)
    if benchmark_frames:
        pd.concat(benchmark_frames, ignore_index=True).to_parquet(
            f"{output_dir}/ussy_swing_benchmark_ohlcv.parquet", index=False
        )

    print(f"Feature Store tersimpan di {output_dir}/ussy_swing_feature_store.parquet")


# ============================================================
# 6. ENTRY POINT (Colab)
# ============================================================

if __name__ == "__main__":
    result = build_feature_store(UNIVERSE)
    save_feature_store(result, output_dir=".")
