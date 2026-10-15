# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **PREPARATION ONLY — NOT EXECUTED**

This runbook prepares the next security step. It does not authorize production DDL, grants, secret changes, project creation, or Shadow writes.

## Target

- Production source project: `rggtylvlrzzesrtumqzj`
- Shadow sink: a different Supabase project, to be provisioned only after the owner selects the organization and confirms the quoted cost.
- Production `service_role` must not be used by the Shadow v2 workflow.

## Gate A — production read-only login

Preferred approach: a dedicated PostgreSQL login used through the Supabase database connection/pooler, not a service-role API key. Provisioning must be reviewed and executed separately in the production SQL editor by an authorized operator.

Illustrative SQL template (do not run as-is; choose a unique role name and generate/store the password securely outside source control):

```sql
CREATE ROLE ussy_shadow_v2_reader
  WITH LOGIN PASSWORD '<GENERATE_AND_INJECT_SECURELY>'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

GRANT CONNECT ON DATABASE postgres TO ussy_shadow_v2_reader;
GRANT USAGE ON SCHEMA public TO ussy_shadow_v2_reader;
GRANT SELECT ON TABLE public.positions TO ussy_shadow_v2_reader;
```

Important:
- This is a proposal, not an executed migration. Do not commit a real password.
- Do not grant membership in `service_role`, `postgres`, or any elevated role.
- RLS is enabled on some tables in the project. Confirm how it applies to `positions`; if the role cannot see the intended rows, stop and review the RLS design rather than broadening privileges casually.
- If an RLS exception or `BYPASSRLS` is proposed, require explicit review. The invariant is still that the role has SELECT on `positions` and no write, DDL, role-management, or ownership privileges.
- Test effective privileges and denied mutations in a controlled transaction/session. Verify `has_table_privilege('ussy_shadow_v2_reader','public.positions','SELECT')` is true and INSERT/UPDATE/DELETE/TRUNCATE are false. Also verify no privileged role memberships and no table ownership.
- Store the connection URL only as a GitHub Actions secret after verifying that the selected connection mode is reachable from GitHub-hosted runners. Do not print it in logs.

## Gate B — isolated Shadow sink

Create a separate Supabase project after confirming organization and cost. Use a distinct URL/project ref and service-role secret for that project only. Create the two Shadow v2 tables there from a reviewed schema contract; do not copy production `positions` into the sink or grant the sink credentials access to the production project.

Required workflow secrets (names are proposals):
- `PROD_READONLY_DATABASE_URL`
- `SHADOW_SUPABASE_URL`
- `SHADOW_SUPABASE_SERVICE_ROLE_KEY`
- Existing R2 secrets needed to read READY data

Do not configure `SUPABASE_SERVICE_ROLE_KEY` in the Shadow v2 workflow. The runner must compare project refs and fail before database access if source and sink are not distinct.

## Gate C — verification

1. Provision and verify the restricted production login; do not run the Shadow runner yet.
2. Provision the isolated sink and verify the project ref is different from production.
3. Add secrets only after both endpoints have been verified.
4. Refactor the runner to use separate source and sink adapters. Production source client must expose only the required SELECT; sink client must only point to the isolated project.
5. Add tests for distinct project refs, missing secret fail-closed behavior, read-only source behavior, and sink-only writes.
6. Run the manual-only test workflow. No push triggers.
7. Refresh R2 READY and record the exact as-of date and prospective T+1 cohort in a dry-run.
8. Obtain separate approval before the first Shadow sink write.

Until all gates pass, keep `WRITE_MODE_ENABLED = False` and do not seed v2 rows.
