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
- [x] G0.8 No correction is implemented until its root cause and intended contract are documented.
- [x] G0.9 Every approved correction receives tests before production decision.
- [x] G0.10 Any validation dataset used for a correction remains untouched after the correction specification is frozen.

G0.8–G0.10 are satisfied for FSE-013. Evidence 10 froze the refined contract before implementation; research regression passed; validation V1 was retained unchanged after its harness defect was observed; V2 corrected only the fixture contract before first execution and then passed 5/5 untouched tests. This does **not** authorize production integration; the explicit production decision remains open.

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
- [x] B4 Establish actual READY history depth distribution per security.
- [x] B5 Record minimum / median / maximum bars per security.
- [x] B6 Count securities with <20, <50, <60, <63, <150, <200, <252 bars.
- [x] B7 Check first/last market date consistency across securities.
- [x] B8 Check duplicate `(security_id,date)` rows.
- [x] B9 Check missing OHLCV / adj_close fields by security/date.
- [x] B10 Check nonpositive/invalid price or volume facts.
- [x] B11 Check corporate-action-sensitive raw-vs-adjusted continuity.
- [x] B12 Determine whether current READY is a rolling finite window or carries sufficient warm-up history by contract.
- [x] B13 Identify which features can be fully computed from READY and which rely on insufficient warm-up.
- [ ] B14 Verify READY snapshot/session lineage around Sep-4 through Sep-10.
- [x] B15 Determine whether R2 universe membership/input snapshot changed materially around Sep-10.

B4–B11 are closed by Evidence 09 and R2 READY QC run `35046652834`: 367,499 rows, 1,227 securities, 250–300 bars/security, zero duplicate `(security_id,date)`, zero missing required facts, zero basic invalid OHLCV, and 31 raw/adjusted-ratio events across 18 securities. Evidence 12 additionally establishes that Sep-14 terminal volume was materially incomplete upstream; the Sep-15 post-refresh diagnostic normalized, while historical Sep-14 same-date reconciliation remains open. B12/B13: READY is a finite 250–300 daily-bar rolling window; terminal canonical EMA uses separate long-history state. B15 is closed by the Sep-10 migration diagnostic.

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

D2.6/D2.7 are closed by Evidence 08 and workflow run `35036545474` (`4 passed`). W-FRI plus backward-as-of is temporally causal. D2.11: the +61 set was newly evaluated after universe expansion, so mass Stage-transition causality is disproven as the primary explanation.

## D3 Relative strength

- [x] D3.1 `return_63d` formula traced.
- [x] D3.2 SPY 63-session return formula traced.
- [x] D3.3 `rs_spy = stock_return_63d - spy_return_63d` traced.
- [x] D3.4 PASS/NEAR/FAIL thresholds traced.
- [ ] D3.5 Verify 63-session horizon rationale/evidence.
- [ ] D3.6 Verify PASS >=0 and NEAR >=-0.02 rationale/evidence.
- [ ] D3.7 Measure missing/NaN RS due to insufficient history.
- [x] D3.8 Measure missing/NaN RS due to benchmark-date alignment.
- [x] D3.9 Audit split/corporate-action semantics of stock and SPY return bases.
- [x] D3.10 Quantify RS transitions Sep-4–Sep-10 and contribution to +61 case.

D3.9 is closed by Evidence 11: on the 18-security corporate-action-sensitive population, stock RS on `adj_close` is consistent with the intended corporate-action-adjusted return basis; 30/31 events showed >5pp raw-vs-adjusted 1d return gaps and 23/31 >5pp at 63d, confirming why raw returns would be inappropriate here. D3.10 retains the migration disposition.

## D4 Liquidity

- [x] D4.1 `avg_volume_50d` formula traced.
- [x] D4.2 PASS >=300k / NEAR >=240k thresholds traced.
- [ ] D4.3 Verify threshold rationale/evidence.
- [x] D4.4 Check raw-share-volume behavior around splits/corporate actions.
- [ ] D4.5 Check min-period behavior and warm-up classification.
- [x] D4.6 Quantify liquidity transitions Sep-4–Sep-10 and contribution to +61 case.

D4.4 is empirically closed by Evidence 11: raw-share-volume 50d windows can mix structurally incomparable pre/post share-count units around splits. Classification remains `MISMATCH`; FSE-014 requires a governed correction specification before production change. D4.6 retains the migration disposition.

## D5 Price floor

- [x] D5.1 Raw-close price basis traced.
- [x] D5.2 PASS >=$10 / NEAR >=$8 thresholds traced.
- [ ] D5.3 Verify threshold rationale/evidence.
- [x] D5.4 Audit corporate-action behavior.
- [x] D5.5 Quantify price transitions Sep-4–Sep-10 and contribution to +61 case.

D5.4 is closed by Evidence 11: the raw-close floor is a valid explicit nominal current-price USSY definition; it should not be reinterpreted as a corporate-action-adjusted historical-price rule. D5.5 retains the migration disposition.

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

Evidence 12 confirms the mass terminal low-percentile anomaly was caused by incomplete Sep-14 upstream volume, not by the percentile formula: after refreshed finalized Sep-15 READY, below-all-prior50 fell from 933/1,223 to 19/1,220 and median current/prior-50-median normalized from ~0.152 to ~1.077. D8.4–D8.6 remain open pending clean finalized-volume comparison and methodology governance; thresholds must not be tuned to compensate for upstream defects.

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
- [x] E9 Check whether latest-date selection can compare securities with different effective data dates.
- [x] E10 Verify candidate filter is exactly `Investability >= NEAR_PASS`.
- [x] E11 Verify lifecycle first-seen semantics use the intended Investability state.
- [x] E12 Verify alerts use intended state transitions.
- [x] E13 Verify production position registration uses intended Investability/Tradability contract.
- [ ] E14 Produce current-state Investability funnel only after upstream audit is clean.

E4–E8 are protected by decision-contract tests. E9 is closed by Evidence 10: common-date selection is correct, and FSE-013 now has refined research implementation, regression PASS, and untouched validation V2 5/5 PASS. E10–E13 are closed by downstream Evidence 05. Production integration remains pending explicit decision.

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

G5/G6 are closed by Evidence 08 and run `35036545474`; G2/G3/G7/G8/G11 by static/empirical temporal evidence and downstream execution ordering. G10 is closed in the sense that canonical R2 EMA overlay is terminal-only; historical mismatch remains explicitly governed.

**Exit criterion:** zero unresolved look-ahead/as-of ambiguity.

---

# Phase H — Sep-4 to Sep-10 workflow continuity audit

Diagnostic target: explain the Sep-10 lifecycle jump without presuming anomaly.

Known run-history evidence already observed: Sep-4 failure; Sep-5 failure; Sep-8 success; Sep-9 failure; Sep-10 legacy `main.py` run reached market date 2026-09-09 with 0/197 candidates and later failed during position tracking on non-JSON-compliant `NaN`.

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

H17: production switch to `r2_main.py`/R2 readiness occurred Sep-13, commit `97ea8f03a9edd4c145e53857fb83a117bab350f7`. H18: the +61 first-seen population is explained by newly evaluated R2 universe coverage rather than accumulated legacy signal transitions.

**Exit criterion:** session-by-session continuity ledger explains what did and did not execute/persist.

---

# Phase I — Sep-10 +61 lifecycle diagnostic

Established facts: cumulative lifecycle before Sep-10 100; first-time lifecycle +61; cumulative 161; current Investability >= NEAR_PASS 85; all 161 historical lifecycle symbols belong to current R2 READY; legacy-only 0.

## I1 Reconstruct the population
- [x] I1.1 Extract exact 61 first-time lifecycle symbols dated Sep-10.
- [x] I1.2 Verify each symbol's first-seen timestamp/date.
- [x] I1.3 Verify none had an earlier lifecycle record under another identifier/ticker mapping.
- [x] I1.4 Confirm security-ID/ticker mapping consistency.
- [x] I1.5 Confirm all 61 are present in the relevant R2 READY snapshot, not merely current READY.

## I2 Reconstruct prior observable state
- [x] I2.1 Find last valid observable session before Sep-10.
- [x] I2.2 Record prior `trend_status`.
- [x] I2.3 Record prior `stage`.
- [x] I2.4 Record prior `ema_stack_aligned`.
- [x] I2.5 Record prior `rs_status` and `rs_spy`.
- [x] I2.6 Record prior `liquidity_status` and underlying average volume.
- [x] I2.7 Record prior `price_status` and raw close.
- [x] I2.8 Record prior `investability_status`.
- [x] I2.9 Record Sep-10 values for the same fields.
- [x] I2.10 Record data date/lineage for both observations.

I2 disposition: prior state for the +61 is `NOT EVALUATED / OUTSIDE LEGACY UNIVERSE`, not a fabricated per-component FAIL state.

## I3 Attribute first qualifying transition
- [x] I3.1 Classify `Trend FAIL -> NEAR/PASS` only.
- [x] I3.2 Classify `RS FAIL -> NEAR/PASS` only.
- [x] I3.3 Classify `Liquidity FAIL -> NEAR/PASS` only.
- [x] I3.4 Classify `Price FAIL -> NEAR/PASS` only.
- [x] I3.5 Classify multiple simultaneous component changes.
- [x] I3.6 Separate `Stage` change from EMA-stack change within Trend transitions.
- [x] I3.7 Identify symbols whose prior state is unavailable because pipeline did not persist it.
- [x] I3.8 Distinguish genuine first qualification from first observed/persisted qualification after a continuity gap.
- [x] I3.9 Produce counts and symbol lists for every transition category.

I3 verdict: all 61 belong to `NOT PREVIOUSLY EVALUATED / UNIVERSE EXPANSION`.

## I4 Test causal hypotheses
- [x] I4.1 HYP-MARKET.
- [x] I4.2 HYP-PIPELINE.
- [x] I4.3 HYP-R2-SNAPSHOT.
- [x] I4.4 HYP-CODE.
- [x] I4.5 HYP-CONFIG.
- [x] I4.6 HYP-FEATURE.
- [x] I4.7 HYP-WARMUP.
- [x] I4.8 HYP-STAGE.
- [x] I4.9 HYP-EMA.
- [x] I4.10 HYP-RS.
- [x] I4.11 HYP-OTHER.

I4 verdict: migration/universe expansion is supported as primary cause; mass market/Stage/EMA/RS transition hypotheses are disproven as primary cause.

## I5 Reproducibility verdict
- [x] I5.1 Re-run/reconstruct Sep-10 decision state from immutable inputs if available.
- [x] I5.2 Compare reconstructed 85 current qualifying symbols with persisted state.
- [x] I5.3 Compare reconstructed first-time set with persisted +61.
- [x] I5.4 Explain every discrepancy.
- [x] I5.5 Record `EXPLAINABLE / NO DEFECT FOUND` when supported.
- [x] I5.6 Create numbered finding if a defect contributed.
- [x] I5.7 Preserve mixed causality if present.

I5 verdict: `EXPLAINABLE MIGRATION / UNIVERSE-EXPANSION EFFECT / NO SIGNAL-ENGINE DEFECT FOUND FOR +61`.

---

# Phase J — Findings register and correction candidates

- [ ] J1 Re-evaluate severity/classification after empirical checks.
- [x] J2 Add any workflow-continuity finding from Sep-4–Sep-10.
- [x] J3 Add any lifecycle-state-machine/persistence finding.
- [x] J4 Add any R2 warm-up/readiness defect.
- [ ] J5 Add any benchmark-freshness defect.
- [ ] J6 Add any temporal/look-ahead defect.
- [ ] J7 Add any NaN handling defect affecting production decision/persistence.
- [x] J8 Separate naming/semantic mismatches from computational bugs.
- [x] J9 For each actionable finding, document affected fields and downstream impact.
- [ ] J10 For each correction candidate, document intended contract before code change.
- [ ] J11 Rank correction execution by dependency/severity, not by convenience.
- [ ] J12 Freeze correction specification before validation.

J3 includes FSE-013; its refined intended contract, implementation, regression, and untouched validation are complete, with production decision pending. FSE-014 records corporate-action-sensitive raw-volume windows and still requires correction specification. FSE-015 records upstream READY volume completeness; Sep-15 finalization normalized but historical Sep-14 reconciliation remains open. Production remains unchanged.

**Exit criterion:** no unresolved high-severity production-relevant finding without an explicit disposition.

---

# Phase K — Test and validation gate

- [ ] K1 Unit tests for every corrected formula.
- [x] K2 Truth-table tests for Investability.
- [x] K3 Truth-table tests for Tradability.
- [x] K4 NaN/insufficient-history tests.
- [ ] K5 Corporate-action/raw-vs-adjusted tests where applicable.
- [x] K6 Weekly Stage calendar/holiday tests.
- [x] K7 Benchmark stale/missing-session tests.
- [x] K8 Temporal no-look-ahead tests.
- [x] K9 T+1 Open execution tests for event-level evaluation.
- [x] K10 Lifecycle idempotency tests.
- [x] K11 First-seen persistence tests.
- [ ] K12 Failed-run/rerun recovery tests.
- [ ] K13 Regression test reproducing Sep-10 diagnostic case where immutable inputs permit.
- [ ] K14 Development sample completed before untouched validation.
- [ ] K15 Correction frozen before validation.
- [ ] K16 Untouched validation executed once under governance.
- [ ] K17 No post-validation tuning without new governed cycle.
- [x] K18 R2 READY empirical QC gate.
- [x] K19 Effective-date alert-state regression tests.
- [x] K20 Effective-date candidate-lifecycle regression tests.

K2–K4: run `35035424562` SUCCESS. K6: run `35036545474` SUCCESS. K18: run `35046652834` SUCCESS. K19–K20 are strengthened by refined FSE-013 runs `35063691151` (12/12 contract PASS) and `35063901480` (contract + downstream regression PASS). FSE-013 untouched validation V2 run `35066531313`, job `104697955901`, passed 5/5. K14–K17 remain open at the **full correction-set** level because other actionable findings have not yet completed their governed cycles; they are satisfied specifically for FSE-013.

**Exit criterion:** approved correction set passes tests and governed validation.

---

# Phase L — Final production decision and post-audit funnel

- [ ] L1 Summarize engine components classified MATCH / VALID / APPROXIMATION / MISMATCH / BUG / UNUSED.
- [x] L2 Summarize Sep-10 lifecycle diagnostic verdict with evidence.
- [ ] L3 Document remaining known limitations.
- [ ] L4 Explicit production decision for each correction candidate: adopt / defer / reject.
- [ ] L5 Production code change only after explicit decision.
- [ ] L6 Re-run full test suite after production integration.
- [ ] L7 Run current R2 READY funnel only after signal engine is clean enough for interpretation.
- [ ] L8 Report current counts by Trend, RS, Liquidity, Price, Investability, Tradability.
- [ ] L9 Establish ongoing health checks for R2 freshness, benchmark freshness, NaN, and lifecycle jumps.
- [ ] L10 Close audit with immutable evidence references/commit SHAs.

L2 verdict: Sep-10 +61 is an explainable migration/universe-expansion effect, not evidence of a mass signal transition or signal-engine defect.

---

# Progress summary

Checklist completion: **203 / 269 = 75.5%**.

| Phase | Area | Status |
|---|---|---|
| G0 | Governance | IN PROGRESS — FSE-013 governance through untouched validation complete; production decision pending |
| A | Production execution map | COMPLETE AT CODE-CONTRACT LEVEL — empirical persisted-row consistency separate |
| B | R2 input/readiness | IN PROGRESS — empirical QC complete; B14 and FSE-015 historical Sep-14 reconciliation remain |
| C | Benchmark boundary | IN PROGRESS — static + empirical alignment complete; governance decision pending |
| D | Feature formulas | IN PROGRESS — corporate-action empirical checks D3.9/D4.4/D5.4 closed; remaining methodology/quantification work open |
| E | Investability | IN PROGRESS — aggregation/effective-date correction validated; final funnel pending |
| F | Tradability | IN PROGRESS — truth table/causality tested; minimum-history and terminology governance remain |
| G | Temporal/look-ahead | IN PROGRESS — daily/pivot/benchmark/weekly Stage/T+1 checks closed; field-level table and historical lifecycle-as-of remain |
| H | Sep-4–Sep-10 workflow continuity | IN PROGRESS — migration cause known; complete run ledger still pending |
| I | Sep-10 +61 diagnostic | COMPLETE — explainable migration/universe expansion |
| J | Findings/corrections | IN PROGRESS — FSE-013 validated; FSE-014/FSE-015 and remaining findings require disposition |
| K | Tests/validation | IN PROGRESS — FSE-013 untouched validation PASS; full correction-set validation not yet complete |
| L | Production decision/funnel | BLOCKED BY REMAINING AUDIT/CORRECTION GOVERNANCE |

## Audit completion rule

The audit is **not complete** merely because all formulas have been read. Completion requires:

`input contract -> formula -> temporal semantics -> downstream consumer -> empirical behavior -> finding classification -> correction specification (if any) -> tests -> governed validation -> explicit production decision`.

The Sep-10 lifecycle case is closed as `EXPLAINABLE MIGRATION / UNIVERSE-EXPANSION EFFECT`; remaining audit work must not reopen it without contradictory evidence.

## Synchronization note — 2026-09-16

Synchronized Evidence 11 corporate-action closures (D3.9/D4.4/D5.4), Evidence 12 post-refresh volume-completeness result, and the completed FSE-013 refined correction/regression/untouched-validation chain. G0.10 is now closed by the governed validation discipline demonstrated in Evidence 10. K14–K17 remain open globally because the full correction set is not yet through validation. Production remains unchanged.