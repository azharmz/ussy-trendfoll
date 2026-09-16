# Full Signal Engine Audit — Evidence 10: Effective-Date State Semantics

Status: **ROOT CAUSE + REFINED CORRECTION SPECIFICATION FROZEN / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Trigger

Evidence 09 found four READY securities whose terminal row was older than the global latest market date. This evidence follows that condition through the downstream production path before any production correction is authorized.

## Observed input condition

R2 READY guarantees sufficient rolling history but does not currently guarantee that every READY security has a row on the global latest market date.

Observed snapshot from Evidence 09:

- global latest market date: `2026-09-14`
- stale-terminal READY securities: 4 / 1,227
- `ZTEK`: last row `2026-09-10`
- `WILC`: last row `2026-09-03`
- `JFB`: last row `2026-09-03`
- `YYGH`: last row `2026-09-11`

## Production selection behavior

`r2_main.py` establishes one global `as_of_date` from the maximum feature-store date and constructs the current snapshot using only rows whose `date == as_of_date`.

Therefore stale-terminal READY securities are **not** compared cross-sectionally using their older terminal rows. They are absent from the current decision snapshot.

Classification for E9 cross-sectional comparison risk: **MATCH / COMMON EFFECTIVE DATE ENFORCED BY CURRENT SNAPSHOT SELECTION**.

The production entry point also retains a separate `universe` derived from every ticker in current R2 READY and computes `missing_latest = universe - latest`. This means the information needed to distinguish current-universe membership from common-date evaluability already exists at the orchestration layer.

## Downstream semantic consequence

Absence from the current snapshot is not neutral in every downstream consumer.

### Alerts / watchlist state

The alert-state path compares the prior persisted watchlist snapshot with the common-date `latest` decision frame. The research correction introduced `DATA_UNAVAILABLE` for a previous symbol absent from `latest`.

However, `compute_alert_transitions()` receives `latest` and previous watchlist only. It does **not** receive current READY-universe membership. Therefore it cannot distinguish:

- a symbol that is still in current READY but lacks a common-date row; from
- a historical watchlist symbol that is no longer a member of current READY.

### Candidate lifecycle

The lifecycle path has the same information loss. `build_candidate_lifecycle(history, latest)` treats every historical symbol absent from `latest` as `DATA_UNAVAILABLE`, but receives no current READY-universe membership set.

### Persisted watchlist source

`database.get_previous_watchlist()` retrieves the latest prior persisted watchlist snapshot by date. The persisted rows contain signal/state facts but no current-universe membership classification. Membership therefore must come from the current R2 READY contract, not be inferred from watchlist history.

### Active positions

The position path is stricter. Active-position coverage is validated against the current snapshot before exit processing; missing current coverage causes a fail-fast condition rather than silently applying an older bar. This protection must remain unchanged.

## Root cause

The original state model conflated signal invalidation with absence of a current-date row. The first research correction separated `INVALIDATED` from `DATA_UNAVAILABLE`, but subsequent trace exposed a second distinction that the current function interfaces cannot represent.

Three materially different cases must be kept separate:

1. **Signal invalidation** — the symbol is evaluable on the common current date and Investability falls below the monitoring threshold.
2. **Data unavailable / stale terminal data** — the symbol remains a member of current READY, but has no row on the common current date.
3. **Out of current universe** — the historical/watchlist symbol is not a member of current READY and therefore is not part of the current evaluation universe.

The common-date snapshot selection itself is correct. The remaining semantic defect is downstream information loss: absence from `latest` alone cannot distinguish cases 2 and 3.

Classification: **MISMATCH — CURRENT SNAPSHOT ABSENCE IS UNDER-SPECIFIED WITHOUT CURRENT-UNIVERSE MEMBERSHIP**.

This finding does not assert why any particular security left or entered the universe. It freezes only the state semantics required to avoid interpreting universe membership changes as signal invalidation or data staleness.

## Refined frozen intended contract

The correction, if approved after tests and governed validation, must preserve these invariants:

1. Current cross-sectional decisions use one common `as_of_date` only.
2. A stale historical row must never be substituted as a current signal row.
3. `INVALIDATED` means a current-date evaluation exists and current Investability is below the monitoring threshold.
4. `DATA_UNAVAILABLE` means the symbol is a member of **current R2 READY universe** but lacks a row on the common current effective date.
5. A historical/watchlist symbol that is **not a member of current R2 READY universe** must use a separate non-signal state, frozen here as `OUT_OF_UNIVERSE`.
6. `OUT_OF_UNIVERSE` is not `INVALIDATED`: no current signal evaluation occurred.
7. `OUT_OF_UNIVERSE` is not `DATA_UNAVAILABLE`: current READY does not claim the symbol as a current member whose latest-session fact is missing.
8. Neither `DATA_UNAVAILABLE` nor `OUT_OF_UNIVERSE` may create `ACTIONABLE`, a new watch signal, or a production entry.
9. Existing historical watchlist/lifecycle facts remain immutable; current state describes present evaluability/membership only.
10. Restoration of a current-universe/current-date row resumes ordinary signal evaluation without rewriting historical facts.
11. Re-entry into the current READY universe is evaluated from current facts; historical lifecycle identity may be retained, but prior signal state must not be substituted for current evaluation.
12. Active positions retain fail-closed/fail-fast protection when current market data required for position management is absent, regardless of membership reason, unless a separately governed position-management contract explicitly changes that behavior.
13. No change may weaken T0-close / T+1-open execution semantics.

## Correction boundary

The smallest intended correction surface is:

- orchestration: pass current READY-universe membership to state/lifecycle consumers;
- alert-state semantics: distinguish current-member/no-current-row from no-longer-current-member;
- candidate lifecycle semantics: preserve the same distinction;
- tests: explicitly cover both absence causes.

It does **not** require changing:

- R2 OHLCV facts,
- feature formulas,
- Investability aggregation,
- Tradability aggregation,
- terminal EMA calculation,
- production entry formula,
- historical persisted observations.

No production merge is authorized by this document.

## Required research-branch tests

At minimum, tests must prove:

1. prior monitored + current row present + Investability below `NEAR_PASS` => `INVALIDATED`;
2. prior monitored + still in current READY universe + no current-date row => `DATA_UNAVAILABLE`;
3. prior monitored + absent from current READY universe => `OUT_OF_UNIVERSE`;
4. neither absence state can become `ACTIONABLE` or create a production entry;
5. stale older row cannot be used as current state;
6. current row restored on a later run resumes ordinary state evaluation without rewriting historical facts;
7. universe re-entry is evaluated from current facts rather than stale prior signal state;
8. active-position missing-current-data protection remains fail-closed/fail-fast;
9. ordinary current-date alert/lifecycle transitions remain regression-equivalent to existing behavior.

The existing 8-test effective-date suite validates the first-stage `INVALIDATED` versus `DATA_UNAVAILABLE` correction but does not provide current-universe membership and therefore does not yet validate this refined three-way contract.

## Governance disposition

This refined document satisfies the root-cause/intended-contract prerequisite under G0.8 for the newly exposed universe-membership distinction. The previous research implementation is now explicitly **incomplete**, not production-ready.

Next gate:

`refined frozen correction spec -> research tests that expose the missing distinction -> research implementation -> regression -> untouched governed validation -> explicit production decision`

No production mutation was made.