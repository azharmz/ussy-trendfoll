# EXIT-CAND-003 — Divergence & Stop-Fill Audit (2026-10-14)

Status: **CODE AUDIT PARTIAL / PRODUCTION UNCHANGED**

## Scope

Read-only follow-up after the untouched validation gate. No production strategy, positions, or database rows were modified.

## Production stop execution contract

Inspection of `positions.py` on `main` confirms production currently implements:

- Stop is evaluated from daily `low_raw <= stop_price`.
- If `open_raw <= stop_price`, fill at observed Open (`gap_open`).
- Otherwise, if Low touches the stop, fill at stop (`stop_touch`).
- If no stop triggers, EMA20 trend exit is `close_raw < ema20`, filled at Close.
- There is no fixed 45-day holding exit in `positions.check_exits`; `days_held` is recorded as a metric only.

This is gap-aware production execution. The validation report explicitly notes that its frozen CURRENT comparator still used legacy theoretical stop fills; the comparison therefore does not isolate the candidate's strategy effect from the comparator execution-model difference.

## Material contract mismatch found

The observational `exit_candidate003_shadow.py` still defines `MAX_HOLDING_DAYS = 45` and emits `observation_boundary` after 45 sessions. Its unit test also asserts that value. In contrast, production `positions.py` has no max-holding exit, consistent with the previously stated direction to exit on stop-loss or trend break only.

The frozen validation report contains 48 `observation_boundary` candidate exits. Therefore, the validation result should not be treated as evidence for a fully no-time-limit candidate. Removing this boundary from the existing shadow contract would reinterpret already-recorded v1 evidence; it must be handled as a new shadow contract/version with an explicit evidence cutover, not by silently editing v1 semantics or rewriting old rows.

## Previously observed shadow/production divergences

The prior read-only operational audit found four cases where the shadow had exited while production still showed the position active. Those are observational differences, not by themselves evidence that either exit is better. Do not publish position-level symbols, prices, or returns in this shared research repository.

The production code review establishes the execution rules above, but a fresh row-level query for those four cases could not be completed in this pass. Consequently, no new conclusion is made about the individual divergence causes or whether a given daily bar was processed identically by both systems.

## Required next controls before productionization

1. Reconcile the comparator under a single, explicit executable fill contract: gap-through stop at Open; intraday stop touch at stop; EMA20 close exit at Close.
2. Preserve the frozen validation result as historical evidence; do not retroactively patch its comparator or tune the candidate after seeing the holdout.
3. Resolve the 45-session shadow boundary through a versioned contract and explicit cutover. Do not overwrite v1 evidence.
4. Re-run the focused shadow tests and a forward-only observational cohort under the resolved contract.
5. Keep production exits and positions unchanged until the above controls are satisfied and a separate productionization decision is recorded.

## Verification limits

This note records source-code inspection and the previously completed aggregate operational audit. No fresh database rows were written. The attempted read-only SQL query was blocked by the execution safety layer, so row-level divergence diagnosis remains **NOT YET VALIDATED**.
