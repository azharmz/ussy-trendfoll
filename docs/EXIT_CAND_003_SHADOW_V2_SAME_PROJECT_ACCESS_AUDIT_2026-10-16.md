# EXIT-CAND-003 Shadow v2 — Same-Project Access Audit

Date: 2026-10-16
Project: `rggtylvlrzzesrtumqzj`
Status: **READ-ONLY AUDIT COMPLETE — NO DDL/DML EXECUTED**

## Finding

A separate Supabase project is not technically mandatory. The same project can support a dedicated PostgreSQL login whose table grants and RLS policies constrain it to the exact Shadow v2 data path, provided the runner connects directly through the database/pooler using that login rather than the production service-role API key.

This design still requires a reviewed production DDL change to create the role, grant minimum privileges, and add narrowly scoped RLS policies. None were applied during this audit.

## Read-only observations

- The database is `postgres`; audit queries executed as `postgres`.
- `public.positions`, `public.exit_candidate003_shadow`, and `public.exit_candidate003_shadow_sessions` all have RLS enabled and `FORCE ROW LEVEL SECURITY` disabled.
- Current policies on all three tables are SELECT-only policies for `anon` and `authenticated`; there are no write policies for those roles in the inspected results.
- Table ACLs show `anon` and `authenticated` have table-level privileges beyond SELECT on `positions` and `exit_candidate003_shadow`. RLS currently blocks their writes because no matching write policy was found, but the ACLs are broader than the policy names suggest. This is a separate hardening concern and was not changed here.
- `service_role` has SELECT/INSERT/UPDATE/DELETE/TRUNCATE privileges on `positions` and has `BYPASSRLS`; it is unsuitable as the Shadow runner credential.
- The existing `positions` table uses an identity column for `id`; the Shadow tables also use identity columns.

## Proposed least-privilege role

Use a dedicated login role (example name: `ussy_shadow_v2_runner`) with:
- database CONNECT and schema USAGE;
- SELECT on `public.positions`;
- SELECT/INSERT/UPDATE on `public.exit_candidate003_shadow`;
- SELECT/INSERT on `public.exit_candidate003_shadow_sessions`;
- no privileges on other tables, no sequence/table ownership, no elevated-role membership, no `BYPASSRLS`, no CREATE/ALTER/DROP, no TRUNCATE/DELETE on the Shadow tables, and no INSERT/UPDATE/DELETE on `positions`.

Add explicit RLS policies for this dedicated role that permit SELECT on `positions`, SELECT/INSERT/UPDATE on the Shadow table, and SELECT/INSERT on the session table. The role must not inherit `anon`, `authenticated`, `service_role`, or `postgres`. Use a direct PostgreSQL connection/pooler; do not send this password as a Supabase API key or put it in source control.

## Required proof before runner use

1. Create the role and grants only through a separately reviewed, approved production change.
2. Verify `rolsuper=false`, `rolbypassrls=false`, no privileged memberships, and no ownership.
3. Verify effective privileges are exactly as above using `has_table_privilege`.
4. In a controlled test session, prove writes to `positions`, DELETE/TRUNCATE/DDL, and writes to unapproved tables are denied; prove permitted Shadow operations work.
5. Verify RLS returns the required production rows to the custom role without widening other roles' policies.
6. Add the connection string as a GitHub Actions secret, never log it.
7. Refactor the runner into a read-only source connection and constrained Shadow writer; retain the Python guard as defense-in-depth.
8. Run tests manually, refresh latest R2 READY, and complete a current dry-run.
9. Require separate explicit approval before the first Shadow v2 write.

## Safety statement

This audit performed SELECT-only catalog queries. No roles, grants, policies, secrets, production rows, or Shadow rows were changed. `WRITE_MODE_ENABLED` must remain false until the full verification gate is passed.
