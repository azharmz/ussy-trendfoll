# USSY Trendfoll — Exit Workstream Progress Checklist

**Purpose:** authoritative execution checklist for the exit/risk workstream so future sessions stay on the frozen governance path instead of reopening completed research or mixing unrelated workstreams.

**Branch:** `research/exit-development-hypotheses`

**Last updated:** 2026-09-16

## Status legend

- `[x]` completed and evidence-locked
- `[~]` implemented / active but awaiting real operational evidence
- `[ ]` not completed
- `[!]` known defect/debt; separate governance required
- `[FROZEN]` do not tune/reopen without new evidence and explicit governance

## North-star governance

`PROB → DIAG → ROOT CAUSE → DEVELOPMENT → UNTOUCHED VALIDATION → SHADOW/PRODUCTION`

Rules:

- Do not tune a frozen candidate after observing outcomes.
- Do not convert a diagnostic result into a production change implicitly.
- Production exit remains authoritative until an explicit promotion decision and implementation contract exist.
- CAND-003 shadow is observational and must never submit, alter, suppress, or accelerate production exits.
- Keep Near-Trigger, Investability/Tradability engine audit, and unrelated entry work outside this checklist.

---

# A. Problem diagnosis and root cause — 100%

- [x] **PROB-013:** production-like exit performance problem identified.
- [x] **DIAG-001:** full-history entry/forward-path diagnostics completed.
- [x] **DIAG-002:** no robust monotonic entry-quality rule found; entry contract left unchanged.
- [x] **DIAG-003:** production-like exit reconstructed: T+1 Open entry, initial 2×ATR14 stop, EMA20 exit, max 45 sessions.
- [x] **RC-004:** exit/risk conversion identified as the supported problem area rather than entry quality.
- [x] **EXIT-ISO-001:** isolated current exit components.
- [x] Fixed 2×ATR stop identified as the primary harmful component in the isolation study; EMA20 was not the primary culprit.
- [x] Evidence locked in `docs/EVIDENCE_EXIT_ISO_001.md`.

**Gate:** COMPLETE. Do not reopen entry tuning from this evidence.

---

# B. Candidate development — 100%

## B1. Invalid candidates

- [x] **CAND-001** evaluated.
- [x] CAND-001 invalidated because the representation allowed impossible Chandelier fills above attainable price.
- [x] Evidence locked: `docs/EVIDENCE_EXIT_CAND_001_INVALID.md`.
- [x] **CAND-002** evaluated.
- [x] CAND-002 invalidated because gap-through stop execution was not represented correctly.
- [x] Evidence locked: `docs/EVIDENCE_EXIT_CAND_002_INVALID.md`.
- [x] CAND-001/CAND-002 marked **[FROZEN]**; do not resurrect or tune them.

## B2. CAND-003 frozen representation

- [x] Representation frozen in `docs/EXIT_CANDIDATE_REPRESENTATION_003.md`.
- [x] Entry reference = T+1 Open.
- [x] Initial stop = entry − 2×ATR14(T0).
- [x] Chandelier = HH22 − 3×Wilder ATR22.
- [x] EMA20 trend exit retained.
- [x] Observation boundary = 45 sessions.
- [x] Chandelier ratchets upward only.
- [x] Session-t Chandelier is computed only after surviving session t and arms t+1.
- [x] Gap-through ordering frozen: Open <= operative stop → fill Open (`risk_stop_gap`).
- [x] Otherwise Low <= operative stop → fill exact operative stop (`risk_stop_touch`).
- [x] No ATR/EMA/holding grids, targets, momentum cutoffs, or post-outcome optimization.

## B3. Development run

- [x] Development workflow completed successfully.
- [x] Frozen gates passed.
- [x] Development median improved versus CURRENT but remained negative.
- [x] Evidence locked: `docs/EVIDENCE_EXIT_CAND_003_DEVELOPMENT.md`.
- [x] Terminal development status: **SUPPORTED FOR UNTOUCHED VALIDATION / NOT PRODUCTION**.

**Gate:** COMPLETE / **[FROZEN]**.

---

# C. Untouched validation — 100%

- [x] Independent validation slice used (rank 101–200 versus development rank 1–100).
- [x] Development/validation overlap = 0.
- [x] Frozen CAND-003 semantics preserved.
- [x] All validation criteria passed.
- [x] Candidate median improved versus CURRENT in untouched validation.
- [x] Candidate median remained negative; validation does not authorize production replacement.
- [x] Evidence locked: `docs/EVIDENCE_EXIT_CAND_003_VALIDATION.md`.
- [x] Terminal status: **DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION**.

**Gate:** COMPLETE / **[FROZEN]**.

---

# D. Production-shadow design and implementation — 100%

## D1. Frozen shadow plan

- [x] Shadow plan frozen: `docs/EXIT_CAND_003_PRODUCTION_SHADOW_PLAN.md`.
- [x] Shadow contract version = `exit-cand-003-shadow-v1`.
- [x] Production architecture remains authoritative.
- [x] Shadow is non-decisioning.
- [x] Required operational invariants defined.
- [x] Monitoring outputs defined as observational, not optimization targets.

## D2. Shadow state engine

- [x] `exit_candidate003_shadow.py` implemented.
- [x] Shadow state persistence deployed separately from production position state.
- [x] R2 production pipeline invokes shadow after authoritative production exit/registration path.
- [x] Frozen initial stop, Chandelier, EMA20, 45-session boundary, gap/touch ordering implemented.
- [x] No production exit-policy change introduced.

## D3. Append-only per-session evidence ledger

- [x] Missing session-ledger requirement identified.
- [x] Implementation specification added: `docs/CAND003_SHADOW_SESSION_LEDGER_IMPLEMENTATION.md`.
- [x] Supabase table `exit_candidate003_shadow_sessions` deployed.
- [x] Unique invariant `(position_id, session_date, contract_version)` enforced.
- [x] Session OHLC persisted.
- [x] Operative stop before session persisted.
- [x] HH22 / Wilder ATR22 / session Chandelier persisted.
- [x] Next-session ratcheted stop persisted.
- [x] Hypothetical exit reason/price persisted.
- [x] Production comparison fields persisted observationally.
- [x] Identical replay is idempotent.
- [x] Divergent duplicate evidence fails closed.
- [x] Gap-before-touch ordering covered.
- [x] No same-day Chandelier look-ahead covered.
- [x] Tests converted/implemented so repository `unittest discover` actually discovers CAND-003 tests.
- [x] Dedicated CI completed successfully; 9/9 ledger tests passed on tested code/schema head.
- [x] RLS enabled and least-privilege grants verified.
- [x] Supabase security advisor returned zero findings after deployment.
- [x] Unindexed foreign-key advisor finding resolved.
- [x] PR #11 merged into `research/exit-development-hypotheses`.
- [x] Merge commit: `42012d17a9e382ea5d3341a4dab1e21f5aca3907`.
- [x] No synthetic live evidence inserted.

**Gate:** IMPLEMENTATION COMPLETE.

---

# E. Operational shadow evidence — ACTIVE / approximately 0% of observation phase

This is now the **PRIMARY EXIT WORKSTREAM**. Do not start a new exit candidate while this phase is pending.

## E1. First-real-session gate

- [ ] Confirm the first real `exit_candidate003_shadow_sessions` row is produced by an actual production-shadow session.
- [ ] Confirm row corresponds to a real production position and real R2 market session.
- [ ] Confirm `(position_id, session_date, contract_version)` uniqueness in live operation.
- [ ] Confirm no synthetic/test row exists in the operational ledger.
- [ ] Recompute one first-session row independently from its inputs and compare all persisted values.
- [ ] Verify operative stop used on session t existed before session t.
- [ ] Verify session-t Chandelier only affects `next_operative_stop`, never session-t stop execution.
- [ ] Verify gap-before-touch execution against actual OHLC.
- [ ] Verify production comparison fields did not alter production state.
- [ ] Record evidence document for the first operational session.

## E2. Coverage and data-quality monitoring

- [ ] Track number of eligible production positions versus positions represented in shadow state.
- [ ] Track number of expected position-sessions versus persisted ledger rows.
- [ ] Calculate shadow coverage rate.
- [ ] Calculate missing-data rate and enumerate missing-data reasons.
- [ ] Confirm no duplicate invariant keys.
- [ ] Confirm no divergent replay events.
- [ ] Confirm no stop-decrease invariant failures.
- [ ] Confirm no same-day Chandelier look-ahead failures.
- [ ] Confirm no touch fill outside observed low/high.
- [ ] Confirm no shadow computation mutates production position/exit state.

## E3. Frozen observational metrics

Accumulate only the metrics specified by the frozen shadow plan; do not add optimization grids.

- [ ] Shadow exit-reason mix: `risk_stop_gap` / `risk_stop_touch` / `trend_exit` / `observation_boundary`.
- [ ] Gap-through frequency.
- [ ] Gap slippage versus operative stop.
- [ ] Timing difference versus production exit.
- [ ] Realized-return difference versus production exit when both exits are observable.
- [ ] MAE/MFE to shadow exit where data are available.
- [ ] Invariant-failure counts.
- [ ] Duplicate/replay-conflict counts.

## E4. Operational evidence sufficiency gate

**No arbitrary observation count is invented here.** Before declaring shadow observation complete, create an explicit governance note defining evidence sufficiency from operational coverage/data quality, not from which outcome looks better.

- [ ] Define and evidence-lock operational sufficiency criteria without inspecting/tuning candidate parameters.
- [ ] Reach the locked sufficiency criteria.
- [ ] Produce an operational shadow evidence report.
- [ ] Freeze the operational dataset/evidence snapshot used for governance review.

**Gate:** PENDING REAL DATA.

---

# F. STOP-EXEC-001 — diagnostic complete; production correction NOT authorized

- [x] Audit protocol frozen: `docs/STOP_EXEC_001_AUDIT_PROTOCOL.md`.
- [x] Diagnostic runner/workflow completed.
- [x] Exact-stop execution feasibility defect confirmed for CURRENT production-like comparator.
- [x] Gap-through events quantified.
- [x] Gap slippage quantified.
- [x] Evidence locked: `docs/EVIDENCE_STOP_EXEC_001.md`.
- [x] Terminal diagnostic status: **CURRENT EXACT-STOP EXECUTION FEASIBILITY DEFECT OBSERVED**.
- [!] Production CURRENT gap-through correction has **not** been governed or implemented.
- [ ] Create a separate production-correction contract if/when this debt is prioritized.
- [ ] Define migration/rollback and tests for CURRENT execution semantics.
- [ ] Validate correction independently before production deployment.

**Important:** STOP-EXEC-001 must not be silently folded into CAND-003 promotion.

---

# G. Engineering debts relevant to exit workstream

- [x] CAND-003 test-discovery mismatch fixed for the session-ledger CI path.
- [!] Verify repository-wide tests do not still contain undiscovered bare pytest-style functions under a unittest-only workflow.
- [!] CAND-003 development summary helper previously reported `stop_touch_timing.stop_events=0` because it expected legacy reason `risk_stop`; this is reporting-only debt and must not be interpreted as zero stop events.
- [!] Duplicate production position key remains a separate engineering debt.
- [!] Alert-event idempotency/same-day transition resend remains separate from exit candidate science.
- [!] Duplicate mapped `(symbol,date)` guard remains separate engineering debt.

These debts may be fixed under engineering governance but must not alter the frozen CAND-003 scientific representation.

---

# H. Final governance review — NOT STARTED

This phase begins only after Section E has sufficient locked operational evidence.

- [ ] Review development evidence.
- [ ] Review untouched-validation evidence.
- [ ] Review operational shadow execution feasibility and data quality.
- [ ] Review invariant/operational failure rate.
- [ ] Explicitly account for the still-negative median CAND-003 return in both development and validation.
- [ ] Review STOP-EXEC-001 independently so CURRENT comparator semantics are understood.
- [ ] Decide one terminal path without tuning v1:
  - keep CURRENT and continue shadow observation;
  - reject/archive CAND-003 v1;
  - authorize a separately governed production implementation of CAND-003 v1;
  - define a genuinely new candidate/version under a new development cycle.
- [ ] If production change is authorized, create explicit implementation contract.
- [ ] Create migration plan.
- [ ] Create rollback plan.
- [ ] Add production tests and monitoring.
- [ ] Deploy only after explicit governance approval.

**Current authorization:** `NO PRODUCTION EXIT CHANGE`.

---

# I. Workstreams explicitly OUT OF SCOPE here

Do not let these interrupt the exit checklist unless an evidence dependency is demonstrated:

- Investability/Tradability engine semantic audit.
- Sep-10 lifecycle +61 investigation.
- Near-Trigger forward validation.
- Entry-rule changes.
- New breakout/pivot/VCP definitions.
- Market-regime research.
- Universe membership changes.

Those belong to their own governance/workstreams.

---

# J. Current marker / next action

**Current marker:**

`RC-004 SUPPORTED → EXIT-CAND-003 DEVELOPMENT PASS → UNTOUCHED VALIDATION PASS → PRODUCTION SHADOW IMPLEMENTED → APPEND-ONLY SESSION LEDGER DEPLOYED + CI PASS → OPERATIONAL SHADOW EVIDENCE ACTIVE → NO PRODUCTION CHANGE`

**NEXT ACTION — do this before any new exit research:**

1. Wait for the first genuine production-shadow eligible session.
2. Query `exit_candidate003_shadow_sessions`.
3. If no row exists, diagnose whether there were zero eligible production positions versus an operational ingestion failure; do not manufacture evidence.
4. When the first real row exists, execute Section E1 completely and evidence-lock the result.
5. Continue Sections E2–E4 until the predeclared operational sufficiency gate is met.

## Approximate progress indicator

For navigation only, not scientific evidence:

- Problem/root-cause diagnosis: **100%**
- Candidate development: **100%**
- Untouched validation: **100%**
- Shadow design/implementation/persistence: **100%**
- Operational shadow observation: **0% / awaiting real evidence**
- Final production governance: **0% / blocked on operational evidence**

The previously quoted ~85% refers to completion through implementation relative to the immediate CAND-003 workstream. Do not mechanically recompute project completion by averaging the percentages above.