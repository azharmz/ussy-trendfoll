# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **ROLE/POLICIES APPLIED; CREDENTIAL-LEVEL TEST AND DRY-RUN PENDING**

This runbook reflects the read-only audit and subsequent operator-applied SQL in [SAME_PROJECT_ACCESS_AUDIT](EXIT_CAND_003_SHADOW_V2_SAME_PROJECT_ACCESS_AUDIT_2026-10-16.md). The role and RLS policies are present in production. No Shadow v2 writes have been made or authorized.

## Decision

**Keep one Supabase project and use a dedicated PostgreSQL login with least-privilege grants and RLS policies.** A separate project is not required if the database-enforced access boundary is verified.

- Production project: `rggtylvlrzzesrtumqzj`
- Never use production `service_role` for the Shadow v2 runner.
- Connect with `SHADOW_V2_DATABASE_URL`, a dedicated PostgreSQL connection/pooler URL, not the Supabase service-role API key.
- Runner is now configured to fail closed if `SHADOW_V2_DATABASE_URL` is missing; it has no fallback to privileged credentials.
- Keep `WRITE_MODE_ENABLED = False` until provisioning, credential-level negative tests, current dry-run, and separate approval pass.

## Gate A — role and grants (applied; verify live)

The database role `ussy_shadow_v2_runner` has been observed with LOGIN enabled, `rolsuper=false`, `rolcreatedb=false`, `rolcreaterole=false`, `rolbypassrls=false`, `NOINHERIT`, and no role memberships.

Expected grants:

- `positions`: SELECT only.
- `exit_candidate003_shadow`: SELECT, INSERT, UPDATE.
- `exit_candidate003_shadow_sessions`: SELECT, INSERT.

No DELETE/TRUNCATE on Shadow tables, and no mutation on `positions`.

## Gate B — RLS policies (applied; verify live)

RLS is enabled on all three tables. The dedicated role has explicit policies:

- `positions`: SELECT only, `USING (true)`.
- `exit_candidate003_shadow`: SELECT, INSERT, UPDATE; write checks constrain `contract_version = 'exit-cand-003-shadow-v2'`.
- `exit_candidate003_shadow_sessions`: SELECT and INSERT only; insert check constrains the same contract version.

Do not use `BYPASSRLS` as a shortcut. Existing policies for other roles were not changed by this work.

## Gate C — credential-level verification and dry-run (pending)

1. Set a strong password for `ussy_shadow_v2_runner` through an authorized SQL Editor session; never store it in source control or chat.
2. Add the PostgreSQL/pooler connection string as GitHub Actions repository secret `SHADOW_V2_DATABASE_URL`. The value must authenticate as `ussy_shadow_v2_runner`, not `postgres` or `service_role`. Prefer Session Pooler if the GitHub runner cannot reach the direct IPv6 endpoint.
3. The manual-only runner workflow first executes `scripts/check_shadow_v2_db_boundary.py`. It verifies the actual authenticated role, flags, memberships, effective grants, SELECT/RLS access, and that UPDATE/DELETE attempts against production and forbidden Shadow tables are denied. Those attempts are expected to fail before any row changes; no successful write is attempted.
4. The dry-run then reads the latest Shadow v2 rows and production positions using that same constrained PostgreSQL connection.
5. Run the focused test workflow manually; no push triggers are configured.
6. Refresh R2 READY and use the exact current as-of date and genuine prospective T+1 cohort.
7. Obtain separate explicit approval before any first Shadow v2 write.

## Fallback

Use a separate Supabase project only if a safe same-project role/policy boundary cannot be implemented or verified. Creating another project may incur cost and is not the default.

Until all gates pass, no v2 writes. Production exit logic and `main.py` remain unchanged.
