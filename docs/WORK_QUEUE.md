# USSY TrendFoll — Master Work Queue

**Repository:** `azharmz/ussy-trendfoll`  
**Branch:** `main`  
**Queue created:** 2026-10-14  
**Purpose:** single ordered entry point for the next TrendFoll work session. This queue points to the evidence/decision documents; those documents remain authoritative for technical details.

## Operating rule

At the start of a session, read this file and execute the first actionable item that is not blocked. After each item: implement only its approved scope, run relevant tests/checks, record actual evidence, update this queue and the linked checklist/evidence, then move to the next item. Never mark an item complete from a decision or code merge alone; require its stated verification. Do not mix Near-Trigger or CAND-003 research changes into current production-exit work.

### Status legend

- **NEXT** — next task to execute.
- **READY** — queued, not started.
- **ACTIVE** — accumulating or ongoing work.
- **BLOCKED/GATED** — cannot advance until stated evidence/condition exists.
- **DONE** — verified and evidence-linked.
- **CLOSED WITH LIMITATION** — work is complete, but a documented limitation remains.
- **FROZEN** — do not tune or change without new evidence and explicit governance.

---

## Ordered queue

### 1. Remove the CURRENT 45-session forced exit — **NEXT**
**Decision:** approved; **implementation: NOT VERIFIED**.

- Decision: [`DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md`](DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md)
- Baseline context: [`EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`](EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md), Section A.
- Scope: remove holding age as a standalone exit trigger from CURRENT production position management. Preserve existing stop-loss and existing technical trend-break behavior; do not tune either.
- Do **not** alter the frozen CAND-003 shadow contract's separate 45-session boundary.
- Required acceptance:
  1. Trace the complete current production exit path and remove the age-only exit condition.
  2. Check dashboard/status/summary consumers so age alone is not represented as an exit reason.
  3. Add regression tests: a position older than 45 sessions remains open when stop-loss and trend-break are both absent; stop-loss still exits; trend-break still exits.
  4. Validate an older live example such as OKTA using the actual current state/data; distinguish code-level tests from production observation.
  5. Run the relevant test suite/workflow and record commit, run IDs, test results, and any production check.
- Completion rule: update the decision document and checklist only after the evidence above exists. Until then, do not claim this change is deployed or verified.

### 2. Reconcile the workstream checklist with current evidence — **READY**
- Main checklist: [`EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`](EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md)
- PROB-017 evidence: [`EVIDENCE_PROB_017_CANONICAL_READER.md`](EVIDENCE_PROB_017_CANONICAL_READER.md)
- PROB-005 evidence: [`EVIDENCE_PROB_005.md`](EVIDENCE_PROB_005.md)
- PROB-003/004 evidence: [`EVIDENCE_PROB_003_004.md`](EVIDENCE_PROB_003_004.md)
- Reconcile stale checklist markers against the evidence before treating them as open defects:
  - **PROB-017:** code merged, production RPC applied, SQL smoke passed; user reported the dashboard now shows one ANF row. The evidence document still says independent live-deployment check pending. Record the user's observed result accurately, but do not claim independent browser/deployment verification unless performed.
  - **PROB-005:** evidence says CLOSED / EVIDENCE LOCKED; reconcile the checklist's duplicate mapped-key debt marker with that scope and evidence.
  - **PROB-003/004:** evidence says CLOSED / EVIDENCE LOCKED. Exactly-once semantic event persistence and normal replay suppression are implemented; Telegram's crash-after-acceptance window can still yield a duplicate. Treat that as a known external-delivery limitation, not as proof the whole item is unfinished.
- Keep this reconciliation documentation-only unless an actual code defect is discovered; any newly discovered defect gets a separate queue entry with evidence.

### 3. Define and govern a production correction for gap-through stop execution — **READY / SEPARATE GOVERNANCE**
- Evidence: [`EVIDENCE_STOP_EXEC_001.md`](EVIDENCE_STOP_EXEC_001.md) and [`STOP_EXEC_001_AUDIT_PROTOCOL.md`](STOP_EXEC_001_AUDIT_PROTOCOL.md).
- Finding: the current exact-stop assumption is infeasible when session Open is already below the stop. The frozen audit found 93 gap-through events among 839 CURRENT stop events in its 1,524-event paired sample.
- Diagnostic is complete; **no production correction is authorized by that finding alone**.
- Next step after item 1: write an explicit correction contract covering gap-through fill semantics, impact on position/return accounting, migrations if any, regression cases, rollout/rollback, and approval boundary. Then validate separately before changing production.
- Do not use this item to retune the 2×ATR stop or modify CAND-003.

### 4. Continue CAND-003 genuine operational shadow observation — **ACTIVE / GATED**
- Frozen sufficiency gate: [`CAND003_OPERATIONAL_EVIDENCE_SUFFICIENCY.md`](CAND003_OPERATIONAL_EVIDENCE_SUFFICIENCY.md)
- Live checklist: [`EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`](EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md), Sections D–H.
- Current known state: E1 first genuine operational session passed for the 2026-09-18 seven-position cohort. E2–E4 observation remains active; sufficiency gate has not been met.
- Continue only sequential evidence from genuine eligible production positions and sessions. No synthetic/backfilled evidence, no retrospective bootstrap, no tuning frozen parameters, and no shadow mutation of production.
- Track eligible versus represented positions, expected versus persisted sessions, missing reasons, active versus terminal shadows, exit-path representation, gap/slippage, timing/return differences, MAE/MFE where available, duplicates/replay conflicts, and all frozen invariants.
- Final governance review stays blocked until every criterion in the frozen sufficiency gate is satisfied. Passing the gate does not itself promote CAND-003 to production.

### 5. Close remaining engineering hygiene debts — **READY / AFTER HIGHER PRIORITIES**
Use the checklist's Section G and inspect the actual current code/tests before opening changes.

- **Test discovery:** verify whether any tests are undiscovered by the repository's unittest-only CI/workflows; add a reproducible discovery check or document why none exist.
- **Reporting-only quirk:** investigate legacy-reason reporting in development summary field `stop_touch_timing`; keep separate from production semantics unless evidence proves a production impact.
- **Checklist accuracy:** remove/resolve stale debt markers only when linked evidence supports closure.
- Do not bundle unrelated refactors with exit behavior changes.

### 6. Near-Trigger forward validation — **ACTIVE / SEPARATE WORKSTREAM**
- Protocol: [`NEAR_TRIGGER_RESEARCH.md`](NEAR_TRIGGER_RESEARCH.md)
- Status: DEVELOPMENT-FROZEN / SHADOW-ONLY / NOT PRODUCTION-VALIDATED.
- Accumulate the preregistered independent shadow/control episodes and matured forward windows. Do not issue PASS/FAIL before every frozen minimum-evidence requirement is met; do not tune the 0.60 ATR threshold against validation outcomes.
- Keep separate from the exit workstream and from the current 45-session removal.

---

## Closed / frozen references — do not reopen by default

| Item | Status | Evidence / boundary |
|---|---|---|
| PROB-017 canonical position history | **DONE in code/DB; user-observed dashboard result reported** | [`EVIDENCE_PROB_017_CANONICAL_READER.md`](EVIDENCE_PROB_017_CANONICAL_READER.md). ANF source rows remain intact; canonical reader selects ID 19 and excludes ID 18 from canonical history. Keep independent deployment-verification distinction clear. |
| PROB-005 mapped identity guard | **CLOSED / EVIDENCE LOCKED** | [`EVIDENCE_PROB_005.md`](EVIDENCE_PROB_005.md). Preventive READY identity/mapping guards; not a claim of exhaustive historical scans outside the documented scope. |
| PROB-003/004 alert event/delivery integrity | **CLOSED WITH LIMITATION** | [`EVIDENCE_PROB_003_004.md`](EVIDENCE_PROB_003_004.md). Semantic event idempotency and retry bookkeeping are implemented; exactly-once external Telegram delivery is impossible across the documented crash window. |
| CAND-001 / CAND-002 | **FROZEN / INVALIDATED** | Do not reopen without new evidence and explicit governance. |
| CAND-003 parameters and sufficiency criteria | **FROZEN; shadow observation active** | [`EXIT_CANDIDATE_REPRESENTATION_003.md`](EXIT_CANDIDATE_REPRESENTATION_003.md), [`CAND003_OPERATIONAL_EVIDENCE_SUFFICIENCY.md`](CAND003_OPERATIONAL_EVIDENCE_SUFFICIENCY.md). No production promotion yet. |
| STOP-EXEC-001 diagnostic | **DONE AS DIAGNOSTIC; correction not authorized** | [`EVIDENCE_STOP_EXEC_001.md`](EVIDENCE_STOP_EXEC_001.md). Production correction requires separate contract and validation. |

## Session handoff format

When work stops, update the top of the queue or the relevant item with:
- **Last completed:** item and evidence link.
- **Current item:** exact implementation/test step.
- **Last verified commit/run:** actual SHA and workflow/run ID, if applicable.
- **Next action:** one concrete action.
- **Blocker:** exact missing evidence or decision; write “none” if none.

**Current handoff:** Start at **Queue item 1**. The 45-session removal is a recorded decision, not yet verified implementation.