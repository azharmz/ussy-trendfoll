# EXIT-CAND-003 Shadow v2 — No Time-Based Exit Contract

Status: **IMPLEMENTATION TESTED / READY FOR DRY-RUN REVIEW / NOT LIVE / NOT DEPLOYED**

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
- Live database constraints were checked read-only: `exit_candidate003_shadow` has UNIQUE `(position_id, contract_version)`; `exit_candidate003_shadow_sessions` has UNIQUE `(position_id, session_date, contract_version)`. These support version-isolated v2 rows without a schema migration.
- V2 starts only on genuine first observable T+1 session. Late bootstrap is rejected.
- Only production positions whose status is `active` and whose `exit_date` is null are eligible for registration.
- V1 `invalid_bootstrap` rows are excluded from valid cohort reporting.
- Production `positions`, production stop prices, exits, dashboard projection, and alerts must not be changed by this shadow.

## Comparator fill contract

For any future paired comparison, both CURRENT and candidate must use the same executable daily-bar semantics:
1. If Open <= stop, fill at Open.
2. Else if Low <= stop, fill at stop.
3. Else if Close < EMA20, fill at Close.
4. Otherwise remain open.

This is a comparator-contract correction for a new research run only. Do not retroactively alter the frozen EXIT-CAND-003 validation results or tune parameters against the untouched holdout.

## Implementation and tests

- Isolated module: `exit_candidate003_shadow_v2.py`.
- Standalone runner: `run_exit_candidate003_shadow_v2.py`. It is not imported by production `main.py`.
- Runner requires an explicit `--as-of-date`, requires that date to match the latest R2 feature date, and defaults to dry-run.
- Persistence requires both `--write` and environment acknowledgement `USSY_CAND003_SHADOW_V2_WRITE_ACK=I_UNDERSTAND_SHADOW_ONLY`.
- Manual-only runner workflow: `.github/workflows/exit-candidate003-shadow-v2-runner.yml`; no push or schedule trigger.
- Focused tests: `tests/test_exit_candidate003_shadow_v2.py`. The successful run [38554050377](https://github.com/azharmz/ussy-trendfoll/actions/runs/38554050377) compiled the module and runner and passed all 11 tests, including no time cap, stop-fill priority, late-bootstrap rejection, closed-position exclusion, replay invariants, and production-position write isolation.
- All 40 workflow trigger declarations in this branch were inspected. Push triggers are branch/path restricted; unscoped push workflows have unrelated path filters. The one-time scoped trigger for tests was removed immediately after the run started; test workflow is manual-only again.

## Rollout gate

1. Run the standalone runner in **dry-run only** against the current R2 READY date and review output/cohort counts.
2. Confirm the expected active position cohort and exact latest R2 date.
3. Review service-role access and table constraints before any first write. Do not write live v2 rows until that review is explicitly accepted.
4. Accumulate forward-only evidence and report cohort counts, divergence classes, and data-quality exceptions.
5. Require a separate explicit productionization decision before any production exit change.

## Current operational status (2026-10-14)

- **PASS:** focused implementation tests and workflow-trigger topology audit.
- **NEXT:** dry-run review only; no live observation yet.
- **NOT DONE:** first v2 database write, live permissions exercise, matched-fill paired research comparison.
- Four v1 divergence cases remain undiagnosed at individual-bar level because the row-level query was blocked by the tool safety layer.
- No v2 rows were written; no Supabase changes; no production file, position, exit, dashboard, or alert state was changed.
