# Full Signal Engine Audit — Evidence 02

Status: **DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## PROB-018 — R2 Trend Warm-up empirical result

GitHub Actions run: `35033214226`  
Job: `104596286912`  
Result: **SUCCESS**  
R2 snapshot: `2026-08-28`  
Universe: 1,227 READY securities  
Deterministic audit sample: 100 securities  
Reference: yfinance 5y  
Overlap observations: 29,907  
Source-matched observations (0.25% close tolerance): 29,818  
Source mismatch observations: 89

### Terminal/latest comparable bar

| Metric | Result |
|---|---:|
| Symbols | 100 |
| EMA-stack disagreement | 1.00% |
| Stage disagreement | 0.00% |
| Trend-status disagreement | 1.00% |
| EMA20 median abs error | ~0% |
| EMA20 p95 abs error | ~0% |
| EMA50 median abs error | 0.000030% |
| EMA50 p95 abs error | 0.003555% |
| EMA150 median abs error | 0.176275% |
| EMA150 p95 abs error | 9.057128% |
| EMA200 median abs error | 0.586994% |
| EMA200 p95 abs error | 22.635004% |

### Disagreement by age inside the finite R2 window

| Age | EMA-stack | Stage | Trend status |
|---|---:|---:|---:|
| 1–50 | 26.58% | 89.22% | 15.78% |
| 51–100 | 10.22% | 94.22% | 17.74% |
| 101–150 | 6.84% | 95.98% | 22.34% |
| 151–200 | 5.22% | 7.68% | 6.54% |
| 201–250 | 2.14% | 0.00% | 2.14% |
| 251+ | 0.934% | 0.00% | 0.934% |

## Interpretation

1. The finite R2 history is **not historically equivalent** to a long-history reference. Early historical rows are materially warm-up contaminated, especially for Stage and long EMAs.
2. The contamination decays strongly with age. By the terminal observation, Stage classification matched the reference in all 100 audited symbols.
3. Terminal Trend is substantially more robust than early historical Trend, but is **not perfectly invariant**: 1/100 audited symbols disagreed.
4. Long EMA numerical error remains heterogeneous even at the terminal row. EMA200 p95 absolute error of 22.64% is too large to treat a finite-window EMA200 as a canonical long-history value.
5. This empirically supports the existing architecture that replaces terminal EMA state with canonical R2 EMA values. It does **not** validate historical finite-window EMA rows for backtesting or retrospective lifecycle reconstruction.
6. Therefore PROB-018 is classified as: **REAL HISTORICAL WARM-UP EFFECT / TERMINAL MITIGATION PRESENT / HISTORICAL USE REQUIRES EXPLICIT WARM-UP GOVERNANCE**.

No production rule is changed by this finding.

## Audit consequence

- Terminal production classification: continue audit; no emergency production change justified by PROB-018 alone.
- Historical studies: must exclude/repair warm-up-contaminated rows or use canonical long-history features.
- Any lifecycle reconstruction using historical feature rows must state whether those rows are canonical or finite-window-derived.
- `pct_off_52w_high` remains separately suspect because its nominal 252-session semantic can be emitted with `min_periods=20`; PROB-018 does not validate that feature.

Artifact from run: `prob-018-trend-warmup-2` (artifact ID `10421814875`, SHA256 `e963e72748b3cfb05dbb585509d54f629958c6b65e37fc0a5db6afcbd9a2bfef`).