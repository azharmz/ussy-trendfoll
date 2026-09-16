# Full Signal Engine Audit — Detailed Progress Checklist

Status: **ACTIVE AUDIT CONTROL DOCUMENT / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

Companion audit: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose

This file is the operational checklist and progress ledger for the full USSY TrendFoll signal-engine audit. It is the primary execution guide for the audit. `FULL_SIGNAL_ENGINE_AUDIT.md` remains the evidence/findings document.

The audit covers the complete path from R2 READY input through feature calculation, Investability, Tradability, lifecycle persistence, alerts, and production entry semantics. EXIT-CAND-003 remains separate and must not influence this audit.

## Governance / stop rules

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
- [x] A2 Confirm workflow entry point is `r2_main.py` for current R2 production path.
- [x] A3 Trace R2 READY loader and validation.
- [x] A4 Trace R2-to-feature adapter.
- [x] A5 Trace legacy feature-engine reuse underneath R2 adapter.
- [x] A6 Trace canonical terminal EMA overlay.
- [x] A7 Trace hard filter.
- [x] A8 Trace decision layer.
- [x] A9 Trace latest-date candidate selection.
- [x] A10 Trace lifecycle/watchlist persistence at high level.
- [x] A11 Trace alert-state transition logic field by field.
- [x] A12 Trace watchlist upsert field by field.
- [x] A13 Trace candidate lifecycle insert/update semantics field by field.
- [x] A14 Trace production position registration and realistic-entry path.
- [x] A15 Confirm exact T0 signal / T+1 execution semantics in every downstream consumer.
- [x] A16 Identify any downstream consumer that uses `hard_filter_status` where `investability_status` is intended.

Evidence: `FULL_SIGNAL_ENGINE_AUDIT_EVIDENCE_05_DOWNSTREAM.md`. A11–A16 are closed at code-contract level; empirical persisted-row consistency remains a separate audit task.

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
- [x] B12 Determine whether current READY is a rolling finite window or carries sufficient warm-up history by contract.
- [x] B13 Identify which features can be fully computed from READY and which rely on insufficient warm-up.
- [ ] B14 Verify READY snapshot/session lineage around Sep-4 through Sep-10.
- [x] B15 Determine whether R2 universe membership/input snapshot changed materially around Sep-10.

B12/B13 evidence: READY is a finite 250–300 daily-bar rolling window; terminal canonical EMA uses separate long-history state, while historical finite-window EMA/Stage warm-up remains audit-relevant. B15 is closed by the Sep-10 lifecycle migration/universe-expansion diagnostic.

**Exit criterion:** every feature has an explicit minimum-history requirement and measured READY coverage.

---

# Phase C — Benchmark / external-data boundary

- [x] C1 Establish that stock OHLCV comes from R2 while SPY/QQQ/VIX/sector ETFs are downloaded separately.
- [x] C2 Inventory every external benchmark actually downloaded.
- [x] C3 Identify which downloaded benchmarks affect production decisions.
- [x] C4 Mark benchmarks/features that are calculated but `DEAD / UNUSED` in production decisions.
- [x] C5 Check benchmark latest date versus R2 latest date.
- [x] C6 Check benchmark missing-session behavior.
- [x] C7 Audit exact-date merge used by RS.
- [x] C8 Audit backward-as-of merge used by market regime.
- [x] C9 Test stale benchmark scenarios and resulting statuses.
- [x] C10 Test R2-ahead-of-benchmark scenario.
- [x] C11 Test benchmark-ahead-of-R2 scenario.
- [ ] C12 Decide whether benchmark freshness requires a governed readiness contract.

C2–C4 static evidence establishes SPY as decision-relevant, with QQQ/VIX/sector data auxiliary or unused by current Investability/Tradability. C5–C11 are covered by the successful benchmark-freshness empirical audit; C12 remains a governance decision.

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
- [x] D1.6 Check EMA initialization/warm-up sensitivity.
- [ ] D1.7 Determine intended canonical historical EMA contract.
- [x] D1.8 Add/identify invariant tests for terminal EMA lineage and ordering.

D1.6 is empirically closed by PROB-018: historical warm-up effect is real, while latest terminal trend classification was robust in 99/100 sampled symbols and production terminal EMA is separately repaired from canonical R2 EMA state. D1.8 is covered by `tests/test_r2_shared_ema.py`.

## D2 Stage Analysis

- [x] D2.1 Current weekly resampling traced.
- [x] D2.2 Current 30-week SMA traced.
- [x] D2.3 Current three-observation slope rule traced.
- [x] D2.4 Current Stage1/2/3/4 mapping traced.
- [x] D2.5 Current implementation classified as `APPROXIMATION` pending dedicated methodology audit.
- [x] D2.6 Audit weekly W-FRI labeling around market holidays.
- [x] D2.7 Verify no weekly look-ahead is introduced by resample/as-of merge.
- [ ] D2.8 Compare current Stage semantics against authoritative Weinstein methodology.
- [ ] D2.9 Enumerate missing lifecycle/context elements.
- [ ] D2.10 Quantify Stage transition stability around Sep-4–Sep-10.
- [x] D2.11 Quantify contribution of Stage transitions to Sep-10 first-time lifecycle symbols.
- [ ] D2.12 Freeze corrected Stage specification only if evidence supports a correction.

D2.6/D2.7 are closed by Evidence 08 and workflow run `35036545474` (`4 passed`). W-FRI plus backward-as-of is temporally causal: Mon–Thu cannot see the current Friday bucket. Good-Friday-style shortened weeks create a conservative calendar-label lag, not future-data leakage. D2.11 disposition: the +61 set was newly evaluated after universe expansion, so there is no valid prior legacy-engine Stage state from which to attribute a Stage transition; mass Stage-transition causality is disproven as the primary explanation.

## D3 Relative strength

- [x] D3.1 `return_63d` formula traced.
- [x] D3.2 SPY 63-session return formula traced.
- [x] D3.3 `rs_spy = stock_return_63d - spy_return_63d` traced.
- [x] D3.4 PASS/NEAR/FAIL thresholds traced.
- [ ] D3.5 Verify 63-session horizon rationale/evidence.
- [ ] D3.6 Verify PASS >=0 and NEAR >=-0.02 rationale/evidence.
- [ ] D3.7 Measure missing/NaN RS due to insufficient history.
- [x] D3.8 Measure missing/NaN RS due to benchmark-date alignment.
- [ ] D3.9 Audit split/corporate-action semantics of stock and SPY return bases.
- [x] D3.10 Quantify RS transitions Sep-4–Sep-10 and contribution to +61 case.

D3.8 is covered by benchmark freshness/alignment evidence. D3.10 has the same migration disposition as D2.11: no prior comparable state exists for the 61 newly evaluated symbols, so a mass RS transition is not the cause of first-seen persistence.

## D4 Liquidity

- [x] D4.1 `avg_volume_50d` formula traced.
- [x] D4.2 PASS >=300k / NEAR >=240k thresholds traced.
- [ ] D4.3 Verify threshold rationale/evidence.
- [ ] D4.4 Check raw-share-volume behavior around splits/corporate actions.
- [ ] D4.5 Check min-period behavior and warm-up classification.
- [x] D4.6 Quantify liquidity transitions Sep-4–Sep-10 and contribution to +61 case.

D4.6 disposition: +61 are first observations under expanded R2 coverage, not attributable legacy FAIL→qualifying transitions.

## D5 Price floor

- [x] D5.1 Raw-close price basis traced.
- [x] D5.2 PASS >=$10 / NEAR >=$8 thresholds traced.
- [ ] D5.3 Verify threshold rationale/evidence.
- [ ] D5.4 Audit corporate-action behavior.
- [x] D5.5 Quantify price transitions Sep-4–Sep-10 and contribution to +61 case.

D5.5 disposition: +61 are first observations under expanded R2 coverage, not attributable legacy FAIL→qualifying transitions.

## D6 Structure / ATR / VCP proxy

- [x] D6.1 ATR14 formula traced.
- [x] D6.2 ATR percentile 63d traced.
- [x] D6.3 `vcp_tightness = 100 - ATR percentile` traced.
- [x] D6.4 VCP label/semantics classified `MISMATCH` with literal VCP morphology.
- [ ] D6.5 Audit ATR/percentile minimum-history behavior.
- [ ] D6.6 Quantify how often `vcp_tightness >=60` occurs.
- [ ] D6.7 Determine whether field should be renamed as low-volatility/tightness proxy or replaced.
- [x] D6.8 Audit `base_length_days` formula and downstream usage.
- [x] D6.9 Mark `base_length_days` `DEAD / UNUSED` if no production consumer exists.

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
- [x] D9.3 Trace every downstream use of `hard_filter_status` and regime.
- [x] D9.4 Audit volatility regime downstream usage.
- [x] D9.5 Audit `rs_sector` downstream usage.
- [x] D9.6 Audit `rs_spy_persistence_weeks` downstream usage.
- [x] D9.7 Audit `volume_ratio` downstream usage.
- [x] D9.8 Audit `volume_dry_up` downstream usage.
- [x] D9.9 Audit ADX downstream usage.
- [x] D9.10 Audit 52-week-high-distance downstream usage.
- [x] D9.11 Mark unused features explicitly `DEAD / UNUSED` rather than treating them as signal inputs.

Static downstream trace establishes the decisioning use of hard-filter/regime and separates auxiliary/dead feature fields from current Investability/Tradability inputs.

**Exit criterion:** feature matrix is complete and every production-relevant field has a defensible, temporally valid contract.

---

# Phase E — Investability contract audit

- [x] E1 Identify Investability components: Trend + Liquidity + RS + Price.
- [x] E2 Confirm regime is excluded from Investability.
- [x] E3 Trace component PASS/NEAR/FAIL thresholds.
- [x] E4 Verify exact aggregation/non-compensation rule.
- [x] E5 Enumerate all possible component-state combinations and expected Investability output.
- [x] E6 Add table-driven tests for aggregation truth table.
- [x] E7 Check NaN/None behavior for every component.
- [x] E8 Check whether insufficient history becomes FAIL, NaN, or another state consistently.
- [ ] E9 Check whether latest-date selection can compare securities with different effective data dates.
- [x] E10 Verify candidate filter is exactly `Investability >= NEAR_PASS`.
- [x] E11 Verify lifecycle first-seen semantics use the intended Investability state.
- [x] E12 Verify alerts use intended state transitions.
- [x] E13 Verify production position registration uses intended Investability/Tradability contract.
- [ ] E14 Produce current-state Investability funnel only after upstream audit is clean.

E4–E8 are now protected by the decision-contract test gate. Run `35035424562` completed successfully: `6 passed, 8 subtests passed`. E10–E13 are closed by downstream Evidence 05; production entry intentionally uses a separate hard-filter/backtest-parity contract rather than watchlist ACTIONABLE.

**Exit criterion:** every Investability transition is reproducible from four component statuses and valid inputs.

---

# Phase F — Tradability contract audit

- [x] F1 Identify breakout requirement.
- [x] F2 Identify breakout-volume confirmation.
- [x] F3 Identify tight-structure confirmation.
- [x] F4 Trace current PASS/NEAR/FAIL aggregation.
- [x] F5 Build complete Tradability truth table.
- [x] F6 Add table-driven aggregation tests.
- [x] F7 Check NaN behavior for pivot, volume percentile, tightness.
- [ ] F8 Check minimum-history behavior.
- [x] F9 Confirm no same-bar self-reference in breakout pivot.
- [x] F10 Confirm signal availability only after T0 close.
- [x] F11 Confirm all executable evaluation uses T+1 Open where execution is modeled.
- [x] F12 Determine whether current Tradability terminology overstates O'Neil/Minervini semantics.
- [x] F13 Separate valid rolling-breakout mechanics from chart-pattern claims.

F5–F7/F9 are covered by the successful decision-contract test gate. F10–F11 are closed by downstream T0/T+1 ordering evidence. F12–F13 are closed semantically: current pivot/VCP components must not be represented as literal validated O'Neil/Minervini morphology.

**Exit criterion:** Tradability is internally coherent, temporally executable, and accurately named.

---

# Phase G — Temporal / look-ahead / as-of audit

- [ ] G1 Build a field-level table: earliest timestamp each input is knowable.
- [x] G2 Verify daily OHLCV T0 is only used for decisions after T0 close.
- [x] G3 Verify shifted pivot excludes T0 high from T0 breakout reference.
- [ ] G4 Verify rolling calculations never use future rows.
- [x] G5 Verify weekly Stage resampling does not leak future Friday information into Mon–Thu.
- [x] G6 Verify holiday-shortened weeks do not create leakage or unintended lag.
- [x] G7 Verify exact-date benchmark merge has no forward fill from future benchmark dates.
- [x] G8 Verify regime backward-as-of merge only uses same/prior benchmark state.
- [ ] G9 Verify lifecycle comparisons are as-of historical state, not recomputed with future/canonical terminal overlays.
- [x] G10 Verify backtests/research do not accidentally use terminal-only canonical EMA state for earlier dates.
- [x] G11 Verify T+1 Open execution constraint wherever signal outcomes are evaluated.

G5/G6 are closed by Evidence 08 and run `35036545474`: 4 temporal/calendar tests passed, including Good Friday and Labor Day cases. Good-Friday W-FRI labeling can conservatively delay the shortened week's Stage state until the next trading session, but does not leak future information. G2/G3/G7/G8/G11 are closed by static/empirical temporal evidence and downstream execution ordering. G10 is closed in the sense that canonical R2 EMA overlay is terminal-only; historical research remains on historical feature rows and the mismatch is explicitly governed rather than silently backfilled.

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
- [x] H4 Explicitly mark weekend dates.
- [x] H5 Explicitly mark US market holiday/non-session dates.
- [x] H6 Do not classify a non-session as missing pipeline output.
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
- [x] H17 Determine when production switched from legacy universe/path to R2 path, if relevant to this window.
- [x] H18 Determine whether any successful R2 run effectively caught up after missed/failed sessions.

H17: production switch to `r2_main.py`/R2 readiness occurred Sep-13, commit `97ea8f03a9edd4c145e53857fb83a117bab350f7`. H18: the +61 first-seen population is explained by newly evaluated R2 universe coverage rather than accumulated legacy signal transitions; it is not evidence of a Sep-10 legacy-run catch-up.

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

- [x] I1.1 Extract exact 61 first-time lifecycle symbols dated Sep-10.
- [x] I1.2 Confirm their prior lifecycle absence.
- [x] I1.3 Confirm all 61 belong to current R2 READY.
- [x] I1.4 Compare the 61 with legacy hard-coded universe.
- [x] I1.5 Determine whether they were previously evaluated by legacy production.

## I2 Causal decomposition

- [x] I2.1 Test mass Stage-transition hypothesis.
- [x] I2.2 Test mass RS-transition hypothesis.
- [x] I2.3 Test mass liquidity-transition hypothesis.
- [x] I2.4 Test mass price-transition hypothesis.
- [x] I2.5 Test benchmark-regime shift hypothesis.
- [x] I2.6 Test workflow catch-up hypothesis.
- [x] I2.7 Test universe-expansion/migration hypothesis.
- [x] I2.8 Test legacy-universe contamination hypothesis.

## I3 Disposition

- [x] I3.1 Root cause documented as `EXPLAINABLE MIGRATION / UNIVERSE-EXPANSION EFFECT`.
- [x] I3.2 Mass signal transition rejected as primary explanation.
- [x] I3.3 Legacy-universe contamination rejected.
- [x] I3.4 Diagnostic closed without production correction.

Evidence: `docs/SEP10_LIFECYCLE_DIAGNOSTIC.md`.

---

# Phase J — Findings and correction specifications

- [ ] J1 Consolidate all findings after remaining empirical/temporal checks.
- [ ] J2 Separate naming/semantic mismatches from calculation defects.
- [ ] J3 For each actual correction candidate, document root cause before code change.
- [ ] J4 Freeze intended corrected contract before validation.
- [ ] J5 Define untouched validation dataset/corpus before implementation.
- [ ] J6 Do not tune after validation result is observed.

---

# Phase K — Tests and governed validation

- [x] K1 Existing terminal canonical EMA tests identified.
- [x] K2 Investability truth-table tests added and passing.
- [x] K3 Tradability truth-table tests added and passing.
- [x] K4 T0/T+1 downstream ordering covered by static contract evidence.
- [x] K5 Benchmark stale/alignment scenarios tested empirically.
- [x] K6 Weekly Stage holiday/calendar edge cases tested.
- [ ] K7 Historical EMA consistent-basis comparison test/validation.
- [ ] K8 R2 READY empirical QC gate.
- [ ] K9 Any approved correction receives dedicated regression tests.
- [ ] K10 Untouched validation run after correction specification freeze.

K6 evidence: `tests/test_weekly_stage_temporal.py`, workflow run `35036545474`, `4 passed in 0.73s`.

---

# Phase L — Final production decision / funnel

- [ ] L1 Confirm all decision-relevant input contracts are clean or explicitly governed.
- [ ] L2 Confirm all temporal ambiguities are closed.
- [ ] L3 Confirm correction specs are frozen where needed.
- [ ] L4 Confirm regression tests pass.
- [ ] L5 Confirm untouched validation completed for any correction.
- [ ] L6 Make explicit production decision per finding: keep / rename / correct / defer.
- [ ] L7 Only after L1–L6, produce current Investability/Tradability funnel and interpret it.
- [ ] L8 Record final audit verdict and production change set (which may be empty).

---

## Current audit posture

Production remains unchanged. The audit has established the full downstream contract, empirical persistence consistency, finite R2 warm-up boundary, benchmark alignment behavior, Sep-10 migration explanation, decision truth tables, and weekly Stage temporal causality. Remaining work is concentrated in R2 empirical QC, historical EMA consistent-basis quantification/canonical-history governance, methodology/evidence questions, remaining minimum-history/frequency measurements, field-level temporal table, workflow continuity ledger, and final correction/validation governance.
