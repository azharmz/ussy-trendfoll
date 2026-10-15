# EXIT-CAND-003 Shadow v2 Gate — 2026-10-15

Status: BLOCKED; read-only audit only. No v2 write approved.

## Live read-only inventory

Supabase project `rggtylvlrzzesrtumqzj` was inspected without DDL or DML.

- `public.positions`: 69 rows.
- `public.exit_candidate003_shadow`: 65 rows, 0 rows for `exit-cand-003-shadow-v2`.
- `public.exit_candidate003_shadow_sessions`: 243 rows, 0 rows for `exit-cand-003-shadow-v2`.
- Current query found 18 active positions with no exit date, not the 21 counted in the 2026-10-14 dry-run. Do not reuse the stale cohort count.
- CVX (position id 69) has null `realistic_entry_price`, so it fails the runner's current valid-entry check.
- These counts do not establish the genuine T+1 candidate; the latest validated R2 READY data and exact as-of date are required.

## Security gate

The runner calls `database.get_client()`, which uses `SUPABASE_SERVICE_ROLE_KEY`. Live grants metadata shows service_role can INSERT, UPDATE, and DELETE `public.positions`. RLS is enabled but not forced; service-role access bypasses RLS. Therefore, the current code's choice to write only shadow tables is not a database-enforced permission boundary.

## Required before first write

1. Keep write mode disabled; do not seed v2 rows.
2. Design an allow-listed persistence boundary so the runner cannot directly mutate arbitrary tables. A SECURITY DEFINER RPC may constrain the intended code path but does not make a broad service-role credential least-privileged. Credential-level isolation requires a dedicated restricted database role/credential or an architecture that prevents arbitrary writes.
3. Test the boundary in an isolated project/branch, including rejection of production table mutations.
4. Re-run a dry-run against the latest R2 READY date and record the exact genuine T+1 candidate. Stop if the snapshot is stale.
5. Separately approve the first write only after both gates pass.

No production rows, schemas, grants, RLS policies, workflow triggers, or secrets were changed during this audit.