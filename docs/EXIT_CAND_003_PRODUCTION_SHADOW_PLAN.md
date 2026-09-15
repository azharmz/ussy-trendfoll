# EXIT-CAND-003 — PRODUCTION SHADOW PLAN

Status: **DESIGN ONLY / VALIDATION-SUPPORTED / NO PRODUCTION EXIT CHANGE**

Prerequisite evidence:
- `docs/EVIDENCE_EXIT_CAND_003_DEVELOPMENT.md`
- `docs/EVIDENCE_EXIT_CAND_003_VALIDATION.md`

EXIT-CAND-003 has passed development and untouched validation, but its median realized return remains negative in both samples. Therefore production replacement is not authorized. The next phase is a non-decisioning shadow implementation that measures operational behavior without changing live position exits.

## Boundary
Production architecture remains unchanged:

`R2 READY → TREND CANDIDATE → INVESTABILITY → TRADABILITY → ALERT`

Existing production position/exit decisions remain authoritative. EXIT-CAND-003 shadow outputs must never submit, alter, suppress, or accelerate a production exit.

## Shadow computation
For each eligible production position/signal instance, compute and persist alongside the existing production state:
- T+1 Open entry reference where applicable;
- ATR14(T0);
- frozen initial stop = entry − 2 × ATR14(T0);
- frozen HH22 and Wilder ATR22 inputs;
- frozen Chandelier = HH22 − 3 × Wilder ATR22;
- operative stop before each session;
- any next-session ratchet after surviving day t;
- hypothetical exit reason: `risk_stop_gap`, `risk_stop_touch`, `trend_exit`, or `observation_boundary`;
- hypothetical exit price and date;
- production exit reason/price/date for comparison.

No candidate parameter is configurable in the shadow path.

## Required operational invariants
Fail closed and flag the shadow record if:
- candidate stop decreases;
- same-day Chandelier affects same-day stop execution;
- gap exit is not filled at observed Open;
- touch fill lies outside observed daily low/high;
- shadow computation changes production state;
- duplicate `(position identity, session date, shadow contract version)` records occur.

## Shadow contract version
Use a distinct immutable identifier, e.g. `exit-cand-003-shadow-v1`, tied to the frozen representation and validation evidence. Any semantic change requires a new contract ID and new governance review; do not silently mutate v1.

## Monitoring outputs
Track counts and distributions, not optimization grids:
- shadow coverage and missing-data rate;
- candidate exit-reason mix;
- gap-through frequency and gap slippage versus operative stop;
- timing difference versus production exit;
- realized-return difference versus production exit when both are observable;
- MAE/MFE to each exit;
- invariant failures and duplicate records.

These metrics are observational. They must not be used to tune EXIT-CAND-003 under the same candidate ID.

## Promotion boundary
Shadow operation alone does not authorize production promotion. A later governance decision must explicitly consider:
1. development + untouched validation evidence;
2. shadow execution feasibility/data quality;
3. operational failure rate;
4. the still-negative median candidate return;
5. the separate `STOP-EXEC-001` audit so production CURRENT execution semantics are understood independently.

Any production change requires its own implementation contract, migration/rollback plan, tests, and explicit evidence lock.

## Separate workstreams
Do not mix this shadow with:
- near-trigger forward validation;
- entry-rule changes;
- investability attribution;
- regime research;
- duplicate-position engineering debt;
- CURRENT gap-through semantics audit (`STOP-EXEC-001`).