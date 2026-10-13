# DIAG-002 — Entry Attribution Evidence

Status: **COMPLETED / OBSERVATIONAL ONLY / NO PRODUCTION CHANGE**

- Workflow: [DIAG-002 Run #5](https://github.com/azharmz/ussy-trendfoll/actions/runs/38387741419)
- Commit: `2787d89b197fe86ba6a5ce16467bdfbcc0dd5ccb`
- Contract: `docs/DIAG_002_ENTRY_ATTRIBUTION_CONTRACT.md`
- Snapshot: `2026-08-28`
- Sample: deterministic SHA256-ranked 100 securities from current R2 readiness universe.
- History: `history/ohlcv/{security_id}.parquet`; 500-bar pre-roll; canonical EMA uses `adj_close`.
- Output artifact: `diag002-entry-attribution-5` (summary JSON and event CSV).

## Coverage and outcome baseline

- 100 securities requested and loaded; 87 had eligible history.
- 470,890 eligible decision rows; 1,610 full-history entry-ready onsets; 1,545 eligible independent onsets.
- 1,544 of 1,545 events had a mature T+5 close outcome.
- Event dates span 1993-12-08 through 2026-08-25; the 1,545 events come from 60 securities.
- Median T+1-open to T+5-close return: **+0.151%**; T+5 positive rate: **51.36%**.
- Median MFE5: **+2.57%**; median MAE5: **-2.50%**.

The events are not independent IID observations: securities contribute repeated onsets (top five symbols account for 22.3% of events). Treat these summaries as descriptive; do not read the event count as an equivalent independent sample size.

## Pre-registered continuous components

All correlations below are Spearman rho against the named outcome. Quantile groups are descriptive and are not candidate thresholds.

| Component | rho vs T+5 return | rho vs MFE5 | rho vs MAE5 | Interpretation |
|---|---:|---:|---:|---|
| T-1 to T0 raw-close return | +0.011 | +0.232 | -0.210 | No monotonic T+5-return separation; stronger signal-day momentum is associated with wider upside and downside excursions. |
| T0 pivot extension (ATR units) | +0.059 | +0.044 | +0.026 | Weak T+5 association; quartile medians are non-monotonic. No extension cap justified. |
| T0 close to T+1 open gap | -0.060 | -0.066 | -0.072 | Weak overall association. The highest signed-gap quartile (median gap +0.96%) has median T+5 -0.10%, positive rate 48.7%, and MAE5 -3.09%. |
| Breakout volume percentile | +0.024 | +0.065 | -0.041 | No clear monotonic T+5 separation; descriptive quartile results are mixed/non-monotonic. |
| VCP tightness | +0.026 | -0.141 | +0.149 | Little T+5-return separation; higher tightness is associated with smaller MFE and less adverse MAE in this sample, not a demonstrated return edge. |

Among positive-gap events only (N=729), gap-vs-T+5 rho is -0.019. Its highest gap quartile (median gap +1.71%) has median T+5 -0.33%, positive rate 47.3%, MFE5 +3.33%, and MAE5 -3.77%. This remains an observational execution-quality hypothesis, not a cutoff recommendation.

## Categorical/context components

- `has_tight_structure=True` (N=234): median T+5 +0.229%, positive rate 55.1%, MFE5 +2.13%, MAE5 -2.08%.
- `has_tight_structure=False` (N=1,311): median T+5 +0.093%, positive rate 50.7%, MFE5 +2.73%, MAE5 -2.57%.

This is modest descriptive separation with mixed excursion behavior; it is not evidence to change the entry gate.

Investability, trend, liquidity, RS, price, regime status, and market regime were non-identifiable in this event corpus: all entry-ready onsets had hard-filter PASS and market regime Bullish. This is a selection-by-construction limitation, not evidence that those components have no effect. Regime and Investability attribution require a separately defined candidate corpus that retains observations before those gates.

## Limitations

1. Universe membership is current R2 readiness, not historical point-in-time membership; survivorship bias is not eliminated.
2. Repeated events are clustered by security; the descriptive correlations do not account for within-symbol dependence.
3. Results are univariate/descriptive. They do not establish causality, incremental value, profitability after costs, or a production-ready rule.
4. Quantile bins are descriptive only. No threshold search, parameter tuning, or strategy change is authorized.

## Decision

**DIAG-002 pipeline and tests PASS.** Entry attribution does not establish a strong monotonic T+5 edge in the pre-registered continuous components. Signal-day momentum is more clearly associated with excursion dispersion than with T+5 return; positive opening gaps remain a weak risk/execution hypothesis; tight structure has modest descriptive separation. No production entry, exit, filter, regime, alert, or threshold changes are authorized.

## Next diagnostic

Proceed to DIAG-003 Exit Conversion / Give-back under the frozen current exit contract: stop at 2 ATR below realistic T+1 open (intraday low trigger, stop-price fill assumption), EMA20 close exit, and 45-trading-day maximum. Measure early failure, time-to-MFE, realized exit versus MFE/MAE, give-back, EMA20-loss timing, and the day-45 counterfactual. Keep position-history integrity separate from the full historical reconstruction.
