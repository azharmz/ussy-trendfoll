# Decision — Remove CURRENT TrendFoll Maximum Holding Period

**Decision date:** 2026-10-14  
**Authority:** explicit user decision in the TrendFoll work session  
**Status:** DECISION RECORDED / IMPLEMENTATION NOT VERIFIED

## Decision

Remove the fixed **45-day / 45-trading-session maximum holding-period exit** from the CURRENT production TrendFoll position-management path.

An open position must not be exited solely because it has reached a holding-age threshold. Exits should instead follow the existing governed exit mechanisms, namely:

- stop-loss; and
- the existing technical trend-break / trend-deterioration exit.

This decision does not authorize changing the stop-loss parameters or redefining the existing trend-break signal. It removes the time-based forced exit only.

## Scope boundary

- Applies to CURRENT production TrendFoll position management and its dashboard/status representation.
- Does **not** silently rewrite the frozen `EXIT-CAND-003` shadow/research contract. That contract retains its own frozen 45-session boundary unless separately governed.
- Does not resolve the separate `STOP-EXEC-001` gap-through execution-feasibility defect.

## Required implementation verification

1. Find and remove the maximum-holding-age exit from the production decision path.
2. Confirm no downstream/dashboard consumer treats holding age alone as an exit reason.
3. Add regression coverage proving a position older than 45 sessions remains open when neither the existing stop-loss nor trend-break exit fires.
4. Confirm existing stop-loss and trend-break exits still fire normally.
5. Verify the production position and dashboard for a long-held example such as OKTA.
6. Update the exit-workstream checklist and production evidence only after verification.

## Important status distinction

This document records the decision; it does **not** claim the code change or production verification is complete. Until implementation and regression evidence are recorded, status remains **DECISION RECORDED / IMPLEMENTATION NOT VERIFIED**.
