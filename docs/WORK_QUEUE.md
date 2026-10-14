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

### 1. Remove the CURRENT 45-session forced exit — **REPOSITORY VERIFIED; LIVE DEPLOYMENT CHECK PENDING**
**Decision:** approved. Source audit found no age-only exit branch in current `positions.py`; regression workflow passed and changes merged in PR #17 (`d5c04e884958befb5c7ab550c4720282a7e354f5`). Live deployment is not independently verified.

- Decision: [`DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md`](DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md)
- Baseline context: [`EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`](EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md), Section A.
- Scope: remove holding age as a standalone exit trigger from CURRENT production position management. Preserve existing stop-loss and existing technical trend-break behavior; do not tune either.
- Do **not** alter the frozen CAND-003 shadow contract's separate 45-session boundary.
- Required acceptance:
  1. [x] Trace `positions.py::check_exits`; no age-only exit condition exists in the current repository code.
  2. [x] Check dashboard consumer: `days_held` is displayed as a metric; no age-based dashboard exit decision was found.
  3. [x] Regression tests added and passed in workflow run `38552916021` (Gap-aware stop execution regression #21); existing stop-loss regression remains in place.
  4. [ ] Verify an older live example such as OKTA using current production data; distinguish code-level tests from production observation.
  5. [x] Workflow run `38552916021` succeeded; PR #17 merged as `d5c04e884958befb5c7ab550c4720282a7e354f5`.
- Current finding: repository source already lacked the age-only exit; regression coverage is merged and CI passed. **Remaining limitation:** live deployment and OKTA row are not independently verified. Proceed to Queue item 2 while treating live verification as a separate pending check.

### 2. Reconcile the workstream checklist with current evidence — **DONE**
- Main checklist: [`EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`](EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md)
- PROB-017 evidence: [`EVIDENCE_PROB_017_CANONICAL_READER.md`](EVIDENCE_PROB_017_CANONICAL_READER.md)
- PROB-005 evidence: [`EVIDENCE_PROB_005.md`](EVIDENCE_PROB_005.md)
- PROB-003/004 evidence: [`EVIDENCE_PROB_003_004.md`](EVIDENCE_PROB_003_004.md)
- Reconcile stale checklist markers against the evidence before treating them as open defects:
  - **PROB-017:** reconciled. Code merged, production RPC applied, SQL smoke passed, and the user observed only one ANF row on the dashboard. Independent browser/deployment verification remains pending; see updated evidence document.
  - **PROB-005:** reconciled. Checklist marks the mapped-key guard complete and preserves the documented limitation that no bucket-wide historical scan was performed.
  - **PROB-003/004:** reconciled. Checklist marks persistence/idempotency complete; Telegram's crash-after-acceptance duplicate remains a documented external-delivery limitation.
- Keep this reconciliation documentation-only unless an actual code defect is discovered; any newly discovered defect gets a separate queue entry with evidence.

### 3. Reconcile STOP-EXEC-001 with current gap-aware implementation — **REPOSITORY AUDIT DONE; LIVE VERIFICATION PENDING**
- Evidence: [`EVIDENCE_STOP_EXEC_001.md`](EVIDENCE_STOP_EXEC_001.md) and [`STOP_EXEC_001_AUDIT_PROTOCOL.md`](STOP_EXEC_001_AUDIT_PROTOCOL.md).
- Current implementation/compatibility audit: [`STOP_EXEC_001_CORRECTION_CONTRACT_DRAFT.md`](STOP_EXEC_001_CORRECTION_CONTRACT_DRAFT.md).
- Finding: the current exact-stop assumption is infeasible when session Open is already below the stop. The frozen audit found 93 gap-through events among 839 CURRENT stop events in its 1,524-event paired sample.
- Historical diagnostic is complete. A follow-up audit found the gap-aware correction already exists in `positions.py` from commit `d213fd491975f8d9aaeb6116fef7eef837fd7cb5`.
- [x] Current source fill semantics, schema status field, alert label, dashboard grouping and realized-return consumer audited read-only.
- [x] Focused regression tests passed in workflow run `38552916021` on 2026-10-14.
- [ ] Independently verify live daily pipeline/dashboard deployment and observe a real post-fix gap-through exit if/when one occurs.
- No further code or schema migration is indicated by the current repository audit. Do not use this item to retune the 2×ATR stop or modify CAND-003.

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

**Current handoff (2026-10-14):** Queue item 1 repository audit/regression is merged and CI-passed; independent live deployment/OKTA verification remains pending. Queue item 2 evidence reconciliation is complete. Queue item 3 confirms gap-aware fill is already present in repository main and focused regression CI passed; independent live verification remains pending. Next actionable queue work is item 5 engineering hygiene (test discovery and reporting-only quirk), while CAND-003 observation continues independently. Do not change production execution semantics without new evidence.