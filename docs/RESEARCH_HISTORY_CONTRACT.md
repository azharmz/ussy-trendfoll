# TrendFoll Research History Contract

Status: **DEVELOPMENT-FROZEN ARCHITECTURE CONTRACT / PROB-019**

This contract governs historical TrendFoll diagnostics and backtests. It does not authorize any trading-rule change.

## Purpose

The rolling ~300-bar R2 readiness dataset is the production scanning window and universe authority. It is not sufficient as the initialization history for EMA150/EMA200 and 30-week Stage across a historical evaluation window.

Research therefore uses:

`R2 ready universe -> R2 full stock history -> pre-roll feature initialization -> eligible evaluation rows -> signal/outcome study`

## Sources

Universe authority:

`production/ready/current.json`

Stock history:

`backtest/ohlcv/{security_id}.parquet`

The full-history object is owned by `azharmz/ussy-data` and uses the columns:

`date, security_id, ticker, open, high, low, close, adj_close, volume`

TrendFoll must not redownload stock history from Yahoo when the governed R2 object exists.

Auxiliary benchmark/regime data remains outside this stock-history contract. That dependency boundary is unchanged by PROB-019.

## Pre-roll rule

The default conservative initialization boundary is **500 prior daily bars per security**.

This is not a trading parameter and must not be tuned for performance. It is an engineering warm-up inherited from the governed long-history comparison work that already excluded the first 500 observations per security.

A row is eligible for research only when:

1. it is inside the requested evaluation date range; and
2. its per-security `bar_age` is greater than the frozen minimum pre-roll requirement.

Rows before that boundary remain available only as feature context.

A newly listed security is not rejected globally. It simply becomes research-eligible only after sufficient own-history pre-roll exists.

## No-look-ahead rule

The loader trims stock history to `evaluation_end` **before** feature computation. Future stock rows therefore cannot enter EMA, Stage, structure, volume, ATR, or other feature state for an earlier evaluation horizon.

Consumers must compute features first on the retained full preceding history and only then filter to `research_eligible == True`.

Filtering to the evaluation window before feature computation is a contract violation.

## Canonical EMA semantics

Production TrendFoll now consumes the governed shared EMA state based on `adj_close`.

Historical research must therefore compute:

`adj_close > EMA20 > EMA50 > EMA150 > EMA200`

using long history and `ewm(span=N, adjust=False)`.

This aligns historical trend qualification with the production canonical EMA price basis. It is not a new strategy optimization.

Stage2 remains the existing weekly raw-close 30-week-SMA implementation. All other signal, Investability, Tradability, entry, exit, structure, volume, ATR, and regime formulas remain unchanged unless separately governed.

## Universe scope and survivorship boundary

The contract intentionally preserves **current R2 readiness as the universe authority**, matching the present TrendFoll research mandate.

It does **not** claim point-in-time historical universe membership. Historical performance results must therefore not be represented as survivorship-bias-free unless a separate point-in-time membership contract is introduced later.

## Required provenance

Every governed historical run must retain at least:

- ready snapshot date;
- requested evaluation start/end;
- minimum pre-roll bars;
- number of requested/loaded securities;
- number of history rows and research-eligible rows;
- stock-history R2 prefix;
- EMA price basis;
- deterministic sample definition when a sample is used;
- source compatibility/equivalence evidence when validating the architecture.

## Consumer rule

New DIAG-002, DIAG-003, regime attribution, Investability attribution, and development backtests must use `research_history.py` (or an explicitly equivalent governed successor) rather than building historical features directly from rolling ready data or fresh per-run Yahoo stock downloads.

Existing frozen evidence is not silently rewritten. If an older diagnostic is rerun under this contract, the rerun must be recorded as a new evidence cycle/version.
