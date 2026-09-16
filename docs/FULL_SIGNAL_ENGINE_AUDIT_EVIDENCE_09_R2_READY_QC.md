# Full Signal Engine Audit — Evidence 09: R2 READY Empirical QC

Status: **EMPIRICAL INPUT EVIDENCE / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Run provenance

- Workflow: `Signal Engine R2 READY QC Audit`
- Run ID: `35046652834`
- Job ID: `104637810967`
- Head SHA: `4b48b961997f2d84b00ced57510a70f0b7acaee1`
- Conclusion: **SUCCESS**
- Artifact: `r2-ready-qc-1`
- Artifact ID: `10427531637`
- Artifact SHA256: `cc00cba8712d9a7c828d131751a12daa077f925f746f2c7a475616d6af981bca`

## Current READY population

- manifest schema version: 1
- manifest rows: 367,499
- observed rows: 367,499
- manifest security IDs: 1,227
- observed securities: 1,227
- observed unique tickers: 1,227
- global latest market date: 2026-09-14

Manifest/data population counts therefore match exactly for this observed snapshot.

## History-depth distribution

- minimum bars/security: **250**
- median: **300**
- maximum: **300**
- <20: 0
- <50: 0
- <60: 0
- <63: 0
- <150: 0
- <200: 0
- <252: **1**

The only <252 security is `CHOW`, with 250 bars. Three securities have exactly 252 bars (`LGN`, `BRCB`, `FOFO`).

Disposition: the empirical population matches the governed finite READY contract of 250–300 bars. All current READY securities satisfy the nominal history lengths for 20/50/60/63/150/200-session calculations. A literal 252-session measure is not fully available for one 250-bar security, and formulas using permissive `min_periods` must not be described as a literal full-252-session statistic for that row.

## Key/schema quality

- duplicate `(security_id,date)` rows: **0**
- security IDs mapped to multiple tickers: **0**
- tickers mapped to multiple security IDs: **0**
- missing date/security_id/ticker/OHLC/adj_close/volume: **0 for every field**

## Basic OHLCV validity

Observed counts are all zero:

- nonpositive open/high/low/close/adj_close
- negative volume
- high < low
- open outside [low,high]
- close outside [low,high]

Classification for the observed snapshot: **MATCH / CLEAN BASIC FACT CONTRACT**.

## Effective latest-date consistency

Four READY securities do not end on the global latest date 2026-09-14:

| Ticker | Bars | Last date |
|---|---:|---|
| ZTEK | 300 | 2026-09-10 |
| WILC | 300 | 2026-09-03 |
| JFB | 300 | 2026-09-03 |
| YYGH | 300 | 2026-09-11 |

This is a real audit finding for effective-date semantics. `READY` currently guarantees sufficient rolling history, but this empirical snapshot demonstrates that not every READY security necessarily has a row on the global latest market date.

Consequences:

1. Per-symbol latest rows can represent different effective dates if selection is performed independently by symbol.
2. Any cross-sectional current-state funnel must either require a common effective date or explicitly disclose stale-symbol rows.
3. This does not by itself prove a wrong production decision; downstream latest-date selection must be checked against this condition before classification as BUG.

Provisional classification: **NEEDS GOVERNED EFFECTIVE-DATE CONTRACT / EMPIRICAL STALENESS PRESENT IN 4/1,227 SECURITIES**.

This evidence directly informs E9 and should remain open until downstream selection behavior is verified.

## Raw-versus-adjusted continuity

Diagnostic proxy: absolute day-over-day change >5% in `close / adj_close`.

- flagged rows: **31**
- affected securities: **18**

These events are not classified as data defects. Changes in raw/adjusted ratio are expected around dividends, splits, and other corporate-action adjustments. The audit records them as a population requiring semantic review because the engine intentionally mixes raw-price fields with adjusted-return/EMA fields in different features.

Examples with large ratio changes include `VISN`, `NLOP`, `AD`, `SITC`, `CPIX`, and others. No production correction follows from the proxy alone.

Classification: **CORPORATE-ACTION-SENSITIVE EVENTS PRESENT / NEEDS SEMANTIC REVIEW, NOT A DATA-QUALITY FAILURE**.

## Checklist disposition

Closed by this evidence:

- B4 actual READY history-depth distribution
- B5 minimum/median/maximum bars
- B6 counts below feature-history thresholds
- B7 first/last date distribution measured (with four stale-terminal securities explicitly identified)
- B8 duplicate keys
- B9 missing required facts
- B10 basic invalid OHLCV facts
- B11 raw-vs-adjusted continuity screened empirically; interpretation remains feature-specific
- K8 R2 READY empirical QC gate executed successfully

New follow-up required:

- E9: verify downstream latest-date selection behavior against the four stale-terminal READY securities.
- D3.9/D4.4/D5.4: use the 18 raw/adjusted-ratio-event securities when auditing corporate-action semantics of RS, raw volume, and raw price.

No production mutation was made.