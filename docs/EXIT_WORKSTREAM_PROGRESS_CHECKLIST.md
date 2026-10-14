# USSY Trendfoll — Exit Workstream Progress Checklist

**Purpose:** authoritative execution checklist for the exit/risk workstream so future sessions stay on the frozen governance path instead of reopening completed research or mixing unrelated workstreams.

**Branch:** `main`

**Last updated:** 2026-10-14

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
- [x] **DIAG-003:** production-like exit reconstructed: T+1 Open entry, initial 2×ATR14 stop, EMA20 exit. Current production has no maximum holding-period exit; see `docs/DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md`.
- [x] **RC-004:** exit/risk conversion identified as the supported problem area rather than entry quality.
- [x] **EXIT-ISO-001:** isolated current exit components.
- [x] Fixed 2×ATR stop identified as the primary harmful component in the isolation study; EMA20 was not the primary culprit.
- [x] Evidence locked in `docs/EVIDENCE_EXIT_ISO_001.md`.

**Gate:** COMPLETE. Do not reopen entry tuning from this evidence.

---

# B. Candidate development — 100%

## B1. Invalid candidates

- [x] **CAND-001** evaluated and invalidated; evidence locked.
- [x] **CAND-002** evaluated and invalidated; evidence locked.
- [x] CAND-001/CAND-002 **[FROZEN]**.

## B2. CAND-003 frozen representation

- [x] Representation frozen in `docs/EXIT_CANDIDATE_REPRESENTATION_003.md`.
- [x] Entry reference = T+1 Open.
- [x] Initial stop = entry − 2×ATR14(T0).
- [x] Chandelier = HH22 − 3×Wilder ATR22.
- [x] EMA20 retained; boundary 45 sessions; Chandelier ratchets upward only.
- [x] Session-t Chandelier arms only t+1.
- [x] Gap-before-touch execution frozen.
- [x] No post-outcome optimization.

**Gate:** COMPLETE / **[FROZEN]**.

---

# C. Untouched validation — 100%

- [x] Independent validation slice with zero development overlap.
- [x] Frozen semantics preserved and validation gates passed.
- [x] Candidate improved versus CURRENT but median remained negative.
- [x] Evidence locked: `docs/EVIDENCE_EXIT_CAND_003_VALIDATION.md`.
- [x] Terminal status: **DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION**.

**Gate:** COMPLETE / **[FROZEN]**.

---

# D. Production-shadow design and implementation — 100%

- [x] Frozen shadow plan and `exit-cand-003-shadow-v1` contract.
- [x] Shadow is non-decisioning and state is separate from production positions.
- [x] Append-only `exit_candidate003_shadow_sessions` ledger deployed with unique `(position_id, session_date, contract_version)` invariant.
- [x] Replay/idempotency, gap-before-touch and no-same-day-lookahead tests implemented.
- [x] RLS/least-privilege/security verification completed.
- [x] Governed research branch promoted to `main`; daily production path can execute the shadow.
- [x] Initial operational smoke run exposed a late-bootstrap defect: historical positions were registered long after T+1 and evaluated as if sequential.
- [x] Defect patched so a new shadow may bootstrap only on its genuine first observable T+1 session; late bootstrap is rejected.
- [x] Regression CI passed after the bootstrap fix.
- [x] Post-fix production-pipeline acceptance run `35035406879` completed successfully.
- [x] 27 pre-fix ledger rows were retained as audit evidence and classified as invalid/quarantined bootstrap evidence; they are not admissible Section E evidence.
- [x] Post-fix acceptance created no additional contaminated operational evidence and duplicate invariant keys remained zero.
- [x] First normal scheduled post-fix production run `35041036914` completed successfully and created no retrospective/contaminated shadow evidence.

**Gate:** IMPLEMENTATION + BOOTSTRAP ACCEPTANCE COMPLETE.

---

# E. Operational shadow evidence — ACTIVE / E1 COMPLETE

This is the **PRIMARY EXIT WORKSTREAM**. Do not start a new exit candidate while this phase is pending.

## E0. Operational evidence boundary

- [x] First smoke execution performed through the real daily production pipeline.
- [x] Smoke execution discovered a real bootstrap defect before E1 was accepted.
- [x] Bootstrap defect corrected without changing frozen CAND-003 scientific parameters.
- [x] Post-fix production acceptance passed.
- [x] Normal scheduled production execution after the fix passed.
- [x] Pre-fix 27 ledger rows explicitly excluded from admissible operational evidence.
- [x] Clean operational evidence count after scheduled run = **0**.
- [x] No synthetic/backfilled row may be used to satisfy E1.
- [x] Next admissible evidence must originate from a newly registered production position observed on its genuine T+1 market session.

## E1. First-real-session gate

- [x] Confirm first admissible post-fix `exit_candidate003_shadow_sessions` rows were produced by an actual production-shadow T+1 session (2026-09-18; seven-position cohort).
- [x] Confirm rows correspond to real production positions and real R2 market session.
- [x] Confirm `(position_id, session_date, contract_version)` uniqueness in live operation: 7 rows / 7 unique keys.
- [x] Confirm rows are not among the 27 quarantined bootstrap rows and are not synthetic/test evidence.
- [x] Recompute admissible rows independently from inputs and compare persisted values.
- [x] Verify operative stop used on session t existed before session t.
- [x] Verify session-t Chandelier affects only `next_operative_stop`; IOVA provides a live ratchet boundary case.
- [x] Verify gap-before-touch execution against actual OHLC.
- [x] Verify production comparison fields did not alter production state.
- [x] Evidence locked in `docs/EVIDENCE_EXIT_CAND_003_E1_FIRST_REAL_SESSION.md`.

## E2. Coverage and data-quality monitoring

- [ ] Track eligible production positions versus positions represented in clean shadow state.
- [ ] Track expected position-sessions versus admissible persisted ledger rows.
- [ ] Calculate clean shadow coverage and missing-data rate/reasons.
- [ ] Confirm no duplicate invariant keys or divergent replay events.
- [ ] Confirm no stop-decrease or same-day-lookahead invariant failures.
- [ ] Confirm no touch fill outside observed OHLC.
- [ ] Confirm shadow computation never mutates production position/exit state.

## E3. Frozen observational metrics

- [ ] Exit-reason mix.
- [ ] Gap-through frequency and slippage.
- [ ] Timing difference versus production exit.
- [ ] Realized-return difference when both exits are observable.
- [ ] MAE/MFE to shadow exit where available.
- [ ] Invariant-failure and duplicate/replay-conflict counts.

## E4. Operational evidence sufficiency gate

- [x] Define and evidence-lock operational sufficiency criteria without inspecting/tuning candidate parameters: `docs/CAND003_OPERATIONAL_EVIDENCE_SUFFICIENCY.md`.
- [x] Sufficiency gate explicitly excludes the 27 invalid-bootstrap rows and requires genuine sequential T+1 evidence, lifecycle completeness for terminal comparisons, invariant integrity, comparator non-feedback, outcome maturity, and multiple independent entry cohorts.
- [x] No favorable return/win-rate/candidate-superiority threshold is used as a sufficiency condition.
- [ ] Reach locked sufficiency criteria.
- [ ] Produce operational shadow evidence report.
- [ ] Freeze operational dataset/evidence snapshot used for governance review.

**Gate:** E1 COMPLETE / E2–E4 ACTIVE. Continue natural sequential observation; no production exit change.

---

# F. STOP-EXEC-001 — diagnostic complete; production correction NOT authorized

- [x] Diagnostic completed and exact-stop execution feasibility defect confirmed.
- [x] Evidence locked: `docs/EVIDENCE_STOP_EXEC_001.md`.
- [x] Gap-aware fill implementation exists in repository main from commit `d213fd491975f8d9aaeb6116fef7eef837fd7cb5`; focused regression workflow passed in run `38552916021`.
- [x] Read-only schema/consumer compatibility audit recorded in `docs/STOP_EXEC_001_CORRECTION_CONTRACT_DRAFT.md`; no new status/schema migration indicated.
- [ ] Independent live deployment verification and observation of a real post-fix gap-through exit remain pending.

**Important:** STOP-EXEC-001 must not be silently folded into CAND-003 promotion.

---

# G. Engineering debts relevant to exit workstream

- [x] CAND-003 test-discovery mismatch fixed for session-ledger CI.
- [x] CAND-003 late-bootstrap operational defect fixed and regression-tested.
- [x] Repository-wide test discovery fixed with `.github/workflows/repository-tests.yml`; full suite passed 104 tests. Evidence: `docs/EVIDENCE_REPOSITORY_TEST_DISCOVERY.md`.
- [x] CAND-003 `stop_touch_timing` reporting-only quirk fixed and regression-tested; detailed `risk_stop_gap` / `risk_stop_touch` reasons remain distinct.
- [x] Duplicate production position identity resolved through the PROB-017 canonical ledger-aware reader; see `docs/EVIDENCE_PROB_017_CANONICAL_READER.md`.
- [x] Alert-event persistence/idempotency and retry bookkeeping implemented; residual Telegram crash-window duplicate limitation is documented in `docs/EVIDENCE_PROB_003_004.md`.
- [x] PROB-005 READY identity/mapping guard closed; see `docs/EVIDENCE_PROB_005.md`.

---

# H. Final governance review — NOT STARTED

Blocked until Section E has sufficient locked operational evidence. Current authorization remains **NO PRODUCTION EXIT CHANGE**.

---

# I. Workstreams explicitly OUT OF SCOPE here

- Investability/Tradability engine semantic audit.
- Sep-10 lifecycle +61 investigation.
- Near-Trigger forward validation.
- Entry-rule changes.
- New breakout/pivot/VCP definitions.
- Market-regime research.
- Universe membership changes.

---

# J. Current marker / next action

**Current marker:**

`RC-004 SUPPORTED → CAND-003 DEVELOPMENT PASS → UNTOUCHED VALIDATION PASS → SHADOW + APPEND-ONLY LEDGER DEPLOYED → BOOTSTRAP DEFECT FOUND/FIXED → REGRESSION + PRODUCTION ACCEPTANCE PASS → 27 PRE-FIX ROWS QUARANTINED → PRE-OUTCOME OPERATIONAL SUFFICIENCY GATE FROZEN → FIRST GENUINE T+1 COHORT 2026-09-18 → E1 PASS / EVIDENCE LOCKED → E2–E4 OBSERVATION ACTIVE → NO PRODUCTION EXIT CHANGE`

**NEXT ACTION:**

1. CURRENT repository audit and regression coverage are merged (PR #17, `d5c04e884958befb5c7ab550c4720282a7e354f5`); workflow run `38552916021` passed. Live deployment / OKTA row check remains pending.
2. Checklist/evidence reconciliation completed in master queue item 2; PROB-017 now distinguishes the user's dashboard observation from independent live verification.
3. STOP-EXEC-001 current-source compatibility audit complete; gap-aware fill is already in repository main, but live deployment verification remains pending.
4. Repository-wide test discovery and CAND-003 reporting-only quirk are fixed; full suite passed 104 tests. See `docs/EVIDENCE_REPOSITORY_TEST_DISCOVERY.md`.
5. Independently verify live deployment and the long-held OKTA row when production read access is available.
6. Separately, let the normal daily pipeline continue; do not manufacture or backfill CAND-003 operational evidence. Continue E2–E4 only on genuine sequential sessions.

## Approximate progress indicator

- Problem/root-cause diagnosis: **100%**
- Candidate development: **100%**
- Untouched validation: **100%**
- Shadow implementation + bootstrap acceptance: **100%**
- Operational sufficiency criteria definition: **100% / frozen pre-outcome**
- Operational shadow observation: **E1 complete; 7 clean first-session rows / E2–E4 active**
- Final production governance: **0% / blocked on operational evidence**
