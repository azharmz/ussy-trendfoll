# Full Signal Engine Audit — Evidence 10: Effective-Date State Semantics

Status: **ROOT CAUSE + CORRECTION SPECIFICATION FROZEN / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Trigger

Evidence 09 found four READY securities whose terminal row was older than the global latest market date. This evidence follows that condition through the downstream production path before any correction is implemented.

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

## Downstream semantic consequence

Absence from the current snapshot is not neutral in every downstream consumer.

### Alerts / watchlist state

The alert-state path evaluates previously monitored symbols against the full current latest universe. A previously monitored symbol that is absent from that universe can be emitted as `INVALIDATED`.

### Candidate lifecycle

The lifecycle path likewise derives current monitored/actionable state from the current latest universe. A historical lifecycle symbol absent from the current snapshot is no longer currently monitored.

### Active positions

The position path is stricter. Active-position coverage is validated against the current snapshot before exit processing; missing current coverage causes a fail-fast condition rather than silently applying an older bar.

## Root cause

The current state model conflates two materially different reasons for a previously monitored symbol being absent from the current snapshot:

1. **Signal invalidation** — a current-date row exists and current Investability falls below the monitoring threshold.
2. **Data unavailability / stale terminal data** — no current-date row exists, so the signal cannot be evaluated for the current effective date.

The common-date snapshot selection itself is correct. The semantic defect is downstream: absence of current data can be represented as signal invalidation even though no current-date signal evaluation occurred.

Classification: **MISMATCH — DATA UNAVAILABLE CAN BE CONFLATED WITH SIGNAL INVALIDATION**.

This is not evidence that the four observed stale securities had valid signals. It establishes that the current state machine cannot distinguish the two causes from the resulting absence alone.

## Frozen intended contract

The correction, if approved after tests and governed validation, must preserve these invariants:

1. Current cross-sectional decisions use one common `as_of_date` only.
2. A stale historical row must never be substituted as a current signal row.
3. `INVALIDATED` must mean that a current-date evaluation exists and the current signal state invalidates monitoring.
4. Absence of a current-date row must be represented separately as **data unavailable/stale**, not as signal invalidation.
5. Data-unavailable state must not create a new actionable/entry signal.
6. Existing historical watchlist/lifecycle facts must remain immutable; the new state describes current evaluability, not a rewrite of past observations.
7. Active positions must retain fail-closed/fail-fast protection when current market data required for position management is absent.
8. No change may weaken T0-close / T+1-open execution semantics.

## Correction boundary

The smallest intended correction surface is the current-state/lifecycle/alert semantic layer. It does **not** require changing:

- R2 OHLCV facts,
- feature formulas,
- Investability aggregation,
- Tradability aggregation,
- terminal EMA calculation,
- production entry formula,
- historical persisted observations.

A concrete implementation must not be merged to production until the tests below are added and pass.

## Required pre-implementation tests

At minimum, tests must prove:

1. prior monitored + current row present + Investability below `NEAR_PASS` => `INVALIDATED`;
2. prior monitored + no current-date row because source is stale/unavailable => distinct data-unavailable state, **not** `INVALIDATED`;
3. data-unavailable symbol cannot become `ACTIONABLE` or create a production entry;
4. stale older row cannot be used as current state;
5. current row restored on a later run resumes ordinary state evaluation without rewriting historical facts;
6. active-position missing-current-data protection remains fail-closed/fail-fast;
7. ordinary current-date alert/lifecycle transitions are regression-equivalent to existing behavior.

## Governance disposition

This document satisfies the root-cause/intended-contract prerequisite for this specific finding under G0.8. It does **not** authorize a production correction by itself.

Next gate:

`frozen correction spec -> tests against current behavior/spec -> implementation on research branch -> regression -> untouched governed validation -> explicit production decision`

No production mutation was made.