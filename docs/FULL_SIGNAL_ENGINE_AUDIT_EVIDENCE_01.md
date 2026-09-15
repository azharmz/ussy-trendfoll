# Full Signal Engine Audit — Evidence 01

Status: **DIAGNOSTIC EVIDENCE / NO PRODUCTION CHANGE**

## 1. R2 READY history contract

Source-of-truth implementation inspected in `azharmz/ussy-data`:

- `src/build_rolling.py` defaults to `rolling_bars=300` and `minimum_ready_bars=250`.
- For each eligible security, rolling production data is the tail of the historical Parquet object, capped at 300 bars.
- A security is classified READY when its rolling output has at least 250 bars.
- `src/export_ready.py` exports only the READY IDs and explicitly validates that every selected security has between `minimum_ready_bars` and `rolling_bars_target` rows.
- The READY manifest carries both `minimum_ready_bars` and `rolling_bars_target`.

Therefore the production READY contract is a **finite rolling window of 250–300 daily bars per READY security**, not full historical OHLCV.

### Feature warm-up consequences

| Feature | Engine requirement / behavior | READY 250–300 consequence |
|---|---|---|
| RS63 | `shift(63)` | terminal row has sufficient nominal history for every READY security |
| avg volume 50 | rolling 50, min 20 | terminal row has sufficient nominal history |
| pivot high 60 | rolling 60, min 20 | terminal row has sufficient nominal history |
| ATR14 | EWM, min 14 | terminal row has sufficient nominal history |
| ATR percentile 63 | rolling 63, min 20 after ATR | terminal row has sufficient nominal history |
| base length | max backward scan 120 | terminal row has sufficient nominal history |
| weekly Stage | 30-week SMA plus 3 MA observations | 250 bars is nominally sufficient for terminal Stage, subject to weekly calendar/resampling audit |
| 52-week high | rolling 252, **min 20** | securities with 250–251 bars do not have a literal full 252-session window, but code still emits a value because `min_periods=20` |
| historical EMA200 | recursive EWM initialized at first READY row | finite-window initialization can differ from long-history EMA; this is already FSE-005/FSE-008 territory |
| terminal EMA20/50/150/200 | canonical shared R2 EMA state overlays terminal row | terminal EMA is separately repaired/governed; historical rows are not |

### Interim classification

- `B12 finite-window contract`: **ESTABLISHED**.
- Terminal RS63 / volume50 / pivot60 / ATR / structure windows: **nominal bar-count coverage is guaranteed by READY >=250**.
- 52-week-high label: **semantic caveat** because code permits less than 252 observations.
- Historical EMA state: **warm-up risk remains material** because READY truncates history while pandas EWM initializes from the first retained row.
- Stage: nominal history appears sufficient, but exact weekly calendar semantics remain pending.

A governed PROB-018 empirical warm-up audit was triggered on the research branch to quantify EMA-stack, Stage, and Trend-status disagreement against longer-history reference data. Run: `35033214226`, commit `1da39bca43da324a5da546ca784a071f71ce463c`. Its result must be incorporated before closing the warm-up phase.

## 2. External benchmark boundary

`feature_engine.build_feature_store()` downloads externally via yfinance:

- SPY
- QQQ
- ^VIX
- sector ETFs: XLK, XLV, XLY, XLP, XLE, XLI, XLB, XLU, XLC, XLRE where applicable.

Current production stock OHLCV is injected from R2, but benchmark OHLCV is still downloaded by the reused legacy feature engine.

### Production relevance

- **SPY is production-relevant**:
  - SPY raw close -> SMA50/SMA200 -> `market_regime`.
  - SPY adjusted close -> 63-session return -> `rs_spy`.
- **QQQ is downloaded but no production feature calculation found in the inspected build path.** Treat as `DEAD / UNUSED` unless another downstream consumer is found.
- **^VIX** feeds `volatility_regime`, but current Investability/Tradability decision contract does not use volatility regime. Treat as auxiliary / non-decisioning pending downstream-use audit.
- **Sector ETFs** feed `rs_sector`, but current Investability uses `rs_spy`, not `rs_sector`. Treat as auxiliary / non-decisioning pending downstream-use audit.

### Alignment semantics

- Stock `return_63d` is merged to SPY `spy_return_63d` by exact `date` left merge. A missing SPY date therefore yields missing `spy_return_63d` / `rs_spy`; it is not forward-filled in this merge.
- Market regime is merged to each stock with `merge_asof(... direction="backward")`, so it can use the same-date or most recent prior SPY regime state.
- Weekly Stage is likewise backward-as-of merged to daily stock rows.

### Interim classification

The benchmark boundary remains a production architecture risk because R2 stock facts and live yfinance SPY facts do not share one manifest/freshness contract. Static code inspection establishes the mechanism but does not quantify current stale/missing-date incidence. Empirical benchmark freshness/alignment testing remains required.

## 3. Sep-10 diagnostic disposition

The Sep-10 `+61` lifecycle case should no longer be used as evidence of a simultaneous Trend/RS/Liquidity/Price transition. The 61 first-time lifecycle symbols were outside the prior legacy 197-symbol evaluation universe and appeared when the production input universe moved to R2 coverage. Their prior engine state is therefore `NOT EVALUATED / OUTSIDE LEGACY UNIVERSE`, not `FAIL`.

Disposition: **EXPLAINABLE MIGRATION / UNIVERSE-EXPANSION EFFECT**. This closes the mass-transition hypothesis for this diagnostic while leaving the independent signal-engine findings open.
