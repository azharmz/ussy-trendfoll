# EXIT-CAND-003 Shadow v2 Gate — 2026-10-15

Status: **BLOCKED; READ-ONLY MODE ONLY; NO V2 WRITE APPROVED**

## Live read-only inventory

Supabase project `rggtylvlrzzesrtumqzj` was inspected without DDL or DML.

- `public.positions`: 69 rows.
- `public.exit_candidate003_shadow`: 65 rows, 0 rows for `exit-cand-003-shadow-v2`.
- `public.exit_candidate003_shadow_sessions`: 243 rows, 0 rows for `exit-cand-003-shadow-v2`.
- Current query found 18 active positions with no exit date, not the 21 counted in the 2026-10-14 dry-run. Do not reuse the stale cohort count.
- CVX (position id 69) has null `realistic_entry_price`, so it fails the runner's current valid-entry check.
- These counts do not establish the genuine T+1 candidate; the latest validated R2 READY data and exact as-of date are required.

## Security finding

The runner's original client uses `SUPABASE_SERVICE_ROLE_KEY`. Live grants metadata shows service_role can INSERT, UPDATE, and DELETE `public.positions`. RLS is enabled but not forced; service-role access bypasses RLS. Code-level discipline alone is not database-enforced isolation.

## Changes implemented on this research branch

- Added `shadow_v2_db_guard.py`, an explicit table/mutation allow-list. Reads are limited to `positions` and the two shadow tables. Writes are limited to INSERT/UPDATE on `exit_candidate003_shadow` and INSERT on `exit_candidate003_shadow_sessions`. Unknown tables and other mutations fail closed.
- Wrapped the runner's Supabase client before it is passed to the Shadow v2 module.
- Added `tests/test_shadow_v2_db_guard.py` covering allowed reads/writes, blocked production writes, unknown-table access, upsert/delete rejection, and absence of raw-client methods.
- Updated the focused test workflow to compile the guard and run both v2 test suites.
- Disabled `--write` in the runner and removed write mode/acknowledgement from the manual workflow. The workflow now exposes dry-run only.

**Important limitation:** this guard is a code-path defense, not credential-level or database-enforced isolation. The underlying service-role key remains privileged if used outside the wrapper. No claim of hard isolation is made. The guard tests have been committed but have not yet been executed in GitHub Actions in this work session.

## Remaining blockers

1. A genuine restricted credential or architecture that prevents arbitrary production writes is still required before any live v2 write. Do not rely on the wrapper alone for credential-level security.
2. Run the focused test workflow and verify all guard tests pass.
3. Re-run a dry-run against the latest R2 READY date and record the exact genuine T+1 candidate. The previous 2026-10-13 snapshot is stale; do not reuse its candidate count.
4. Separately approve the first write only after the security boundary and prospective cohort both pass.

No production rows, schemas, grants, RLS policies, secrets, or production workflow triggers were changed. No v2 rows were seeded.
