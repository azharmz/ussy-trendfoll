# Full Signal Engine Audit — Detailed Progress Checklist

Status: **ACTIVE TERMINAL CLOSURE / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

Companion audit: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose and completion rule

This document is the operational ledger for the full USSY TrendFoll signal-engine correctness audit. The original 269-item engineering checklist remains useful evidence, but after completion of the 10/10 Core Indicator Audit it is **not** a mechanical 269/269 production-closure target.

Terminal closure is governed by the actual production path:

`R2 READY -> FEATURES/INDICATORS -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST -> ALERT/ACTIONABLE -> PRODUCTION ENTRY/EXIT`

A remaining item blocks closure only when it can materially change production correctness, temporal semantics, persisted decision state, or the interpretation of an authoritative production output. Methodology optimization, threshold tuning, optional historical forensics, and already-dispositioned approximation naming are non-blocking unless new evidence changes their classification.

## Governance gates — COMPLETE

- [x] Production behavior remained unchanged during audit/research cycles.
- [x] EXIT-CAND-003 remained outside the signal-engine decision path.
- [x] Controlled classifications used: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.
- [x] No suspicious result was promoted to bug without input/code/temporal/reproducibility checks.
- [x] Core Indicator Audit completed 10/10.
- [x] Independent C01-C04 review gate passed.
- [x] Sep-10 +61 diagnostic closed as explainable migration/universe expansion; do not reopen without contradictory evidence.
- [x] Sep-14 partial-volume incident/FSE-015 closed for TrendFoll scope; optional majority-self-heal provenance is not a signal-engine blocker.

## Production execution map — COMPLETE

- [x] Scheduled workflow and `r2_main.py` entry point traced.
- [x] R2 READY loader/schema/checksum/security-id validation traced.
- [x] R2-to-feature adapter and legacy feature-engine reuse traced.
- [x] Canonical terminal EMA overlay traced.
- [x] Hard filter and decision layer traced.
- [x] Common-date latest selection traced.
- [x] Candidate/watchlist, alert state, lifecycle, notification, production position entry/exit traced.
- [x] T0-close / T+1-open execution semantics traced.
- [x] Dual downstream contracts explicitly confirmed: watchlist/actionability != authoritative production-entry predicate.

## R2 input/readiness — MATERIAL CORRECTNESS COMPLETE

Evidence 09 measured 367,499 rows / 1,227 securities / 250-300 bars per security, with no duplicate `(security_id,date)`, no missing required facts, and no basic invalid OHLCV. READY finite-window semantics and the separate canonical long-history terminal EMA state are explicit.

- [x] Current READY history is sufficient for the non-EMA rolling features used by the production terminal row.
- [x] Stale-terminal members are excluded from common-date decisions rather than substituted with old rows.
- [x] FSE-013 governs downstream absence semantics.
- [x] Sep-14 partial-volume incident repaired/verified upstream and downstream; no TrendFoll formula correction supported.
- [ ] Authoritative corporate-action split facts are not present in current R2 READY contract — explicit upstream blocker for split-sensitive corrections.

## Benchmark boundary — AUDIT CONTRACT COMPLETE / INTEGRATION DECISION PENDING

Evidence 07 found the observed SPY state empirically fresh. Evidence 14 freezes the preventive readiness contract and research tests pass.

- [x] SPY is the decision-relevant benchmark.
- [x] RS exact-date benchmark semantics audited.
- [x] Regime backward-as-of semantics audited.
- [x] R2-ahead-of-SPY must fail closed because RS requires exact T0 SPY.
- [x] SPY-ahead-of-R2 is benign for T0 state.
- [x] Frozen benchmark-readiness contract research tests PASS (`35164057505`, job `105021059280`).
- [ ] Explicit production integration decision for benchmark readiness guard.

## Core feature conclusions — COMPLETE 10/10

| Component | Terminal audit conclusion | Remaining production-relevant disposition |
|---|---|---|
| C01 Trend / EMA | current terminal canonical state `VALID USSY DEFINITION` | historical/local raw-close EMA consistency is separate standardization debt; no terminal production blocker |
| C02 Stage | `APPROXIMATION` | retain + redocument; no tuning |
| C03 RS vs SPY | `VALID USSY DEFINITION` | benchmark readiness guard decision only |
| C04 Liquidity | split-sensitive `MISMATCH` | FSE-014 correction contract proven; blocked on upstream split facts |
| C05 Price floor | `VALID USSY DEFINITION` | retain; threshold research optional |
| C06 ATR / tightness | ATR split-state `MISMATCH`; VCP naming mismatch | ATR correction mechanics research PASS; blocked on upstream split facts; rename/redocument tightness proxy |
| C07 Pivot / breakout | valid 60-session trailing-high breakout; not O'Neil pivot | rename/redocument; no formula tuning |
| C08 Volume confirmation | valid rolling volume-rank proxy; O'Neil approximation | rename/redocument; shares FSE-014 normalized-volume dependency |
| C09 Market regime | `VALID USSY DEFINITION` | benchmark readiness guard decision only |
| C10 Aggregation | Investability/Tradability mechanics valid USSY contracts | preserve explicit dual downstream contracts |

## Material findings disposition register

| ID | Severity | Status at terminal-closure stage | Blocking condition |
|---|---|---|---|
| FSE-001 Stage semantics | HIGH | DISPOSITIONED: approximation | non-blocking; redocument |
| FSE-002 VCP/tightness semantics | HIGH | DISPOSITIONED: naming/methodology mismatch | non-blocking; rename/redocument |
| FSE-003 pivot semantics | HIGH | DISPOSITIONED: generic trailing-high rule, not O'Neil pivot | non-blocking; rename/redocument |
| FSE-004 volume-confirmation semantics | MEDIUM | DISPOSITIONED: rolling volume-rank approximation | non-blocking; rename/redocument |
| FSE-005 historical EMA basis | HIGH | DISPOSITIONED for current terminal production; separate standardization debt | no terminal production blocker |
| FSE-006 price/EMA semantic split | MEDIUM | VALID USSY DEFINITION | none |
| FSE-007 benchmark ingestion/readiness | MEDIUM | observed state MATCH; frozen preventive contract PASS | explicit production integration decision |
| FSE-008 R2 warm-up | HIGH | CHARACTERIZED / terminal non-EMA rolling coverage sufficient; canonical terminal EMA separate | none for current terminal decision path |
| FSE-009 regime architecture | INFO | MATCH | none |
| FSE-010 breakout temporal semantics | MEDIUM | MATCH | none |
| FSE-011 downstream dual contracts | MEDIUM | VALID USSY DEFINITION | preserve invariant |
| FSE-012 entry-price semantics | LOW | VALID USSY DEFINITION | naming/documentation only |
| FSE-013 effective-date lifecycle | HIGH | correction + regression + untouched validation V2 PASS | explicit production adoption/defer/reject decision |
| FSE-014 liquidity/corporate actions | HIGH | frozen correction + research tests PASS | BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_FACTS |
| FSE-015 Sep-14 READY volume completeness | HIGH | CLOSED / VERIFIED for TrendFoll scope | none; optional upstream forensics only |
| FSE-016 ATR corporate-action state | HIGH | frozen correction mechanics + research tests PASS | BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_FACTS |

## Correction-set governance

### Correction candidates requiring explicit production decision

1. **FSE-013 effective-date lifecycle state**
   - technical chain complete: root cause -> frozen correction -> implementation -> regression -> untouched validation V2 5/5 PASS;
   - production decision still required.

2. **FSE-007 benchmark readiness guard**
   - observed benchmark freshness is good;
   - preventive fail-closed contract frozen and research-tested;
   - production integration decision still required, followed by full-path regression if adopted.

### Corrections technically specified but externally blocked

3. **FSE-014 split-normalized share volume**
   - correction mechanics and tests exist;
   - cannot safely integrate until `ussy-data` supplies authoritative split facts with effective-date/lineage semantics.

4. **FSE-016 split-normalized ATR state**
   - correction mechanics and tests pass (`35161603163`, job `105013382516`);
   - same upstream corporate-action fact dependency as FSE-014.

### Non-blocking semantic hardening

- rename/redocument Stage as Weinstein-inspired approximation;
- rename/redocument `vcp_tightness` as ATR/volatility-tightness proxy rather than literal Minervini VCP;
- rename/redocument pivot as trailing-high resistance proxy rather than O'Neil/base pivot;
- rename/redocument breakout volume confirmation as rolling volume-rank confirmation;
- preserve explicit documentation of nominal raw-price rules vs adjusted-return/EMA rules;
- preserve dual watchlist/actionability vs production-entry contracts.

No threshold or lookback tuning is authorized by this audit.

## Governed validation state

- [x] Investability/Tradability truth-table and NaN contract tests.
- [x] Weekly Stage temporal/holiday tests.
- [x] R2 READY empirical QC.
- [x] Corporate-action evidence for RS/liquidity/price semantics.
- [x] FSE-013 regression and untouched validation V2 PASS.
- [x] FSE-014 research correction contract tests PASS.
- [x] FSE-016 ATR split-state research correction contract tests PASS.
- [x] FSE-007 benchmark readiness research contract tests PASS.
- [ ] Full regression after any explicitly approved production integrations.
- [ ] Current R2 funnel after approved integration/defer decisions are frozen.

## Terminal closure gates

The Full Signal Engine Audit may close when all of the following are true:

- [x] production path and all decision-relevant primitive/aggregation semantics are known;
- [x] no unresolved look-ahead ambiguity remains in the current terminal decision path;
- [x] every known material finding has an explicit technical disposition;
- [x] externally blocked corrections identify the exact missing upstream contract rather than remaining open-ended research;
- [ ] explicit adopt/defer/reject decision recorded for FSE-013;
- [ ] explicit adopt/defer/reject decision recorded for FSE-007 benchmark readiness guard;
- [ ] if either is adopted, production integration + full regression passes;
- [ ] current R2 funnel is rerun under the final frozen production contract;
- [ ] final limitations and immutable evidence/commit references are recorded;
- [ ] audit status changed to `CLOSED`.

## Legacy 269-item checklist disposition

The previous ledger reported `203 / 269 = 75.5%`. That number is retained as historical engineering-checklist progress only. Open legacy items fall into four groups:

1. superseded by the completed 10/10 Core Indicator Audit;
2. optional methodology/threshold research rather than correctness;
3. optional historical workflow forensics whose causal question is already resolved;
4. terminal production-decision/regression gates represented explicitly above.

They must not be mechanically completed merely to manufacture `269 / 269` when they cannot change the terminal correctness verdict.

## Current audit status — 2026-09-17

**TERMINAL CLOSURE IN PROGRESS / MATERIAL FINDINGS DISPOSITIONED / TWO EXPLICIT PRODUCTION DECISIONS PENDING / TWO CORPORATE-ACTION CORRECTIONS BLOCKED ON UPSTREAM FACTS / NO PRODUCTION CHANGE**
