# Trend Filter Methodology Audit — O'Neil / CAN SLIM Adaptation

Status: **RESEARCH NOTE / DEVELOPMENT-FROZEN CANDIDATE / NO PRODUCTION CHANGE**

## Research question

For TrendFoll, which moving-average representation is methodologically justified for structural trend qualification when adapting the O'Neil/CAN SLIM family to short-to-medium swing trading?

This audit is **not** a parameter search and does not ask which moving-average combination produces the best backtest. It first identifies candidate rules supported by the source methodology, then permits a governed empirical comparison.

## Source evidence

Authoritative/first-party O'Neil/IBD material repeatedly treats the following as distinct technical horizons:

- **50-day moving average (50-DMA)**: an important intermediate trend/support line.
- **200-day moving average (200-DMA)**: a major long-term trend/support line.
- **10-day moving average**: a shorter tactical line used for active trade management.
- **21-day exponential moving average (21-EMA)**: a faster/intermediate trade-management line between the 10-day and 50-day horizons.
- SwingTrader explicitly adapts CAN SLIM/IBD methodology to a shorter swing-trading environment.

Structural trend qualification and tactical trade management therefore remain separate.

## Current production baseline

`close > EMA20 > EMA50 > EMA150 > EMA200`

plus weekly Stage2 based on a 30-week simple moving average.

Production remains unchanged.

## Frozen development candidate

### TF-SMA-STRUCT-01

`close > SMA50 > SMA200`

No `SMA200 rising` gate is included because no exact authoritative slope horizon has been established. No extra MA terms, slope lookbacks, or parameter grids may be added after viewing development results without a new evidence-backed hypothesis.

## Historical-data contract

Research uses:

`R2 readiness universe -> long-history OHLCV -> 500-bar context-only warm-up -> evaluation window`

Pre-evaluation history is feature context only and does not count as evaluated observations or outcomes. This is a development research contract, not a change to the production R2 readiness contract.

## Development comparison Cycle 1

Workflow: `Trend Filter Development Comparison` run `34810094506`.

Run conclusion: **SUCCESS**.

Artifact:
- ID: `10333279823`
- Name: `trend-filter-comparison-1`
- SHA256: `1cfc38ca12043ce78e19d80cdb954a52e8c70e646975536db595b5016c5091a0`
- R2 readiness snapshot: `2026-08-28`
- Deterministic SHA256-ranked sample: 100 symbols
- Symbols downloaded: 100
- Warm-up excluded: first 500 observations per symbol
- Comparable evaluation rows: 427,604

### Structural coverage

| Metric | Baseline | TF-SMA-STRUCT-01 |
|---|---:|---:|
| PASS rate | 23.45% | 34.23% |
| PASS rows | 100,290 | 146,388 |
| Unique symbols with PASS | 76 | 80 |

Agreement rate was 86.80%.

Disagreement decomposition:
- both PASS: 95,109
- baseline-only: 5,181
- candidate-only: 51,279
- neither: 276,035

The candidate is therefore materially broader/less selective than the current baseline. Candidate-only observations outnumber baseline-only observations by almost ten to one.

### Raw forward path from structural PASS rows

These are descriptive close-to-close future returns from every structural PASS row, not independent entry-ready events and not executable-entry backtests.

| Horizon | Baseline median | Baseline positive | Candidate median | Candidate positive |
|---|---:|---:|---:|---:|
| T+1 | 0.0000% | 46.91% | 0.0000% | 46.87% |
| T+3 | 0.0000% | 48.90% | 0.0000% | 49.09% |
| T+5 | 0.0000% | 49.92% | 0.0137% | 50.03% |

No meaningful raw short-horizon outcome separation is established by this structural-only comparison.

## Interpretation boundary

Cycle 1 establishes two useful facts:

1. `TF-SMA-STRUCT-01` is structurally much broader than the current EMA+Stage2 gate.
2. Simply being in the candidate structural state does not, by itself, show a meaningful T+1/T+3/T+5 return advantage over the baseline state.

This does **not** establish that the candidate is inferior or superior as a trading filter because the comparison has not yet held the rest of the entry-ready signal construction constant. Repeated daily PASS rows are also not independent trade events.

## Governance decision after Cycle 1

- Current EMA contract: **UNCHANGED / PRODUCTION BASELINE**.
- TF-SMA-STRUCT-01: **REMAINS DEVELOPMENT-FROZEN / NOT VALIDATED**.
- No threshold tuning is authorized.
- No MA grid search is authorized.
- No production promotion is authorized.
- The candidate must not be altered in response to Cycle 1 results.

## Required next evidence

Proceed to an event-level treatment comparison where all non-trend signal logic is held constant and only the trend gate differs.

Minimum next study:
1. construct baseline entry-ready condition with current trend gate,
2. construct candidate entry-ready condition with `TF-SMA-STRUCT-01`,
3. hold liquidity, RS, price, regime, breakout, volume, and other non-trend conditions constant,
4. use independent False->True entry-ready onsets rather than repeated PASS rows,
5. measure executable T+1 open path, T+1 close, T+3, T+5, MFE, MAE,
6. compare both-pass, baseline-only, and candidate-only event populations,
7. segment by T-1->T0 extension/overextension where available,
8. do not change the frozen candidate after observing the results.

Only after this event-level development evidence is reviewed can a decision be made whether the candidate merits an untouched validation cycle.