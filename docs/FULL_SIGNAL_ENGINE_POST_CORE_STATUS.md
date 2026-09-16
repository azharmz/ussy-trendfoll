# Full Signal Engine Audit — Post-Core Status

Status: **ACTIVE / CORE 10/10 FROZEN / PRODUCTION UNCHANGED**

Date: 2026-09-17

Branch: `research/exit-development-hypotheses`

## Purpose

This document synchronizes the Full Signal Engine Audit after `CORE_INDICATOR_AUDIT.md` reached 10/10 closure. The 269-item engineering checklist remains useful evidence and hardening inventory, but Core findings now control primitive semantics. Open checklist items must not mechanically reopen a Core component unless new contradictory evidence appears.

The remaining terminal objective is end-to-end correctness:

`R2 READY -> FEATURES/INDICATORS -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST -> ALERT/ACTIONABLE -> PRODUCTION ENTRY/EXIT`

## Frozen Core dispositions consumed by Full Audit

1. C01 terminal canonical EMA: retain current governed adj-close terminal state. Historical/local EMA consistency remains separate.
2. C02 Stage: retain as Weinstein-inspired approximation; do not claim full Weinstein morphology.
3. C03 RS vs SPY: retain 63-session adjusted-return excess-return definition; threshold/horizon optimization is separate research.
4. C04 Liquidity: split-sensitive raw share-volume state is a real mismatch; FSE-014 correction governance applies.
5. C05 nominal price floor: retain raw current-price rule; threshold optimization is separate research.
6. C06 ATR: ordinary formula valid, but raw split-sensitive ATR state requires separate correction governance. `vcp_tightness` must be treated as an inverse ATR-percentile/volatility-tightness proxy, not literal VCP.
7. C07 pivot/breakout: retain as prior-60-session trailing-high breakout; do not call it O'Neil/base pivot.
8. C08 breakout volume: retain as inclusive rolling-volume-rank confirmation; not canonical O'Neil volume-expansion semantics; inherits normalized-volume dependency.
9. C09 regime: retain internal SPY SMA50/SMA200 three-state regime; benchmark readiness/freshness remains a Full-Audit boundary.
10. C10 aggregation: preserve explicit dual contracts. Watchlist/actionability and production entry are not interchangeable.

## Reconciliation of stale Full-Audit statements

The existing detailed checklist still says FSE-014 requires a correction specification. That statement is stale. The correction contract has already been frozen and a research-only implementation exists at commit `5e0e91046c30165abeef02857435d5f553ee0c63`. Contract tests were added at `785c513f442a27971616af2122b5ecdbd5eb5a80`; the CI research gate at head `593e8f699494e7e155e95e1835eaf4e98f754056` completed successfully in run `35080840497`.

The FSE-014 contract keeps window=50, min_periods=20, and existing PASS/NEAR thresholds unchanged. For an evaluation row T0, historical raw share volume is expressed on the T0 share basis using only split factors effective in `(t,T0]`. Same-day reported volume is already on that day's post-event share basis. Future split events cannot alter historical as-of states. Unknown required split factors fail closed. Production feature code remains unchanged.

FSE-013 is also technically past the correction/validation stage: refined contract, regression, and untouched validation V2 are complete. Its remaining step is explicit production adoption/defer/reject governance, not more implementation tuning.

FSE-015 Sep-14 partial-volume incident is CLOSED/VERIFIED under its incident scope after upstream finalization protection and residual HUBB/SITC repair. Do not keep historical same-date reconciliation as a blocking TrendFoll remediation unless new contradictory evidence appears.

## Remaining production-relevant work after Core

### P1 — Production-decision queue

**FSE-013 effective-date lifecycle state**

Technical state: correction implemented on research branch, regression passed, untouched validation V2 passed. Remaining boundary: explicit production decision.

**FSE-014 split-normalized share-volume state**

Technical state: frozen contract + research implementation + contract tests + successful CI research gate. Before production decision, Full Audit should verify the production data contract can actually supply authoritative split factors with the required as-of semantics. The current R2 adapter's synthetic `stock_splits=0.0` cannot satisfy the correction contract by itself.

### P2 — Newly isolated Core remediation dependency

**ATR split-sensitive state**

C06 establishes a production-relevant corporate-action basis defect because raw OHLC true range can interpret a split discontinuity as volatility and the recursive ATR state affects production stop distance. This requires its own correction contract; it must not be silently folded into FSE-014 because the data basis and downstream risk semantics differ.

### P3 — Benchmark readiness governance

C09 confirms the regime formula is causal, but stock state is governed by R2 READY while SPY/other benchmark state is downloaded live. FSE-007 therefore remains an ingestion/readiness governance item. The needed decision is whether to add an explicit benchmark as-of/freshness guard or move benchmark state under a governed snapshot contract. This is architecture hardening, not formula tuning.

### P4 — Historical EMA consistency

Terminal production EMA is already canonical. Historical rows remain on the legacy finite-window/raw-close contract. This matters for historical lifecycle/research semantics but must not be confused with the already-correct terminal production state. Any remediation belongs to the separate legacy feature-engine standardization workstream unless Full Audit finds a current production consumer whose decision is materially affected by historical mixed-basis state.

## Non-blocking methodology research

The following open checklist questions are not blockers to signal-engine correctness under the frozen USSY definitions and should not be used to keep the audit artificially open:

- optimizing RS horizon or PASS/NEAR thresholds;
- optimizing liquidity/price thresholds;
- replacing Stage approximation with a fuller Weinstein model;
- replacing trailing-high breakout with O'Neil pattern morphology;
- replacing rolling-volume rank with O'Neil average-volume expansion;
- tuning ATR percentile/tightness threshold;
- frequency studies whose only purpose is strategy optimization rather than correctness.

They may be researched later as strategy-development workstreams.

## Immediate Full-Audit execution order

1. Verify FSE-014 upstream split-factor availability/lineage contract. If unavailable, record the production blocker explicitly; do not fake split factors in TrendFoll.
2. Freeze a separate C06/ATR corporate-action correction contract and build research-only tests/implementation; no production change.
3. Close FSE-007 benchmark freshness governance with an explicit detectable contract.
4. Reconcile the Full-Audit findings register and detailed checklist against Core 10/10 so stale methodology items are marked non-blocking rather than reopened.
5. Produce the correction decision matrix: FSE-013, FSE-014, ATR, benchmark readiness, and any truly production-relevant historical EMA dependency.
6. Only after those gates, proceed to explicit production adoption/defer/reject decisions and full regression/untouched validation as applicable.

## Current terminal state

- Core Indicator Audit: **CLOSED 10/10**.
- Full Signal Engine Audit: **ACTIVE**.
- Production code: **UNCHANGED by Core/post-Core synchronization**.
- Next executable technical blocker: **FSE-014 authoritative split-factor availability/lineage**.
