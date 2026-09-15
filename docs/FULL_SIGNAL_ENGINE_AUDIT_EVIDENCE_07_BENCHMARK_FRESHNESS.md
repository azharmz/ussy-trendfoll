# Full Signal Engine Audit — Evidence 07: Benchmark Freshness

Status: **DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Empirical run

GitHub Actions run: `35034595865`  
Job: `104600702249`  
Conclusion: **SUCCESS**  
Audit branch head: `e1dc3e6a3cd05cf0a77be088a52222571dd43a59`  
Artifact: `signal-engine-benchmark-freshness-1`  
Artifact ID: `10423305549`  
Artifact SHA256: `ba8b29f1487cf53264b605b83af176ae2f01e267a68e70d361579cf455452426`

## R2 state observed

- R2 snapshot date: `2026-08-28`
- R2 latest market date: `2026-09-14`
- Distinct R2 dates: `333`

The snapshot label and latest contained market date are separate concepts; this run explicitly measured benchmark alignment against the actual latest R2 market date.

## Benchmark inventory checked

`SPY`, `QQQ`, `^VIX`, `XLK`, `XLV`, `XLY`, `XLP`, `XLE`, `XLI`, `XLB`, `XLU`, `XLC`, `XLRE`.

All 13 benchmark/context series returned status `OK` in the empirical audit.

## SPY decision-relevant freshness

Observed:

- SPY latest date: `2026-09-15`
- exact SPY row exists for R2 latest date `2026-09-14`: **YES**
- R2 dates missing from SPY across the audited R2 window: **0**
- RS exact-date merge latest safe: **YES**
- backward-as-of regime source for R2 latest date: `2026-09-14`

Therefore the currently observed R2 state is not ahead of the decision-relevant SPY series. The exact-date RS contract has complete SPY coverage across all R2 dates in this audit, and the regime as-of merge resolves to same-date SPY state at the R2 terminal observation.

Classification for the observed state: **MATCH / EMPIRICALLY FRESH**.

## Other benchmarks

QQQ, VIX and all sector ETFs also contained the exact R2 latest date and had zero missing R2 dates across the audited window. Their latest available date was `2026-09-15`, one calendar day beyond the latest R2 market date.

This benchmark-ahead condition is benign under the traced merge contracts because:

- exact-date joins cannot import a future benchmark row into an earlier stock date;
- backward-as-of joins select same/prior benchmark observations, not future observations.

Classification: **MATCH** for the observed benchmark-ahead scenario.

## What this closes

The empirical run closes the current-state uncertainty behind FSE-007. There is no observed stale/misaligned benchmark defect in the audited R2 state.

However, this does **not** establish a preventive production readiness contract. Stock data and benchmark data still arrive through separate ingestion paths. A future R2-ahead-of-SPY state remains architecturally possible unless production explicitly detects it.

Therefore distinguish:

1. **Current empirical state:** `MATCH / EMPIRICALLY FRESH`.
2. **Preventive freshness guard:** still a governance/design question, not evidence of a current bug.

No production change is authorized by this evidence alone.
