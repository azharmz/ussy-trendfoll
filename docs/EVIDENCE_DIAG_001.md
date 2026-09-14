# EVIDENCE — DIAG-001 Signal-to-Outcome Funnel

> **Historical record / superseded for causal interpretation.** This run used the rolling ~300-bar feature history before PROB-019 was resolved. The governed valid-history rebuild is `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md` and must be used for current historical interpretation. This file is retained for provenance and comparison only.

Status: **OBSERVATIONAL EVIDENCE / SUPERSEDED BY VALID-HISTORY REBUILD / NO PRODUCTION CHANGE AUTHORIZED**

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

Interpretation recorded at the time: stronger T-1 -> T0 moves appeared associated with larger subsequent excursion in both directions and negative median T+5 in the upper half. **This directional T+5 interpretation is not reproduced by the governed valid-history rebuild and is superseded.**

## Descriptive T0 -> T+1 opening-gap quartiles

Again, these are descriptive quantiles only.

| Gap bucket | Median gap | Median T+5 return | T+5 positive rate | Median MAE T+5 |
|---|---:|---:|---:|---:|
| Q1, largest gap-down | -1.49% | -1.69% | 40.5% | -5.75% |
| Q2, mild gap-down | -0.24% | +0.87% | 55.0% | -3.50% |
| Q3, mild gap-up | +0.45% | +0.46% | 53.1% | -3.50% |
| Q4, largest gap-up | +1.93% | -0.97% | 43.5% | -6.11% |

The original symmetric extreme-gap interpretation is also not reproduced by the governed rebuild. See `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md`.

## Regime limitation

All DIAG-001 entry-ready events in this historical sample were `Bullish / PASS` at the regime gate. Therefore this run cannot diagnose regime dependence; `PROB-014` remains open.

## Governance conclusion

This file no longer supports current causal conclusions about historical signal-day momentum or T+5 decay. It remains useful only as evidence of why PROB-018/019 mattered and as provenance for the diagnostic evolution.
