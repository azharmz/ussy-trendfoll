# Core Indicator Audit — Legacy vs Current

Status: **CORE COMPLETE 10/10 / C01-C04 REVIEW GATE PASS / NO PRODUCTION CHANGE / RETURN TO FULL AUDIT**

Branch: `research/exit-development-hypotheses`

Extended engineering audit: `docs/FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md`

Evidence/findings register: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose and closure boundary

This Core track answers whether the primitive/current decision components are implemented coherently, how they differ from legacy, whether their names match what they measure, and whether they are temporally causal. Core completion does **not** declare the complete production signal engine validated. The Full Signal Engine Audit remains responsible for end-to-end composition, ingestion/readiness, lifecycle, consumer semantics, and governed remediation/production decisions.

Controlled verdicts: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.

## Core progress

- [x] C01 Trend / EMA
- [x] C02 Stage Analysis
- [x] C03 Relative Strength vs SPY
- [x] C04 Liquidity
- [x] C05 Price floor
- [x] C06 ATR / volatility tightness
- [x] C07 Pivot / breakout
- [x] C08 Breakout volume confirmation
- [x] C09 Market regime
- [x] C10 Investability / Tradability aggregation

**Core completion: 10 / 10.**

## Final Core matrix

| ID | Component | Core verdict | Action |
|---|---|---|---|
| C01 | Trend / EMA | Current terminal canonical EMA is a `VALID USSY DEFINITION`; legacy-current deliberately changed. | RETAIN current terminal contract; historical/local consistency remains separate debt/remediation. |
| C02 | Stage Analysis | `APPROXIMATION`; legacy-current MATCH. | RETAIN + REDOCUMENT as Weinstein-inspired approximation. |
| C03 | RS vs SPY | `VALID USSY DEFINITION`; legacy-current MATCH. | RETAIN; horizon/threshold evidence separate. |
| C04 | Liquidity | legacy-current MATCH but split-sensitive `MISMATCH`. | CORRECT under FSE-014 governance; no production change from Core. |
| C05 | Price floor | `VALID USSY DEFINITION`; legacy-current MATCH. | RETAIN; $10/$8 rationale separate research. |
| C06 | ATR / volatility tightness | ATR raw state split-sensitive `MISMATCH`; VCP label `MISMATCH`; legacy-current MATCH. | CORRECT ATR basis/state separately; RENAME/REDOCUMENT VCP proxy. |
| C07 | Pivot / breakout | Valid trailing-high breakout; not O'Neil/base pivot; legacy-current MATCH. | RENAME/REDOCUMENT; no silent morphology substitution. |
| C08 | Breakout volume confirmation | Valid inclusive rolling-volume rank; `APPROXIMATION` as O'Neil confirmation; legacy-current MATCH. | RENAME/REDOCUMENT; inherit FSE-014 normalized-volume dependency. |
| C09 | Market regime | `VALID USSY DEFINITION` internal SPY trend regime; legacy-current MATCH. | RETAIN + REDOCUMENT portfolio-level consumer boundary; benchmark readiness remains Full-Audit concern. |
| C10 | Investability / Tradability aggregation | Aggregation mechanics are `MATCH` legacy-current and internally coherent, but downstream semantics intentionally form **two distinct contracts** rather than one universal actionable definition. | RETAIN explicit dual-contract architecture; do not silently unify. Full Audit must validate composition/lifecycle and pending primitive remediations before engine-level closure. |

## C01-C04 independent review gate

**PASS.** No dependent Core conclusion was invalidated. C04 remediation remains separately governed.

## C05-C09 disposition summary

C05 nominal price floor is retained. C06 identified split-sensitive ATR state and an overstated VCP label. C07 is a valid trailing-high breakout rather than an O'Neil/base pivot. C08 is an inclusive rolling volume-rank confirmation and inherits split-volume normalization concerns. C09 is a valid internal SPY trend regime whose consumer boundary must remain explicit.

## C10 evidence note — Investability / Tradability aggregation

### 1. Primitive aggregation formulas

`compute_investability()` combines exactly four structural statuses: Trend, Liquidity, RS, and Price. It is non-compensatory: any FAIL produces Investability FAIL; otherwise any NEAR_PASS produces Investability NEAR_PASS; only all PASS produces Investability PASS. Regime is deliberately excluded because the decision-layer contract treats it as portfolio-level context.

`compute_tradability()` is also hierarchical rather than scored. It first creates the causal breakout against the shifted prior pivot, then derives volume confirmation and tight-structure booleans. Without breakout, Tradability is FAIL. With breakout, both confirmations produce PASS; one confirmation produces NEAR_PASS; even breakout with neither confirmation remains NEAR_PASS under the explicit legacy rule.

This last branch is important: Tradability NEAR_PASS does **not** mean that at least one confirmation is present. It can mean breakout-only. Documentation/consumers must not infer otherwise.

### 2. Legacy comparison

Original repository commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` contains the identical `INVESTABILITY_COLS`, non-compensatory minimum-rank aggregation, shifted-pivot breakout, >=80 volume confirmation, >=60 `vcp_tightness` confirmation, and Tradability PASS/NEAR/FAIL branching. Therefore the decision-layer aggregation itself has no legacy-current regression.

Current production differs upstream in important primitive state — notably canonical terminal EMA and R2 stock ingestion — but the aggregation functions consuming the resulting statuses remain the legacy composition rules.

### 3. Actual current production consumers

The production R2 path executes:

`R2 READY -> features -> hard filter -> decision layer -> common latest date`.

It then creates the watchlist/candidate population from **Investability >= NEAR_PASS only**. Tradability is retained on those rows for state/explainability but is not required for membership in the monitored candidate set.

`alert_state` defines:

- monitored = Investability >= NEAR_PASS;
- ACTIONABLE = Investability PASS **and** Tradability PASS;
- otherwise a monitored row is NEAR_TRIGGER;
- loss/invalidation/data-unavailable/out-of-universe are lifecycle states handled separately.

Thus the watchlist/actionability contract is genuinely based on the Investability/Tradability split.

### 4. Separate authoritative production-position entry contract

`positions.register_new_positions()` does **not** require `investability_status == PASS` and does **not** require `tradability_status == PASS`. It selects the full latest universe and requires:

`hard_filter_status == PASS`
`AND has_breakout == True`
`AND has_volume_confirmation == True`.

Because `hard_filter_status` includes Regime while Investability excludes Regime, the two contracts are not interchangeable. Because production entry requires volume confirmation but does not require `has_tight_structure`, it is also not interchangeable with Tradability PASS, which requires both volume confirmation and tightness.

This independently confirms FSE-011: the system intentionally preserves a backtest-parity production-entry contract alongside the newer watchlist/actionability contract. Core finds no evidence that one is accidentally substituting for the other in the traced current path.

### 5. Consequences of the dual contract

A row can be **ACTIONABLE in alert semantics** (`Investability PASS + Tradability PASS`) yet fail production entry because Regime makes `hard_filter_status` non-PASS.

Conversely, a row can satisfy the production entry contract with hard-filter PASS + breakout + volume confirmation even when `has_tight_structure` is false, meaning Tradability can be NEAR_PASS rather than PASS. Therefore "ACTIONABLE" and "entry-ready" are deliberately different predicates.

This distinction is semantically valid only while documentation and downstream consumers keep the names/contracts explicit. A future refactor that substitutes `tradability_status == PASS` for the production-entry predicate, or substitutes `hard_filter_status` for Investability candidate selection, would change strategy behavior and requires an explicit governed decision plus regression/backtest evidence.

### 6. Temporal correctness

All decision-layer inputs are T0-or-earlier under their primitive contracts. Breakout uses the prior-row pivot; T0 volume/tightness/structural statuses are known after T0 close. Candidate/actionable classification is therefore a T0-close decision state. Production position registration records T0 trigger facts; realistic executable entry remains separately filled at the first available T+1 Open. No C10 aggregation step introduces a new future-data dependency.

### 7. Dependency propagation from Core findings

C10 aggregation mechanics can be correct while the aggregate output remains affected by upstream primitive findings. In particular:

- C04/FSE-014 can alter Liquidity and therefore hard filter / Investability;
- C06 split-sensitive ATR can alter tightness and production stop state;
- C08 inherits normalized-volume dependency and can alter volume confirmation;
- C09 benchmark freshness can alter hard-filter Regime status;
- C01 historical/local EMA consistency remains relevant outside the canonical terminal production state.

Therefore Core completion must not be interpreted as approval to freeze the complete engine exactly as-is. It closes the component audit and hands the remaining composition/remediation questions back to Full Audit governance.

### C10 disposition

- Investability aggregation mechanics: **`MATCH` legacy-current / `VALID USSY DEFINITION`**.
- Tradability aggregation mechanics: **`MATCH` legacy-current / `VALID USSY DEFINITION` for the documented USSY hierarchy**, subject to the already-closed C06/C07/C08 semantic caveats.
- Candidate/watchlist membership: **Investability >= NEAR_PASS**, confirmed in actual R2 production path.
- Alert ACTIONABLE: **Investability PASS + Tradability PASS**, confirmed in `alert_state`.
- Production position entry: **hard-filter PASS + breakout + volume confirmation**, confirmed independently and intentionally distinct.
- Regime: excluded from Investability but included in hard filter, so it can block production entry without blocking Investability monitoring.
- Tightness: required for Tradability PASS but not production entry.
- Temporal causality: **PASS at aggregation level**; realistic execution remains T+1 Open.
- Legacy-current decision-layer aggregation: **MATCH**.
- Action: **RETAIN explicit dual-contract architecture / REDOCUMENT names and invariants / prohibit silent unification.**

**C10 CLOSED. Production remains unchanged.**

## Core terminal conclusion

The Core Indicator Audit is **COMPLETE 10/10**. It does not support a blanket statement that every primitive is correct as currently implemented. Instead it establishes a controlled disposition for each component and confirms the actual decision-layer composition.

Core-supported corrections or semantic hardening still requiring separate governance include at minimum:

- C04/FSE-014 split-normalized share-volume handling;
- C06 split-sensitive ATR state;
- C06/C07/C08 naming/documentation so proxies are not represented as literal VCP/O'Neil constructs;
- C09/FSE-007 benchmark readiness/freshness governance;
- historical/local EMA consistency outside the canonical terminal production state;
- any explicit production adoption decisions already pending in Full Audit, including FSE-013/FSE-014 workstreams.

No production code was changed by Core closure.

## Handoff back to Full Signal Engine Audit

Core is no longer the blocking primitive-audit track. The next primary objective is the Full Signal Engine Audit terminal chain:

`R2 READY -> FEATURES/INDICATORS -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST -> ALERT/ACTIONABLE OUTPUT -> PRODUCTION ENTRY/EXIT`

Full Audit should now consume the frozen Core dispositions rather than reopening/tuning them without new evidence. Remaining work is composition correctness, unresolved readiness/effective-date/corporate-action governance, regression/untouched validation for approved corrections, explicit production decisions, and synchronization of the extended engineering checklist.

**CORE INDICATOR AUDIT: CLOSED / 10 OF 10.**