# Trend Filter Methodology Audit — O'Neil / CAN SLIM Adaptation

Status: **RESEARCH NOTE / DEVELOPMENT-FROZEN CANDIDATE / NO PRODUCTION CHANGE**

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

Frozen development candidate:

1. `close > SMA50`
2. `SMA50 > SMA200`

Equivalent expression:

`close > SMA50 > SMA200`

This candidate is deliberately minimal. It uses only structural relationships that are directly and repeatedly supported by O'Neil/IBD methodology.

### Why `SMA200 rising` is NOT a gate

The initial research note proposed adding `SMA200 slope > 0`, with the slope lookback to be frozen before testing. Further methodology audit did not identify an authoritative O'Neil/IBD rule that specifies an exact lookback such as 5, 10, 20, or 30 trading days for a rising 200-DMA requirement.

Therefore no slope lookback will be invented or selected from performance results. `SMA200 rising` is removed from the candidate gate rather than assigning an arbitrary window.

If later authoritative evidence specifies a slope rule, it must enter as a new evidence-backed candidate and go through a separate development/validation cycle.

This is a governance decision: **absence of an exact source rule is not permission to optimize one.**

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

The first governed comparison is frozen as:

- **Baseline:** current production `EMA20/50/150/200 + Stage2` trend gate.
- **Candidate:** `TF-SMA-STRUCT-01 = close > SMA50 > SMA200`.

Do not add a grid of SMA20/50/100/150/200, EMA variants, crossover permutations, or slope lookbacks.

Hold all non-trend logic constant wherever the comparison reaches full signal construction. The trend representation is the treatment variable.

Evaluate at minimum:

1. coverage / selectivity,
2. overlap and disagreement with current production Trend PASS,
3. independent entry-ready onset count with all non-trend conditions held constant,
4. T+1 executable path,
5. T+3 / T+5 path,
6. MFE / MAE,
7. sensitivity to T-1 -> T0 overextension,
8. regime segmentation where available,
9. stability across symbols and time.

The objective is not to maximize CAGR on the development sample. The candidate must show coherent structural behavior and robustness before it can be frozen for untouched validation.

## Historical-data contract for comparison

The development comparison must use long-history OHLCV with a proper warm-up. It must not use the 300-bar R2 readiness window as the complete historical backtest dataset.

Required separation:

`long-history OHLCV -> feature warm-up -> evaluation start -> signal/outcome comparison`

Pre-evaluation history is context only and must not count as evaluated trades or outcomes.

## Production/readiness implication

If TF-SMA-STRUCT-01 eventually survives development and untouched validation, it has an architectural advantage for the current R2 readiness contract:

- SMA50 requires exactly 50 closes.
- SMA200 requires exactly 200 closes.
- A 300-bar production readiness window can therefore compute both levels exactly from the same final 200 observations as a much longer history, assuming identical adjusted/raw price treatment.

This is a secondary engineering benefit, **not the reason to choose the strategy**. Methodological and empirical validation comes first.

## Governance decision

- Current EMA contract: **UNCHANGED / PRODUCTION BASELINE**.
- TF-SMA-STRUCT-01: **DEVELOPMENT-FROZEN / METHODOLOGY-SUPPORTED / NOT VALIDATED**.
- Frozen candidate: **`close > SMA50 > SMA200`**.
- `SMA200 rising`: **NOT INCLUDED — exact slope horizon not established by authoritative evidence**.
- 10-SMA / 21-EMA: **TACTICAL RESEARCH VARIABLES, NOT STRUCTURAL GATE**.
- No brute-force moving-average optimization is authorized.
- No production change is authorized from this audit.

## Next evidence

Implement one baseline-vs-candidate development comparison using long-history OHLCV with proper warm-up and T+1-executable outcome measurement. Do not change the frozen SMA candidate after viewing development results; any materially different candidate requires a new hypothesis and evidence trail.