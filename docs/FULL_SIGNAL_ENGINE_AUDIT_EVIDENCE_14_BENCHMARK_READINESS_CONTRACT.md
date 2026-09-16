# Full Signal Engine Audit — Evidence 14: Benchmark Readiness Contract

Status: **GOVERNED READINESS CONTRACT FROZEN + RESEARCH TEST PASS / PRODUCTION INTEGRATION PENDING / NO PRODUCTION CHANGE**

Date: 2026-09-17

## Context

Evidence 07 established that the observed benchmark state was empirically fresh: SPY had exact-date coverage for the R2 terminal date and across the audited R2 window. It also identified an architectural gap: stock facts and benchmark facts arrive through separate ingestion paths, so a future R2-ahead-of-SPY state remains possible without a preventive readiness guard.

The actual consumers make the minimum safe contract unambiguous:

- stock RS uses an exact-date SPY observation;
- market regime uses same/prior SPY state through backward-as-of;
- SPY rows after stock T0 cannot leak through either contract.

Because RS is decision-relevant and exact-date, production readiness must fail closed when the stock T0 date lacks an exact SPY row. Allowing stale SPY for regime cannot rescue missing exact-date RS input.

## Frozen contract

For production stock as-of date T0:

1. SPY must be available;
2. SPY must contain an exact T0 observation;
3. regime may resolve only to SPY date <= T0;
4. SPY observations after T0 are benign and must not affect T0 state;
5. an R2-ahead-of-SPY terminal state fails closed rather than silently producing a partial/stale decision state.

Research implementation: `benchmark_readiness.py`.

## Contract tests

`tests/test_benchmark_readiness.py` covers:

- same-day SPY readiness;
- R2-ahead-of-SPY fail-closed;
- SPY-ahead-of-R2 benign behavior;
- future SPY row cannot rescue a missing exact T0 row;
- unavailable SPY fail-closed.

Workflow: `.github/workflows/audit-benchmark-readiness-contract.yml`.

Run `35164057505`, job `105021059280`: **SUCCESS**. Frozen benchmark readiness contract tests passed.

## Finding disposition

FSE-007 is now split cleanly into:

- observed benchmark state: **MATCH / EMPIRICALLY FRESH** (Evidence 07);
- preventive readiness architecture: **GOVERNED CONTRACT REQUIRED**, now frozen and research-tested;
- current production implementation: no explicit fail-closed benchmark readiness gate yet.

This is not evidence that historical/current production emitted a known wrong decision due to stale SPY. It is a preventive correctness gap at the independently ingested benchmark boundary.

## Production decision

No production change is made in this audit step. Integration of the frozen guard remains an explicit production decision and must be followed by regression of the complete R2-to-decision path.

## Verdict

- Current observed freshness: **MATCH**.
- Temporal semantics of exact-date RS and backward-as-of regime: **PASS**.
- Preventive readiness contract: **FROZEN + TEST PASS**.
- Production guard: **PENDING PRODUCTION DECISION**.
- Threshold/model tuning: **NONE**.