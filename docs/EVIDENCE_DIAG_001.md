# EVIDENCE — DIAG-001 Signal-to-Outcome Funnel

Status: **OBSERVATIONAL EVIDENCE / NO PRODUCTION CHANGE AUTHORIZED**

Source run: GitHub Actions `DIAG-001 Signal Path Evidence` run #1, run id `34803838276`.
R2 ready snapshot: `2026-08-28`.

## Coverage

- Decision rows: 367,203
- Independent entry-ready onset events: 845
- Mature through T+1: 845
- Mature through T+3: 842
- Mature through T+5: 837
- Linked Supabase forward positions: 24
- Supabase position rows observed: 27
- Duplicate `(symbol, entry_date)` position keys: 1 (`ANF`, `2026-08-26`)

## Whole-sample medians

| Metric | Median |
|---|---:|
| T-1 -> T0 return | +5.50% |
| T0 pivot extension | +0.54 ATR |
| T0 close -> T+1 open gap | +0.03% |
| T+1 open -> T+1 close | +0.13% |
| T+1 open -> T+3 close | +0.03% |
| T+1 open -> T+5 close | -0.27% |
| T+1-open anchored MFE through T+5 | +4.67% |
| T+1-open anchored MAE through T+5 | -4.71% |
| Linked-position realized return | -6.09% |

The T0 -> T+1 opening gap is near zero at the median, so the current evidence does **not** support overnight gap alone as the primary explanation for poor realized outcomes.

## Descriptive T-1 -> T0 momentum quartiles

These are descriptive quantiles only; they are **not production thresholds**.

| T-1 -> T0 bucket | Median move | Median T+5 return | T+5 positive rate | Median MFE T+5 | Median MAE T+5 |
|---|---:|---:|---:|---:|---:|
| Q1 | +2.05% | +0.15% | 51.0% | +3.15% | -3.15% |
| Q2 | +4.31% | +0.74% | 52.6% | +4.43% | -4.00% |
| Q3 | +7.17% | -0.63% | 44.0% | +4.91% | -5.59% |
| Q4 | +13.82% | -1.12% | 44.5% | +6.50% | -7.92% |

Interpretation: stronger T-1 -> T0 moves are associated with larger subsequent excursion in **both** directions. Upside opportunity increases, but downside excursion deteriorates more strongly; median T+5 return turns negative in the upper half of the momentum distribution.

## Descriptive T0 -> T+1 opening-gap quartiles

Again, these are descriptive quantiles only.

| Gap bucket | Median gap | Median T+5 return | T+5 positive rate | Median MAE T+5 |
|---|---:|---:|---:|---:|
| Q1, largest gap-down | -1.49% | -1.69% | 40.5% | -5.75% |
| Q2, mild gap-down | -0.24% | +0.87% | 55.0% | -3.50% |
| Q3, mild gap-up | +0.45% | +0.46% | 53.1% | -3.50% |
| Q4, largest gap-up | +1.93% | -0.97% | 43.5% | -6.11% |

Interpretation: both gap extremes look weaker than the middle buckets. This is evidence for a possible execution-quality effect, but not enough to define a cutoff.

## Regime limitation

All DIAG-001 entry-ready events in this historical sample were `Bullish / PASS` at the regime gate. Therefore this run cannot diagnose regime dependence; `PROB-014` remains open.

## Governance conclusion

DIAG-001 supports continuing diagnosis around:
- signal-day overextension / volatility expansion,
- early post-entry fade between T+1 and T+5,
- execution quality at extreme overnight gaps,
- exit behavior for the forward-position subset.

It does **not** authorize a new momentum threshold, gap threshold, entry delay, stop change, or exit change.
