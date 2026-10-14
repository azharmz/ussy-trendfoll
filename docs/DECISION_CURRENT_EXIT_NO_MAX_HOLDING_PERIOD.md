# Decision — Remove CURRENT TrendFoll Maximum Holding Period

**Decision date:** 2026-10-14  
**Authority:** explicit user decision in the TrendFoll work session  
**Status:** VERIFIED IN REPOSITORY CODE + REGRESSION TESTS / LIVE DEPLOYMENT NOT INDEPENDENTLY VERIFIED

## Decision

Remove the fixed **45-day / 45-trading-session maximum holding-period exit** from the CURRENT production TrendFoll position-management path.

An open position must not be exited solely because it has reached a holding-age threshold. Exits should instead follow the existing governed exit mechanisms, namely:

- stop-loss; and
- the existing technical trend-break / trend-deterioration exit.

This decision does not authorize changing the stop-loss parameters or redefining the existing trend-break signal. It removes the time-based forced exit only.

## Repository audit and implementation result (2026-10-14)

A source audit of `positions.py::check_exits` found that the current production exit function already has no age-based exit branch. The only use of `days_held` in that function is to calculate and persist the holding-duration metric when a position exits. If neither stop-loss nor `close_raw < ema20` is triggered, the position remains active and its mark/MFE/MAE fields are updated.

The dashboard's `days_held` field is displayed as a duration; it is not used as an exit decision. The `max_holding` CSS badge selector is a presentation artifact and is not referenced by the production exit decision path.

This work therefore adds regression coverage for the behavior rather than removing a live max-age conditional that is not present in the current source:
- A position held for 51 trading sessions remains active when stop-loss and trend-break are both absent.
- The existing trend-break exit still fires when `close_raw < ema20` and the stop is not touched.
- Existing stop-loss execution tests continue to cover stop exits.

**Verification boundary:** this establishes repository behavior and test coverage. It does not independently prove which commit is currently deployed to the live dashboard, nor does it independently inspect the live OKTA row. The user's reported OKTA age of 47 calendar days is consistent with an age display and is not by itself evidence of a forced exit.

## Scope boundary

- Applies to CURRENT production TrendFoll position management and its dashboard/status representation.
- Does **not** silently rewrite the frozen `EXIT-CAND-003` shadow/research contract. That contract retains its own frozen 45-session boundary unless separately governed.
- Does not resolve the separate `STOP-EXEC-001` gap-through execution-feasibility defect.

## Validation record

- [x] Audited `positions.py::check_exits`: no max-age exit condition found.
- [x] Audited dashboard references: `days_held` is rendered as a metric, not an exit rule.
- [x] Added regression test for a 51-trading-session open position with no exit signal.
- [x] Added regression test confirming trend-break exit remains active.
- [x] CI/workflow passed: Gap-aware stop execution regression #21, run `38552916021`.
- [x] PR #17 merged to `main` at `d5c04e884958befb5c7ab550c4720282a7e354f5`.
- [ ] Independent live deployment / OKTA row verification.

Do not mark the live deployment check complete until that check is actually performed.