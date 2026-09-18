# Full Signal Engine Audit — Detailed Progress Checklist

Status: **ARCHIVED EXECUTION LEDGER / AUDIT TERMINALLY CLOSED**

Terminal production branch: `main`

Companion audit: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose

This file preserves the historical execution checklist for the full USSY TrendFoll signal-engine audit. It is **not an active backlog**. Unchecked boxes below are historical decomposition items that were either resolved by later focused audits/remediations, superseded by terminal evidence, or intentionally blocked/deferred under governance. Do not reopen them merely because the old checkbox remains unchecked. `FULL_SIGNAL_ENGINE_AUDIT.md`, `FULL_SIGNAL_ENGINE_STATIC_CLOSURE.md`, and `FEATURE_ENGINE_REACHABILITY_AUDIT.md` carry the terminal evidence/state.

The audit covers the complete path from R2 READY input through feature calculation, Investability, Tradability, lifecycle persistence, alerts, and production entry semantics. EXIT-CAND-003 remains separate and must not influence this audit.

## Terminal closure marker

**FULL SIGNAL ENGINE MATERIAL AUDIT = 100% / CLOSED**  
**CORE INDICATOR AUDIT = 10/10 COMPLETE / FROZEN**  
**TERMINAL PRODUCTION PATH = PASS**

Production architecture after consolidation:

```text
daily.yml → main.py → r2_integration.py → feature_engine.py → r2_shared_ema.py → downstream
```

FSE-005 is **CORRECTED / CI VALIDATED / PRODUCTION ADOPTED / TERMINAL VERIFIED / CLOSED**. FSE-014 and FSE-016 remain upstream-blocked/deferred and are not reasons to reopen this audit. Production-equivalence run `35283636542` and subsequent normal scheduled run `35292138481` both succeeded on the consolidated path.

## Historical governance / stop rules

- [x] G0.1 Audit is diagnostic; production behavior remains unchanged.
- [x] G0.2 EXIT-CAND-003 is explicitly outside the signal-engine audit decision path.
- [x] G0.3 Existing production definitions are not silently reinterpreted during audit.
- [x] G0.4 Findings use controlled labels: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.
- [x] G0.5 A suspicious result is not called a bug until input, code path, temporal semantics, and reproducibility are checked.
- [x] G0.6 Sep-10 `+61` lifecycle jump is a diagnostic case, not a presumed anomaly.
- [x] G0.7 Legacy-universe contamination is closed/disproven: current R2 READY = 1,227; historical lifecycle = 161; 161/161 are in current R2 READY; legacy-only = 0. Do not reopen without contradictory evidence.
- [ ] G0.8 No correction is implemented until its root cause and intended contract are documented.
- [ ] G0.9 Every approved correction receives tests before production decision.
- [ ] G0.10 Any validation dataset used for a correction remains untouched after the correction specification is frozen.

---

# Phase A — Production execution map

- [x] A1 Identify scheduled production workflow.
- [x] A2 Confirm workflow entry point is `main.py` for current R2 production path.
- [x] A3 Trace R2 READY loader and validation.
- [x] A4 Trace R2-to-feature adapter.
- [x] A5 Trace legacy feature-engine reuse underneath R2 adapter.
- [x] A6 Trace canonical terminal EMA overlay.
- [x] A7 Trace hard filter.
- [x] A8 Trace decision layer.
- [x] A9 Trace latest-date candidate selection.
- [x] A10 Trace lifecycle/watchlist persistence at high level.
- [ ] A11 Trace alert-state transition logic field by field.
- [ ] A12 Trace watchlist upsert field by field.
- [ ] A13 Trace candidate lifecycle insert/update semantics field by field.
- [ ] A14 Trace production position registration and realistic-entry path.
- [ ] A15 Confirm exact T0 signal / T+1 execution semantics in every downstream consumer.
- [ ] A16 Identify any downstream consumer that uses `hard_filter_status` where `investability_status` is intended.

**Exit criterion:** one complete production data-flow map with no unknown decisioning consumer.

---

# Phase B — R2 input contract and readiness

- [x] B1 Confirm R2 manifest/schema/checksum/security-ID validation exists.
- [x] B2 Confirm stock universe is derived from current R2 READY.
- [x] B3 Confirm terminal canonical EMA is lineage-checked against current R2 READY.
- [ ] B4 Establish actual READY history depth distribution per security.
- [ ] B5 Record minimum / median / maximum bars per security.
- [ ] B6 Count securities with <20, <50, <60, <63, <150, <200, <252 bars.
- [ ] B7 Check first/last market date consistency across securities.
- [ ] B8 Check duplicate `(security_id,date)` rows.
- [ ] B9 Check missing OHLCV / adj_close fields by security/date.
- [ ] B10 Check nonpositive/invalid price or volume facts.
- [ ] B11 Check corporate-action-sensitive raw-vs-adjusted continuity.
- [ ] B12 Determine whether current READY is a rolling finite window or carries sufficient warm-up history by contract.
- [ ] B13 Identify which features can be fully computed from READY and which rely on insufficient warm-up.
- [ ] B14 Verify READY snapshot/session lineage around Sep-4 through Sep-10.
- [ ] B15 Determine whether R2 universe membership/input snapshot changed materially around Sep-10.

**Exit criterion:** every feature has an explicit minimum-history requirement and measured READY coverage.

---

# Phase C — Benchmark / external-data boundary

- [x] C1 Establish that stock OHLCV comes from R2 while SPY/QQQ/VIX/sector ETFs are downloaded separately.
- [ ] C2 Inventory every external benchmark actually downloaded.
- [ ] C3 Identify which downloaded benchmarks affect production decisions.
- [ ] C4 Mark benchmarks/features that are calculated but `DEAD / UNUSED` in production decisions.
- [ ] C5 Check benchmark latest date versus R2 latest date.
- [ ] C6 Check benchmark missing-session behavior.
- [ ] C7 Audit exact-date merge used by RS.
- [ ] C8 Audit backward-as-of merge used by market regime.
- [ ] C9 Test stale benchmark scenarios and resulting statuses.
- [ ] C10 Test R2-ahead-of-benchmark scenario.
- [ ] C11 Test benchmark-ahead-of-R2 scenario.
- [ ] C12 Decide whether benchmark freshness requires a governed readiness contract.

**Exit criterion:** no silent stale/misaligned benchmark can alter a production status without being detected or documented.

---

# Phase D — Feature-by-feature formula audit

For every feature below, document: input basis, formula, minimum history, current-bar usage, adjustment basis, temporal availability, downstream use, intended meaning, actual meaning, classification, and test coverage.

## D1 Trend / moving averages

- [x] D1.1 Terminal EMA20/50/150/200 formula/basis traced.
- [x] D1.2 Historical EMA formula/basis traced.
- [x] D1.3 Terminal `ema_stack_aligned` traced.
- [x] D1.4 Historical-vs-terminal EMA basis mismatch identified (`close_raw` history vs canonical `adj_close` terminal).
- [ ] D1.5 Quantify how many historical rows/symbols change classification under consistent EMA basis.
- [ ] D1.6 Check EMA initialization/warm-up sensitivity.
- [ ] D1.7 Determine intended canonical historical EMA contract.
- [ ] D1.8 Add/identify invariant tests for terminal EMA lineage and ordering.

## D2 Stage Analysis

- [x] D2.1 Current weekly resampling traced.
- [x] D2.2 Current 30-week SMA traced.
- [x] D2.3 Current three-observation slope rule traced.
- [x] D2.4 Current Stage1/2/3/4 mapping traced.
- [x] D2.5 Current implementation classified as `APPROXIMATION` pending dedicated methodology audit.
- [ ] D2.6 Audit weekly W-FRI labeling around market holidays.
- [ ] D2.7 Verify no weekly look-ahead is introduced by resample/as-of merge.
- [ ] D2.8 Compare current Stage semantics against authoritative Weinstein methodology.
- [ ] D2.9 Enumerate missing lifecycle/context elements.
- [ ] D2.10 Quantify Stage transition stability around Sep-4–Sep-10.
- [ ] D2.11 Quantify contribution of Stage transitions to Sep-10 first-time lifecycle symbols.
- [ ] D2.12 Freeze corrected Stage specification only if evidence supports a correction.

## D3 Relative strength

- [x] D3.1 `return_63d` formula traced.
- [x] D3.2 SPY 63-session return formula traced.
- [x] D3.3 `rs_spy = stock_return_63d - spy_return_63d` traced.
- [x] D3.4 PASS/NEAR/FAIL thresholds traced.
- [ ] D3.5 Verify 63-session horizon rationale/evidence.
- [ ] D3.6 Verify PASS >=0 and NEAR >=-0.02 rationale/evidence.
- [ ] D3.7 Measure missing/NaN RS due to insufficient history.
- [ ] D3.8 Measure missing/NaN RS due to benchmark-date alignment.
- [ ] D3.9 Audit split/corporate-action semantics of stock and SPY return bases.
- [ ] D3.10 Quantify RS transitions Sep-4–Sep-10 and contribution to +61 case.

## D4 Liquidity

- [x] D4.1 `avg_volume_50d` formula traced.
- [x] D4.2 PASS >=300k / NEAR >=240k thresholds traced.
- [ ] D4.3 Verify threshold rationale/evidence.
- [ ] D4.4 Check raw-share-volume behavior around splits/corporate actions.
- [ ] D4.5 Check min-period behavior and warm-up classification.
- [ ] D4.6 Quantify liquidity transitions Sep-4–Sep-10 and contribution to +61 case.

## D5 Price floor

- [x] D5.1 Raw-close price basis traced.
- [x] D5.2 PASS >=$10 / NEAR >=$8 thresholds traced.
- [ ] D5.3 Verify threshold rationale/evidence.
- [ ] D5.4 Audit corporate-action behavior.
- [ ] D5.5 Quantify price transitions Sep-4–Sep-10 and contribution to +61 case.

## D6 Structure / ATR / VCP proxy

- [x] D6.1 ATR14 formula traced.
- [x] D6.2 ATR percentile 63d traced.
- [x] D6.3 `vcp_tightness = 100 - ATR percentile` traced.
- [x] D6.4 VCP label/semantics classified `MISMATCH` with literal VCP morphology.
- [ ] D6.5 Audit ATR/percentile minimum-history behavior.
- [ ] D6.6 Quantify how often `vcp_tightness >=60` occurs.
- [ ] D6.7 Determine whether field should be renamed as low-volatility/tightness proxy or replaced.
- [ ] D6.8 Audit `base_length_days` formula and downstream usage.
- [ ] D6.9 Mark `base_length_days` `DEAD / UNUSED` if no production consumer exists.

## D7 Pivot / breakout

- [x] D7.1 `pivot_high` rolling-60 formula traced.
- [x] D7.2 `prev_pivot_high = pivot_high.shift(1)` traced.
- [x] D7.3 `close_raw(T0) > prev_pivot_high` breakout rule traced.
- [x] D7.4 Current pivot classified `MISMATCH` with validated O'Neil/base pivot semantics.
- [x] D7.5 Current breakout recognized as a valid USSY rolling-high breakout definition if labeled accurately.
- [ ] D7.6 Audit min-period=20 behavior for nominal 60-session pivot.
- [ ] D7.7 Quantify rolling-high breakout frequency.
- [ ] D7.8 Determine intended production meaning: Donchian-like rolling breakout vs chart-base pivot breakout.
- [ ] D7.9 Freeze terminology/formula correction if needed.

## D8 Breakout volume

- [x] D8.1 Rolling-50 percentile formula traced.
- [x] D8.2 Current bar inclusion identified.
- [x] D8.3 >=80 confirmation threshold traced.
- [ ] D8.4 Compare current-included percentile with prior-50-only percentile.
- [ ] D8.5 Verify threshold rationale/evidence.
- [ ] D8.6 Compare semantics with intended breakout-volume concept.

## D9 Market regime and auxiliary features

- [x] D9.1 Market regime formula traced at high level.
- [x] D9.2 Confirm Investability excludes regime.
- [ ] D9.3 Trace every downstream use of `hard_filter_status` and regime.
- [ ] D9.4 Audit volatility regime downstream usage.
- [ ] D9.5 Audit `rs_sector` downstream usage.
- [ ] D9.6 Audit `rs_spy_persistence_weeks` downstream usage.
- [ ] D9.7 Audit `volume_ratio` downstream usage.
- [ ] D9.8 Audit `volume_dry_up` downstream usage.
- [ ] D9.9 Audit ADX downstream usage.
- [ ] D9.10 Audit 52-week-high-distance downstream usage.
- [ ] D9.11 Mark unused features explicitly `DEAD / UNUSED` rather than treating them as signal inputs.

**Exit criterion:** feature matrix is complete and every production-relevant field has a defensible, temporally valid contract.

---

# Phase E — Investability contract audit

- [x] E1 Identify Investability components: Trend + Liquidity + RS + Price.
- [x] E2 Confirm regime is excluded from Investability.
- [x] E3 Trace component PASS/NEAR/FAIL thresholds.
- [ ] E4 Verify exact aggregation/non-compensation rule.
- [ ] E5 Enumerate all possible component-state combinations and expected Investability output.
- [ ] E6 Add table-driven tests for aggregation truth table.
- [ ] E7 Check NaN/None behavior for every component.
- [ ] E8 Check whether insufficient history becomes FAIL, NaN, or another state consistently.
- [ ] E9 Check whether latest-date selection can compare securities with different effective data dates.
- [ ] E10 Verify candidate filter is exactly `Investability >= NEAR_PASS`.
- [ ] E11 Verify lifecycle first-seen semantics use the intended Investability state.
- [ ] E12 Verify alerts use intended state transitions.
- [ ] E13 Verify production position registration uses intended Investability/Tradability contract.
- [ ] E14 Produce current-state Investability funnel only after upstream audit is clean.

**Exit criterion:** every Investability transition is reproducible from four component statuses and valid inputs.

---

# Phase F — Tradability contract audit

- [x] F1 Identify breakout requirement.
- [x] F2 Identify breakout-volume confirmation.
- [x] F3 Identify tight-structure confirmation.
- [x] F4 Trace current PASS/NEAR/FAIL aggregation.
- [ ] F5 Build complete Tradability truth table.
- [ ] F6 Add table-driven aggregation tests.
- [ ] F7 Check NaN behavior for pivot, volume percentile, tightness.
- [ ] F8 Check minimum-history behavior.
- [ ] F9 Confirm no same-bar self-reference in breakout pivot.
- [ ] F10 Confirm signal availability only after T0 close.
- [ ] F11 Confirm all executable evaluation uses T+1 Open where execution is modeled.
- [ ] F12 Determine whether current Tradability terminology overstates O'Neil/Minervini semantics.
- [ ] F13 Separate valid rolling-breakout mechanics from chart-pattern claims.

**Exit criterion:** Tradability is internally coherent, temporally executable, and accurately named.

---

# Phase G — Temporal / look-ahead / as-of audit

- [ ] G1 Build a field-level table: earliest timestamp each input is knowable.
- [ ] G2 Verify daily OHLCV T0 is only used for decisions after T0 close.
- [ ] G3 Verify shifted pivot excludes T0 high from T0 breakout reference.
- [ ] G4 Verify rolling calculations never use future rows.
- [ ] G5 Verify weekly Stage resampling does not leak future Friday information into Mon–Thu.
- [ ] G6 Verify holiday-shortened weeks do not create leakage or unintended lag.
- [ ] G7 Verify exact-date benchmark merge has no forward fill from future benchmark dates.
- [ ] G8 Verify regime backward-as-of merge only uses same/prior benchmark state.
- [ ] G9 Verify lifecycle comparisons are as-of historical state, not recomputed with future/canonical terminal overlays.
- [ ] G10 Verify backtests/research do not accidentally use terminal-only canonical EMA state for earlier dates.
- [ ] G11 Verify T+1 Open execution constraint wherever signal outcomes are evaluated.

**Exit criterion:** zero unresolved look-ahead/as-of ambiguity.

---

# Phase H — Sep-4 to Sep-10 workflow continuity audit

Diagnostic target: explain the Sep-10 lifecycle jump without presuming anomaly.

Known run-history evidence already observed:

- Sep-4: failure observed.
- Sep-5: failure observed.
- Sep-8: successful run observed.
- Sep-9: failure observed.
- Sep-10: failure observed for a legacy `main.py` run; it reached market date 2026-09-09 with 0/197 candidates and later failed during position tracking on non-JSON-compliant `NaN`.

These observations must be reconciled with the R2 lifecycle records before causal attribution.

- [ ] H1 Enumerate every workflow run Sep-4 through Sep-10 with run ID, event, branch, commit, start/end, conclusion.
- [ ] H2 Separate scheduled production runs from manual/research/other workflows.
- [ ] H3 Map each run timestamp to the intended US market session.
- [ ] H4 Explicitly mark weekend dates.
- [ ] H5 Explicitly mark US market holiday/non-session dates.
- [ ] H6 Do not classify a non-session as missing pipeline output.
- [ ] H7 For each market session, determine whether a production run started.
- [ ] H8 For each production run, determine whether feature calculation completed.
- [ ] H9 Determine whether candidate/watchlist persistence completed.
- [ ] H10 Determine whether lifecycle persistence completed.
- [ ] H11 Determine whether alert persistence/notification completed.
- [ ] H12 Determine whether position stage failed only after lifecycle persistence or before it.
- [ ] H13 Identify exact exception/root cause for each failed run.
- [ ] H14 Determine whether reruns occurred and whether they repaired missing persistence.
- [ ] H15 Compare commits/configuration used by each production run.
- [ ] H16 Identify code/config/threshold changes between last normal pre-jump run and Sep-10 lifecycle-producing run.
- [ ] H17 Determine when production switched from legacy universe/path to R2 path, if relevant to this window.
- [ ] H18 Determine whether any successful R2 run effectively caught up after missed/failed sessions.

**Exit criterion:** session-by-session continuity ledger explains what did and did not execute/persist.

---

# Phase I — Sep-10 +61 lifecycle diagnostic

Established facts supplied for this diagnostic:

- cumulative lifecycle before Sep-10: 100 symbols
- first-time lifecycle on Sep-10: +61 symbols
- cumulative lifecycle after jump: 161 symbols
- current Investability >= NEAR_PASS on Sep-10: 85 symbols
- all 161 historical lifecycle symbols belong to current R2 READY
- legacy-only symbols: 0

## I1 Reconstruct the population

- [ ] I1.1 Extract exact 61 first-time lifecycle symbols dated Sep-10.
- [ ] I1.2 Verify each symbol's first-seen timestamp/date.
- [ ] I1.3 Verify none had an earlier lifecycle record under another identifier/ticker mapping.
- [ ] I1.4 Confirm security-ID/ticker mapping consistency.
- [ ] I1.5 Confirm all 61 are present in the relevant R2 READY snapshot, not merely current READY.

## I2 Reconstruct prior observable state

For every one of the 61 symbols:

- [ ] I2.1 Find last valid observable session before Sep-10.
- [ ] I2.2 Record prior `trend_status`.
- [ ] I2.3 Record prior `stage`.
- [ ] I2.4 Record prior `ema_stack_aligned`.
- [ ] I2.5 Record prior `rs_status` and `rs_spy`.
- [ ] I2.6 Record prior `liquidity_status` and underlying average volume.
- [ ] I2.7 Record prior `price_status` and raw close.
- [ ] I2.8 Record prior `investability_status`.
- [ ] I2.9 Record Sep-10 values for the same fields.
- [ ] I2.10 Record data date/lineage for both observations.

## I3 Attribute first qualifying transition

- [ ] I3.1 Classify `Trend FAIL -> NEAR/PASS` only.
- [ ] I3.2 Classify `RS FAIL -> NEAR/PASS` only.
- [ ] I3.3 Classify `Liquidity FAIL -> NEAR/PASS` only.
- [ ] I3.4 Classify `Price FAIL -> NEAR/PASS` only.
- [ ] I3.5 Classify multiple simultaneous component changes.
- [ ] I3.6 Separate `Stage` change from EMA-stack change within Trend transitions.
- [ ] I3.7 Identify symbols whose prior state is unavailable because pipeline did not persist it.
- [ ] I3.8 Distinguish genuine first qualification from first *observed/persisted* qualification after a continuity gap.
- [ ] I3.9 Produce counts and symbol lists for every transition category.

## I4 Test causal hypotheses

- [ ] I4.1 HYP-MARKET: test whether market/stock price movement alone reproduces component transitions under unchanged engine/input contract.
- [ ] I4.2 HYP-PIPELINE: test whether failed/missing production persistence caused accumulated first-seen records.
- [ ] I4.3 HYP-R2-SNAPSHOT: compare relevant R2 manifest/snapshot lineage before and on Sep-10.
- [ ] I4.4 HYP-CODE: compare commits affecting feature/filter/decision/lifecycle code.
- [ ] I4.5 HYP-CONFIG: compare thresholds/environment-driven configuration.
- [ ] I4.6 HYP-FEATURE: identify formula/implementation changes affecting classifications.
- [ ] I4.7 HYP-WARMUP: test whether added history/readiness crossed feature minimum periods simultaneously.
- [ ] I4.8 HYP-STAGE: quantify Stage-driven transitions.
- [ ] I4.9 HYP-EMA: quantify EMA-stack-driven transitions.
- [ ] I4.10 HYP-RS: quantify RS-driven transitions.
- [ ] I4.11 HYP-OTHER: inspect identifier, date-selection, NaN, persistence, or state-machine defects.

## I5 Reproducibility verdict

- [ ] I5.1 Re-run/reconstruct Sep-10 decision state from immutable inputs if available.
- [ ] I5.2 Compare reconstructed 85 current qualifying symbols with persisted state.
- [ ] I5.3 Compare reconstructed first-time set with persisted +61.
- [ ] I5.4 Explain every discrepancy.
- [ ] I5.5 If all +61 are legitimate and reproducible, record `EXPLAINABLE / NO DEFECT FOUND` with evidence.
- [ ] I5.6 If a data/engine/pipeline defect contributed, create a numbered FSE finding with severity, affected population, mechanism, and correction candidate.
- [ ] I5.7 Do not collapse mixed causality: report proportions/counts by cause if multiple mechanisms contributed.

**Exit criterion:** all 61 symbols are individually attributable or explicitly marked unresolved with the missing evidence named.

---

# Phase J — Findings register and correction candidates

Existing findings in `FULL_SIGNAL_ENGINE_AUDIT.md`: FSE-001 through FSE-010.

- [ ] J1 Re-evaluate severity/classification after empirical checks.
- [ ] J2 Add any workflow-continuity finding from Sep-4–Sep-10.
- [ ] J3 Add any lifecycle-state-machine/persistence finding.
- [ ] J4 Add any R2 warm-up/readiness defect.
- [ ] J5 Add any benchmark-freshness defect.
- [ ] J6 Add any temporal/look-ahead defect.
- [ ] J7 Add any NaN handling defect affecting production decision/persistence.
- [ ] J8 Separate naming/semantic mismatches from computational bugs.
- [ ] J9 For each actionable finding, document affected fields and downstream impact.
- [ ] J10 For each correction candidate, document intended contract before code change.
- [ ] J11 Rank correction execution by dependency/severity, not by convenience.
- [ ] J12 Freeze correction specification before validation.

**Exit criterion:** no unresolved high-severity production-relevant finding without an explicit disposition.

---

# Phase K — Test and validation gate

- [ ] K1 Unit tests for every corrected formula.
- [ ] K2 Truth-table tests for Investability.
- [ ] K3 Truth-table tests for Tradability.
- [ ] K4 NaN/insufficient-history tests.
- [ ] K5 Corporate-action/raw-vs-adjusted tests where applicable.
- [ ] K6 Weekly Stage calendar/holiday tests.
- [ ] K7 Benchmark stale/missing-session tests.
- [ ] K8 Temporal no-look-ahead tests.
- [ ] K9 T+1 Open execution tests for event-level evaluation.
- [ ] K10 Lifecycle idempotency tests.
- [ ] K11 First-seen persistence tests.
- [ ] K12 Failed-run/rerun recovery tests.
- [ ] K13 Regression test reproducing Sep-10 diagnostic case where immutable inputs permit.
- [ ] K14 Development sample completed before untouched validation.
- [ ] K15 Correction frozen before validation.
- [ ] K16 Untouched validation executed once under governance.
- [ ] K17 No post-validation tuning without new governed cycle.

**Exit criterion:** approved correction set passes tests and governed validation.

---

# Phase L — Final production decision and post-audit funnel

- [ ] L1 Summarize engine components classified MATCH / VALID / APPROXIMATION / MISMATCH / BUG / UNUSED.
- [ ] L2 Summarize Sep-10 lifecycle diagnostic verdict with evidence.
- [ ] L3 Document remaining known limitations.
- [ ] L4 Explicit production decision for each correction candidate: adopt / defer / reject.
- [ ] L5 Production code change only after explicit decision.
- [ ] L6 Re-run full test suite after production integration.
- [ ] L7 Run current R2 READY funnel only after signal engine is clean enough for interpretation.
- [ ] L8 Report current counts by Trend, RS, Liquidity, Price, Investability, Tradability.
- [ ] L9 Establish ongoing health checks for R2 freshness, benchmark freshness, NaN, and lifecycle jumps.
- [ ] L10 Close audit with immutable evidence references/commit SHAs.

---

# Progress summary

| Phase | Area | Status |
|---|---|---|
| G0 | Governance | IN PROGRESS |
| A | Production execution map | IN PROGRESS — core path traced |
| B | R2 input/readiness | IN PROGRESS — contract traced, empirical coverage pending |
| C | Benchmark boundary | IN PROGRESS — split ingestion established |
| D | Feature formulas | IN PROGRESS — major formulas traced, evidence/quantification pending |
| E | Investability | IN PROGRESS — components traced |
| F | Tradability | IN PROGRESS — components traced |
| G | Temporal/look-ahead | PENDING DETAILED AUDIT |
| H | Sep-4–Sep-10 workflow continuity | IN PROGRESS — initial failed-run evidence established |
| I | Sep-10 +61 diagnostic | PENDING RECONSTRUCTION |
| J | Findings/corrections | IN PROGRESS — FSE-001..010 registered |
| K | Tests/validation | NOT STARTED |
| L | Production decision/funnel | BLOCKED BY AUDIT |

## Audit completion rule

The audit is **not complete** merely because all formulas have been read. Completion requires:

`input contract -> formula -> temporal semantics -> downstream consumer -> empirical behavior -> finding classification -> correction specification (if any) -> tests -> governed validation -> explicit production decision`.

The Sep-10 lifecycle case is considered closed only when the 61 first-time symbols are explainable at symbol/component level or the exact missing evidence preventing attribution is documented.
