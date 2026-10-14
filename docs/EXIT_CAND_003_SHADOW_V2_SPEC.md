# EXIT-CAND-003 Shadow v2 — No Time-Based Exit Contract

Status: **SPECIFIED / NOT DEPLOYED / NO PRODUCTION CHANGES**

## Purpose

Define a separately versioned observational contract that follows the user's stated exit policy: exit only on risk stop or EMA20 trend break; do not use a fixed 45-session holding exit. Preserve all v1 rows and their original meaning.

## Frozen parameters retained

- Initial stop: realistic entry minus 2 × ATR14 measured at T0.
- Chandelier: highest high over 22 sessions minus 3 × Wilder ATR22.
- Stop ratchets upward only; never decreases.
- The Chandelier calculated from session T is armed for session T+1; no same-session look-ahead.
- Gap-through stop has priority and fills at Open.
- Intraday stop touch fills at operative stop.
- If neither stop triggers, EMA20 close break exits at Close.
- No fixed maximum holding period and no observation-boundary exit.
- Missing/incomplete OHLC data does not synthesize an exit.

## Versioning and data isolation

- New contract identifier: `exit-cand-003-shadow-v2`.
- Existing v1 records, session ledger, and validation artifact remain immutable historical evidence.
- Live database constraints were checked read-only and PASS: `exit_candidate003_shadow` has UNIQUE `(position_id, contract_version)`; `exit_candidate003_shadow_sessions` has UNIQUE `(position_id, session_date, contract_version)`. These support version-isolated v2 rows without a schema migration.
- The row-level session/production divergence query was blocked by the tool safety layer, so the four cases remain undiagnosed at individual-bar level.
- V2 starts only on genuine first observable T+1 session. No late bootstrap.
- V1 invalid_bootstrap rows are excluded from all valid cohort reporting.
- Production `positions`, production stop prices, exits, dashboard projection, and alerts must not be changed by this shadow.

## Comparator fill contract

For any future paired comparison, both CURRENT and candidate must use the same executable daily-bar semantics:
1. If Open <= stop, fill at Open.
2. Else if Low <= stop, fill at stop.
3. Else if Close < EMA20, fill at Close.
4. Otherwise remain open.

This is a comparator-contract correction for a new research run only. Do not retroactively alter the frozen EXIT-CAND-003 validation results or tune parameters against the untouched holdout.

## Required acceptance tests

- v2 contract ID is distinct from v1.
- A position held for 45, 46, and 60 sessions does not exit solely because of elapsed time.
- Gap-through stop fills at Open and has priority over touch/trend exit.
- Intraday stop touch fills at operative stop.
- EMA20 exit fills at Close only when no stop triggers.
- Operative stop is monotonic and Chandelier arms only next session.
- Identical replay is idempotent; divergent evidence for the same ledger key fails closed.
- No v2 state registration occurs after the genuine first observable session.
- Production positions are read-only inputs and never mutated by shadow code.

## Rollout gate

1. Implement isolated v2 module and focused tests on this research branch.
2. Database version-key uniqueness is verified; do not write v2 rows until the module and tests exist and are reviewed.
3. Verify workflow trigger blast radius; keep workflows manual-only unless a narrowly isolated one-time run is needed.
4. Start v2 only as an observational cohort; compare production execution without using production outcomes as inputs to shadow decisions.
5. Accumulate forward-only evidence and report cohort counts, divergence classes, and data-quality exceptions.
6. Require a separate explicit productionization decision before any production exit change.

## Current limitation

The attempted source-code write for the isolated v2 module was blocked by the tool safety layer in this execution. This spec is committed as a non-executable research artifact; no claim is made that v2 code or live cohort has been implemented.
