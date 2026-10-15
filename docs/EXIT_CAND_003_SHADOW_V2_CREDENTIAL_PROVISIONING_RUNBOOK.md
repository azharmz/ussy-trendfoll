# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **PREPARATION ONLY — NOT EXECUTED**

This runbook reflects the read-only audit in [SAME_PROJECT_ACCESS_AUDIT](EXIT_CAND_003_SHADOW_V2_SAME_PROJECT_ACCESS_AUDIT_2026-10-16.md). No production DDL/DML, secrets, or Shadow writes are authorized by this document.

## Decision

**Preferred: keep one Supabase project and create a dedicated PostgreSQL login with least-privilege grants and RLS policies.** A separate project is not technically required if the database-enforced access boundary is verified.

- Production project: `rggtylvlrzzesrtumqzj`
- Never use production `service_role` for the Shadow v2 runner.
- Connect with a dedicated PostgreSQL connection/pooler URL, not the Supabase service-role API key.
- Keep `WRITE_MODE_ENABLED = False` until provisioning, negative tests, current dry-run, and separate approval pass.

## Gate A — role and grants (proposal only)

Use a unique role name and generate the password securely outside source control. This SQL is a review template, not an approved or executed migration:

```sql
CREATE ROLE ussy_shadow_v2_runner
  WITH LOGIN PASSWORD '<GENERATE_AND_INJECT_SECURELY>'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

GRANT CONNECT ON DATABASE postgres TO ussy_shadow_v2_runner;
GRANT USAGE ON SCHEMA public TO ussy_shadow_v2_runner;

GRANT SELECT ON TABLE public.positions TO ussy_shadow_v2_runner;

GRANT SELECT, INSERT, UPDATE
  ON TABLE public.exit_candidate003_shadow TO ussy_shadow_v2_runner;
GRANT SELECT, INSERT
  ON TABLE public.exit_candidate003_shadow_sessions TO ussy_shadow_v2_runner;
```

Do not grant role membership in `anon`, `authenticated`, `service_role`, `postgres`, or any elevated role. Do not grant DELETE/TRUNCATE on Shadow tables, or any mutation on `positions`. Do not grant table ownership, sequence ownership, CREATE privileges, or `BYPASSRLS`.

## Gate B — explicit RLS policies (proposal only)

RLS is enabled on all three tables. Existing policies only cover SELECT for `anon` and `authenticated`, so the dedicated role needs explicit policies to read positions and perform only the approved Shadow operations. Review exact policy definitions before applying them. Minimum intent:

- `positions`: SELECT only, `USING (true)`.
- `exit_candidate003_shadow`: SELECT, INSERT, UPDATE; INSERT/UPDATE checks must constrain `contract_version = 'exit-cand-003-shadow-v2'`.
- `exit_candidate003_shadow_sessions`: SELECT and INSERT only; INSERT check must constrain `contract_version = 'exit-cand-003-shadow-v2'`.

Do not use `BYPASSRLS` as a shortcut. Keep existing policies unchanged unless a separately reviewed security fix is approved.

## Gate C — verify before connecting the runner

1. Obtain explicit approval for the production role/policy DDL and have an authorized operator apply the reviewed migration.
2. Verify `rolsuper=false`, `rolbypassrls=false`, no elevated role memberships, and no ownership.
3. Verify effective privileges: SELECT on `positions`; no INSERT/UPDATE/DELETE/TRUNCATE on `positions`; only SELECT/INSERT/UPDATE on the main Shadow table; only SELECT/INSERT on the sessions table; no access to unrelated tables.
4. Test in a controlled session that production mutations, Shadow DELETE/TRUNCATE, and writes to unrelated tables are denied. Verify permitted Shadow operations work and RLS returns the required positions.
5. Add the direct database/pooler URL as GitHub Actions secret `SHADOW_V2_DATABASE_URL`. Never log it. Do not use `SUPABASE_SERVICE_ROLE_KEY` in the Shadow v2 workflow.
6. Refactor runner to use this single constrained database connection and retain the Python guard as defense-in-depth.
7. Run tests manually; no push triggers.
8. Refresh R2 READY and record the exact current as-of date and genuine prospective T+1 cohort in dry-run.
9. Obtain separate explicit approval before the first Shadow v2 write.

## Fallback

Use a separate Supabase project only if a safe same-project role/policy boundary cannot be implemented or verified. Creating another project may incur cost and is not the default.

Until all gates pass, no v2 writes. This document does not itself authorize production DDL or secret changes.
