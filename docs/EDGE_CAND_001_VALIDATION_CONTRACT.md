# EDGE-CAND-001 — Untouched Validation Contract

Status: **FROZEN BEFORE OOS RUN / NOT PRODUCTION-AUTHORIZED**

Development evidence: docs/EVIDENCE_EDGE_DECOMP_001.md

## Candidate
Post-breakout acceptance:
1. T0 must be a current TrendFoll independent entry-ready onset.
2. Observe T+1 close relative to the T0 prev_pivot_high.
3. Qualify iff T+1 close >= T0 prev_pivot_high.
4. Earliest executable candidate entry is T+2 Open.
5. No margin around pivot; no gap/momentum/volume/tightness threshold; no retest requirement.
6. Existing TrendFoll rolling-60D pivot only; no O'Neil/CAN SLIM morphology.

## Untouched holdout
Rank current READY security identities deterministically by SHA256(security_id|ticker), exactly as development sampling.

- development: ranks 1–100
- untouched validation: ranks 101–200
- no overlap permitted
- full canonical history and 500-bar pre-roll
- event onset detected on full stream before research_eligible restriction
- current READY membership caveat remains; this is untouched by security identity, not a point-in-time universe backtest

## Comparison
On the same untouched T0 onset corpus report:
- baseline T+1 Open→T+5/T+10 median and mean
- candidate accepted subset T+2 Open→T+5/T+10 median and mean
- candidate participation rate
- positive-return rate
- MFE10 / MAE10
- event count and unique symbols
- yearly counts/outcomes
- top-symbol concentration

This is not a portfolio backtest and does not compare current exit rules.

## Pre-registered interpretation
Candidate is **supported for further research** only if the untouched accepted subset:
- has at least 200 mature T+10 events and at least 25 unique symbols;
- median T+2→T+10 > 0;
- positive T+10 rate > 50%;
- median MAE10 is less adverse than baseline T+1 MAE10;
- direction is not dependent on one calendar year: among years with >=20 candidate events, at least 60% have non-negative median T+10;
- no single symbol contributes >10% of candidate events.

These are governance sufficiency gates, not optimized trading thresholds.

Failure of a gate means no production authorization and no post-hoc threshold repair in this candidate. Any new candidate requires a new contract.
