# EXIT-CAND-003 Shadow v2 — Proposed Same-Project Role SQL

Status: **REVIEW TEMPLATE ONLY — DO NOT EXECUTE WITHOUT EXPLICIT APPROVAL**

Project: `rggtylvlrzzesrtumqzj`

This template creates a custom login role in the existing production project. It contains no real password. A dedicated password must be generated and injected securely by the authorized operator; never commit or log it.

## 1. Role and exact table grants

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

No grants are made to any other table. Do not grant role memberships. Do not grant DELETE/TRUNCATE on Shadow tables, or any write privilege on `positions`.

## 2. RLS policies

Review these policy definitions with the existing policies before applying. The runner role must not inherit `anon`, `authenticated`, `service_role`, or `postgres`.

```sql
CREATE POLICY shadow_v2_runner_read_positions
  ON public.positions FOR SELECT TO ussy_shadow_v2_runner
  USING (true);

CREATE POLICY shadow_v2_runner_read_shadow
  ON public.exit_candidate003_shadow FOR SELECT TO ussy_shadow_v2_runner
  USING (contract_version = 'exit-cand-003-shadow-v2');

CREATE POLICY shadow_v2_runner_insert_shadow
  ON public.exit_candidate003_shadow FOR INSERT TO ussy_shadow_v2_runner
  WITH CHECK (contract_version = 'exit-cand-003-shadow-v2');

CREATE POLICY shadow_v2_runner_update_shadow
  ON public.exit_candidate003_shadow FOR UPDATE TO ussy_shadow_v2_runner
  USING (contract_version = 'exit-cand-003-shadow-v2')
  WITH CHECK (contract_version = 'exit-cand-003-shadow-v2');

CREATE POLICY shadow_v2_runner_read_shadow_sessions
  ON public.exit_candidate003_shadow_sessions FOR SELECT TO ussy_shadow_v2_runner
  USING (contract_version = 'exit-cand-003-shadow-v2');

CREATE POLICY shadow_v2_runner_insert_shadow_sessions
  ON public.exit_candidate003_shadow_sessions FOR INSERT TO ussy_shadow_v2_runner
  WITH CHECK (contract_version = 'exit-cand-003-shadow-v2');
```

These policies intentionally constrain Shadow writes to the v2 contract version. They do not grant SQL privileges by themselves; the role grants in section 1 are also required. Do not use `BYPASSRLS`.

## 3. Verification queries

Run after provisioning, using an administrative read-only audit session:

```sql
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolbypassrls
FROM pg_roles
WHERE rolname = 'ussy_shadow_v2_runner';

SELECT
  has_table_privilege('ussy_shadow_v2_runner','public.positions','SELECT') AS positions_select,
  has_table_privilege('ussy_shadow_v2_runner','public.positions','INSERT') AS positions_insert,
  has_table_privilege('ussy_shadow_v2_runner','public.positions','UPDATE') AS positions_update,
  has_table_privilege('ussy_shadow_v2_runner','public.positions','DELETE') AS positions_delete,
  has_table_privilege('ussy_shadow_v2_runner','public.positions','TRUNCATE') AS positions_truncate,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow','SELECT') AS shadow_select,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow','INSERT') AS shadow_insert,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow','UPDATE') AS shadow_update,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow','DELETE') AS shadow_delete,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow_sessions','INSERT') AS sessions_insert,
  has_table_privilege('ussy_shadow_v2_runner','public.exit_candidate003_shadow_sessions','UPDATE') AS sessions_update;
```

Expected: role is login-enabled but not superuser, cannot create databases/roles, and does not bypass RLS. `positions_select` true; all `positions_*` mutation flags false. Shadow SELECT/INSERT/UPDATE true and DELETE false. Sessions INSERT true and UPDATE false.

Also verify no privileged role memberships or table ownership. Test actual allowed/denied SQL operations using the role in a controlled session before using it in GitHub Actions. A catalog privilege query alone is not sufficient to prove RLS behavior.

## 4. Caveats

- The policy/grant DDL is production-impacting and has not been applied.
- Confirm direct database/pooler connectivity from GitHub-hosted runners before adding a secret.
- If the role cannot see the needed positions due to RLS, do not grant `BYPASSRLS`; revise and review policy scope.
- The Python guard remains defense-in-depth. The credential itself must enforce the boundary.
- Keep the Shadow v2 runner dry-run-only until these checks, automated tests, current R2 dry-run, and separate write approval are complete.
