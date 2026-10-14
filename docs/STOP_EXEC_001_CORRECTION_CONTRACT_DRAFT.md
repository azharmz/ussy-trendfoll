# STOP-EXEC-001 — CURRENT Gap-Through Correction Contract (Proposal)

**Created:** 2026-10-14  
**Status:** **DRAFT FOR GOVERNANCE REVIEW / NOT APPROVED / NO PRODUCTION CHANGE**  
**Evidence:** [`EVIDENCE_STOP_EXEC_001.md`](EVIDENCE_STOP_EXEC_001.md)  
**Protocol:** [`STOP_EXEC_001_AUDIT_PROTOCOL.md`](STOP_EXEC_001_AUDIT_PROTOCOL.md)

## 1. Problem statement

The locked audit found 93 gap-through events in 839 CURRENT stop events within 1,524 paired events. For a gap-through session, the observed session Open is already below the operative stop. Recording a fill at the stop price is not executable under the audited daily-OHLC model.

This is an execution-price representation defect. It is **not** evidence to change the 2×ATR stop distance, EMA20 trend-break definition, entry rule, or frozen CAND-003 candidate.

## 2. Proposed production semantics

Keep the existing stop trigger and precedence, but distinguish the actual fill price:

1. Read the operative stop that was established before the current session; do not use a stop first computed from the current session to trigger a same-session exit.
2. If `open_raw <= operative_stop`, exit at observed `open_raw` and classify the reason as `stop_loss_gap`.
3. Else, if `low_raw <= operative_stop`, exit at the operative stop and classify the reason as `stop_loss` (ordinary intraday stop touch). Preserve the existing canonical reason unless downstream compatibility review approves a separate reason.
4. Else, do not trigger a stop exit; preserve existing trend-break and mark/MFE/MAE behavior.
5. Never record a stop fill above the observed Open when Open has already gapped below the stop. Do not infer intraday path beyond daily OHLC.

This proposal changes fill representation only. It does not change stop placement or the rule for when the stop becomes operative.

## 3. Compatibility and data contract review required before implementation

Before approval, trace every consumer of `exit_price`, `status` / `exit_reason`, `exit_date`, `days_held`, realized return/PnL, Telegram alerts, dashboard labels, summaries, and any backtest/forward-test reconciliation.

Decisions required:
- Whether `status = stop_loss_gap` is accepted by all status filters and reporting paths, or whether a separate `exit_reason` field is needed while preserving a stable terminal status.
- Whether existing rows/schema constraints or RPCs enumerate allowed exit statuses/reasons.
- How actual fill price is used in realized return and downstream performance metrics.
- Whether any historical records are migrated. Default proposal: **no backfill and no rewriting historical production rows**; change behavior only for new exits after a governed cutover.
- Whether the dashboard/alerts display a distinct gap-through label without breaking existing stop-loss grouping.
- Whether the new rule affects idempotent alert event identity or duplicate transition handling.

No schema migration is assumed necessary; confirm through the consumer/schema audit before implementation.

## 4. Required validation before production authorization

Add deterministic regression cases covering at least:

1. `open_raw < stop` and `low_raw <= open_raw`: fill at Open, never at stop; gap-specific reason is propagated consistently.
2. `open_raw == stop`: fill at Open (equal to stop) under the proposed `<=` boundary.
3. `open_raw > stop` and `low_raw <= stop`: fill at stop with existing ordinary-stop semantics.
4. `low_raw > stop`: no stop exit.
5. Gap-through and trend-break conditions on the same bar: stop takes precedence, with fill at Open.
6. A stop calculated/ratcheted from session-t data is not allowed to trigger on session t if the frozen production contract says it becomes operative on t+1.
7. Non-stop trend-break exit still behaves as before.
8. Existing replay/idempotency and notification tests continue to pass.
9. Realized return uses the actual selected fill price, including adverse gaps.
10. Regression guard that the 2×ATR stop placement and unrelated entry behavior have not changed.

Run relevant focused tests and full repository CI/test-discovery checks. Report exact test commands, counts, CI run IDs, and commit SHA. Compare the frozen audit's expected affected class (gap-through only) against a deterministic test fixture; do not retune parameters to improve aggregate performance.

## 5. Rollout and rollback

- No production deploy until the contract is approved and validation evidence is recorded.
- Deploy through the repository's normal governed merge/workflow; inspect the first real post-deploy gap-through exit if one occurs.
- Monitor exit reason distribution, fill price versus Open/stop/Low, return accounting, dashboard rendering, alert delivery and replay conflicts.
- Rollback means reverting the code change to the previous execution behavior for subsequent events only. Do not rewrite already persisted exits automatically.
- If a new reason/status would violate existing schema/reporting assumptions, stop and resolve compatibility before deployment.

## 6. Explicit non-goals

- No change to 2×ATR14 stop distance.
- No change to EMA20 trend-break logic.
- No max-holding-period policy change beyond the separately recorded CURRENT decision.
- No modification to frozen CAND-003 parameters, sufficiency criteria, or shadow ledger.
- No backtest-driven parameter optimization and no production database mutation as part of the diagnostic.

## 7. Approval gates

- [ ] Consumer/schema compatibility audit complete.
- [ ] Proposed reason/status representation explicitly chosen.
- [ ] Regression tests implemented and passing.
- [ ] Full relevant CI and test-discovery validation passing.
- [ ] Rollout/rollback checklist reviewed.
- [ ] Explicit authorization to implement/deploy recorded.

**Current next action:** complete the read-only consumer/schema compatibility audit and bring back concrete findings. Until the approval gates are met, this document is a proposal only.
