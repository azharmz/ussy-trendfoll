# EXIT-CAND-003 Shadow v2 — Credential Boundary Design

Status: **HISTORICAL DESIGN PROPOSAL — credential topology superseded by the 2026-10-16 same-project audit; writes remain disabled**

> **Current source of truth:** `docs/EXIT_CAND_003_SHADOW_V2_SAME_PROJECT_ACCESS_AUDIT_2026-10-16.md` and `docs/EXIT_CAND_003_SHADOW_V2_CREDENTIAL_PROVISIONING_RUNBOOK.md`. The dedicated `ussy_shadow_v2_runner` PostgreSQL login is now provisioned and verified through GitHub Actions run `38887143847`. The runner uses `SHADOW_V2_DATABASE_URL` via the Session Pooler, and credential-level negative checks passed. `WRITE_MODE_ENABLED` remains `False`; no Shadow v2 writes have been authorized.

## Objective

Make it technically impossible for the Shadow v2 runner's persistence credentials to mutate production `public.positions`, even if the Python allow-list guard is bypassed or the runner contains a bug.

The original proposal below was written before the dedicated PostgreSQL login was provisioned. The current read-only runner does **not** use `SUPABASE_SERVICE_ROLE_KEY`; it connects through `SHADOW_V2_DATABASE_URL`. The verified role is constrained by database grants/RLS. The Python wrapper remains defense-in-depth, not the security boundary. This does not authorize writes.

## Original proposed architecture (historical; not the current credential topology)

The original proposal recommended two distinct data-plane credentials and a separate sink project:

1. **Production source (read-only):** a credential whose effective database grants allow SELECT on `public.positions` only (plus the minimum schema usage required). It must not own the table, be a member of a privileged role, or have INSERT/UPDATE/DELETE/TRUNCATE/DDL privileges. Verify effective privileges in the live database before use. Do not use `service_role` as the source credential.
2. **Shadow sink (isolated):** a separate Supabase project dedicated to research Shadow v2 tables. Its service-role credential may write only inside that separate project. It must not be the production project's URL/key. Create only the two Shadow v2 tables and required indexes/policies there; do not point it at the production project.
3. **Runner:** load source positions through the read-only source adapter; load R2 READY features; calculate the cohort; persist only to the isolated sink. Keep production exit/stop/alert/dashboard functions out of the runner. Do not use a shared generic client for both source and sink.
4. **GitHub Actions secrets:** use distinct names such as `PROD_READONLY_DATABASE_URL` (or another verified read-only connection mechanism), `SHADOW_SUPABASE_URL`, and `SHADOW_SUPABASE_SERVICE_ROLE_KEY`. Never alias the production service-role secret to the sink. Add secrets only after the corresponding credential/project exists and its grants are verified. Do not print secret values.
5. **Tests:** include negative tests proving the source adapter cannot issue mutations and that the sink target is configured independently from production. Add a deployment-time assertion that source and sink project references differ; fail closed if either is missing or the project refs match.

## Provisioning decision and safety constraints

A separate Shadow Supabase project is preferred for the sink because project-level service-role credentials cannot reach production tables. Provisioning a project may incur cost and requires explicit confirmation of the organization/cost; do not create one automatically.

A true read-only production source credential may require a database role/grants change or an already-existing restricted credential. Neither is established by the current audit. Do not create a production role, change grants/RLS, add GitHub secrets, or write to either database without a separately approved and verified plan.

If a restricted production read credential is not available, the runner must remain dry-run-only. A copied/exported positions snapshot can support offline research but must be clearly timestamped and cannot be represented as a live cohort.

## Verification gates

- [ ] Confirm a restricted production read credential exists; inspect effective grants and prove write/DDL attempts are denied in a safe test.
- [ ] Provision/identify a separate Shadow project only after cost/org confirmation.
- [ ] Verify the sink project reference differs from production and the sink schema contains no production tables.
- [ ] Refactor runner to distinct source and sink adapters; remove production service-role access from the Shadow v2 workflow.
- [ ] Add and pass isolation tests and the existing focused tests.
- [ ] Run the manual-only GitHub Actions tests; do not add push triggers.
- [ ] Refresh latest R2 READY, run a dry-run, and verify the genuine T+1 cohort from current data.
- [ ] Obtain explicit approval for any first Shadow v2 write. Production writes remain prohibited.

## Current state (2026-10-16)

The same-project credential design was implemented and verified as documented in `docs/EXIT_CAND_003_SHADOW_V2_SAME_PROJECT_ACCESS_AUDIT_2026-10-16.md` and the credential runbook. GitHub Actions run `38887143847` verified the dedicated login, effective grants, expected denied mutations, current R2 date `2026-10-15`, and a read-only cohort preview. Focused tests passed in run `38884771979` (11 Shadow v2 tests + 8 database guard tests). The runner's `--write` path remains disabled; no Shadow v2 rows have been written or authorized. Any future write requires a separate explicit governance decision and review of the write path.
