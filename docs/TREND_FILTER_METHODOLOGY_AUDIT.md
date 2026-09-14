# Trend Filter Methodology Audit — O'Neil / CAN SLIM Adaptation

Status: **RESEARCH NOTE / DEVELOPMENT INPUT / NO PRODUCTION CHANGE**

## Research question

For TrendFoll, which moving-average representation is methodologically justified for structural trend qualification when adapting the O'Neil/CAN SLIM family to short-to-medium swing trading?

This audit is **not** a parameter search and does not ask which moving-average combination produces the best backtest. It first identifies candidate rules supported by the source methodology, then permits a governed empirical comparison.

## Source evidence

Authoritative/first-party O'Neil/IBD material repeatedly treats the following as distinct technical horizons:

- **50-day moving average (50-DMA)**: an important intermediate trend/support line. O'Neil/IBD material routinely discusses stocks and indices holding, reclaiming, or breaking the 50-DMA.
- **200-day moving average (200-DMA)**: a major long-term trend/support line. O'Neil material routinely distinguishes names above versus below the 200-DMA.
- **10-day moving average**: a shorter tactical line used for active trade management.
- **21-day exponential moving average (21-EMA)**: IBD explicitly describes this as a faster/intermediate trade-management line between the 10-day and 50-day horizons.
- SwingTrader explicitly states that it adapts CAN SLIM/IBD methodology, originally designed mainly for position trading, to a shorter swing-trading environment.

The evidence therefore does **not** support treating all moving averages as interchangeable or selecting EMA solely because it is more responsive. Structural trend qualification and tactical trade management should be separated.

## Important terminology boundary

In O'Neil/IBD material, `DMA` is used for day moving-average lines. Where the source explicitly identifies a simple moving average, this audit treats it as SMA. The 21-day line is explicitly documented by IBD as an **EMA**. Therefore this project must not silently convert every O'Neil moving-average reference into EMA.

## Current TrendFoll production baseline

Current stock trend contract:

`close > EMA20 > EMA50 > EMA150 > EMA200`

plus weekly Stage2 based on a 30-week simple moving average.

This remains the production baseline. This audit does not authorize its replacement.

## Methodology-derived candidate contract

### Candidate TF-SMA-STRUCT-01 — structural qualification

A deliberately minimal O'Neil-aligned structural candidate for development testing:

1. `close > SMA50`
2. `SMA50 > SMA200`
3. `SMA200 slope > 0`

The slope must be specified before testing using a fixed, non-optimized lookback. It must not be selected by searching multiple slope windows for performance.

Rationale:

- 50-DMA and 200-DMA are repeatedly used by O'Neil/IBD as intermediate and long-term structural levels.
- Requiring price above 50-DMA, 50-DMA above 200-DMA, and a rising 200-DMA represents a mature structural uptrend without importing the current EMA20/50/150/200 stack.
- SMA200 is finite-window deterministic: once 200 observations exist, earlier history cannot change the same-date SMA200 value.

### Tactical lines are NOT part of TF-SMA-STRUCT-01

10-day SMA and 21-day EMA are reserved for separate research into:

- pullback/support behavior,
- trade management,
- exit/give-back,
- short-horizon swing adaptation.

They must not be added to structural qualification merely because they appear in O'Neil/IBD material.

## Weekly Stage relationship

The existing TrendFoll Stage2 implementation uses a 30-week SMA. That is a separate inherited feature and is **not automatically part of the O'Neil-derived SMA candidate**.

A 40-week line is approximately the weekly analogue of a 200-day line, but no replacement is authorized here. Any weekly structural rule must have its own evidence and frozen definition before testing.

## Development comparison design

The first governed comparison should be small and interpretable:

- **Baseline:** current production `EMA20/50/150/200 + Stage2` trend gate.
- **Candidate:** `TF-SMA-STRUCT-01`.

Do not add a grid of SMA20/50/100/150/200, EMA variants, or crossover permutations.

Evaluate at minimum:

1. coverage / selectivity,
2. overlap and disagreement with current production Trend PASS,
3. independent entry-ready onset count,
4. T+1 executable path,
5. T+3 / T+5 path,
6. MFE / MAE,
7. sensitivity to T-1 -> T0 overextension,
8. regime segmentation where available,
9. stability across symbols and time.

The objective is not to maximize CAGR on the development sample. The candidate must show coherent structural behavior and robustness before it can be frozen for untouched validation.

## Production/readiness implication

If TF-SMA-STRUCT-01 eventually survives development and untouched validation, it has an architectural advantage for the current R2 readiness contract:

- SMA50 requires exactly 50 prior closes.
- SMA200 requires exactly 200 prior closes.
- A 300-bar production readiness window can therefore compute these levels without recursive initialization ambiguity, subject to whatever fixed SMA200-slope lookback is frozen.

This is a secondary engineering benefit, **not the reason to choose the strategy**. Methodological and empirical validation comes first.

## Governance decision

- Current EMA contract: **UNCHANGED / PRODUCTION BASELINE**.
- TF-SMA-STRUCT-01: **METHODOLOGY-SUPPORTED DEVELOPMENT CANDIDATE / NOT VALIDATED**.
- 10-SMA / 21-EMA: **TACTICAL RESEARCH VARIABLES, NOT STRUCTURAL GATE**.
- No brute-force moving-average optimization is authorized.
- No production change is authorized from this audit.

## Next evidence

Before development backtesting, freeze the exact SMA200 slope definition from a methodological rationale rather than performance optimization. Then run one baseline-vs-candidate development comparison using long-history OHLCV with proper warm-up and T+1-executable outcome measurement.