# EVIDENCE — PROB-018 R2 Trend Feature Warm-up Validity

Status: **OBSERVATIONAL EVIDENCE / NO PRODUCTION RULE CHANGE**

Run: GitHub Actions `PROB-018 Trend Warmup Audit` run #1, ID `34807966315`  
Head: `3fcfdf72161d6cbce50a056cfbc2ebe90a2d0eef`  
Artifact: `prob-018-trend-warmup-1`, ID `10334110579`  
Artifact SHA256: `2581efc5d247f597c2ccb5ba46cef294f5c090043fe80931ab9c9a54512b133c`

## Question

Does the approximately 300-bar R2 stock history reproduce the current TrendFoll trend feature contract closely enough to support current scanning and historical research?

Current contract under audit:

- EMA20
- EMA50
- EMA150
- EMA200
- `close > EMA20 > EMA50 > EMA150 > EMA200`
- 30-week moving average and weekly stage
- downstream `trend_status` from EMA-stack alignment + Stage2

The audit does **not** search for better moving averages and does not tune any production rule.

## Method

A deterministic SHA256-ranked sample of 100 symbols was selected from the 1,226-security R2 readiness universe. For each symbol:

1. Compute the current trend formulas from the finite R2 window.
2. Fetch a substantially longer 5-year yfinance reference history.
3. Compute the same formulas on the reference history.
4. Compare only identical symbol/date observations.
5. Separate likely source-data disagreement from warm-up disagreement using a 0.25% raw-close compatibility guard. This guard is an audit/data-comparability tolerance, not a trading threshold.
6. Measure numerical EMA error and, more importantly, decision disagreement for EMA-stack, weekly stage, and `trend_status` by R2 bar age.

The reference source is deliberately external to the R2 finite window. The test therefore asks whether starting the recursive/rolling indicators at the beginning of the finite R2 history changes the same-date feature decision.

## Coverage

- R2 snapshot: `2026-08-28`
- Universe: 1,226 symbols
- Deterministic sample requested: 100
- Successful comparisons: 100 / 100
- Overlap observations: 29,901
- Source-compatible observations: 29,900
- Source mismatches: 1

The extremely high raw-price compatibility materially reduces the risk that the result is merely a vendor-price comparison.

## Latest comparable bar per symbol

Across all 100 sampled symbols at their latest comparable observation:

| Metric | Result |
|---|---:|
| EMA-stack disagreement | **0.00%** |
| Stage disagreement | **0.00%** |
| Trend-status disagreement | **0.00%** |
| EMA20 median abs error | effectively 0% |
| EMA50 median abs error | 0.000032% |
| EMA150 median abs error | 0.1641% |
| EMA200 median abs error | 0.5727% |
| EMA150 p95 abs error | 9.3187% |
| EMA200 p95 abs error | 22.7450% |

### Interpretation

For the **current/latest scan**, this sample gives strong evidence that the finite R2 history is presently producing the same categorical trend decision as the long-history reference, despite a long tail of numerical EMA150/EMA200 initialization error.

This is important: numerical equality is not required for the current scanner if the downstream decision is unchanged. However, the large p95 EMA150/EMA200 errors show that it would be unsafe to infer that the long-period EMA values themselves are fully converged for every symbol.

## Historical disagreement by R2 bar age

| R2 bar age | EMA-stack disagreement | Stage disagreement | Trend-status disagreement | EMA150 median abs error | EMA200 median abs error |
|---|---:|---:|---:|---:|---:|
| 1–50 | 24.08% | 89.02% | 15.64% | 8.89% | 10.80% |
| 51–100 | 11.38% | 94.10% | 18.08% | 4.18% | 6.24% |
| 101–150 | 5.94% | 95.92% | 21.76% | 2.11% | 3.77% |
| 151–200 | 5.42% | 1.94% | 5.68% | 1.05% | 2.27% |
| 201–250 | 2.14% | 0.00% | 2.14% | 0.53% | 1.33% |
| 251+ | 0.96% | 0.00% | 0.96% | 0.26% | 0.78% |

The extreme Stage disagreement before roughly 150 bars is expected from the 30-week rolling requirement: the long-history reference already has mature weekly context while the finite R2 window does not. The key point is that the production feature code can still emit values/statuses in parts of the finite window where the historical context is not equivalent to the long-history calculation.

## Verdict for PROB-018

### Current scanner

**SUPPORTED FOR CURRENT-END TREND CLASSIFICATION, subject to continued monitoring.**

On this deterministic 100-symbol sample, the latest categorical EMA-stack, Stage and `trend_status` decisions agree 100% with the long-history reference.

This does **not** mean EMA150/EMA200 numerical values are universally converged; the p95 error remains large for a minority of names.

### Historical backtest / diagnostics

**R2 300-bar history is NOT valid as a full 300-bar backtest window for the current trend contract.**

The first ~150 bars have severe weekly-stage warm-up contamination and material trend-status disagreement. Even at 201–250 bars the observed trend-status disagreement is 2.14%, and at 251+ it remains 0.96% across historical observations.

Therefore the project must not treat all 300 R2 bars as equally valid feature history merely because pandas returns an EMA or Stage value.

## Governance consequence

1. Do **not** remove or retune EMA20/50/150/200 based on this audit.
2. Production latest-day scanning may continue under the current feature contract; the sample found no latest decision disagreement.
3. Development backtests and historical attribution must **not** use the whole finite R2 window without a warm-up contract.
4. Because a conservative warm-up would consume most of a 300-bar dataset, the preferred research solution is to provide **longer historical OHLCV / explicit pre-roll history**, rather than pretending the early R2 bars are valid or shrinking the trend model to fit the data.
5. A separate implementation decision should define the research/backtest history contract (e.g. additional pre-roll history that is used for feature initialization but excluded from the evaluated period).
6. Existing DIAG-001 remains useful observational evidence, but any conclusions dependent on early-window trend classification must be treated cautiously until rebuilt under a valid pre-roll contract.

## What this evidence does not authorize

- No production signal threshold changes.
- No moving-average replacement.
- No exit-rule change.
- No claim of profitability.
- No arbitrary declaration that a particular bar count is universally sufficient.

The next architectural task is to define a **feature pre-roll / research history contract** that preserves the R2 readiness universe while giving long-period trend features sufficient prior history for backtesting and diagnostics.
