# EXIT-CAND-003 Shadow v2 — Credential Boundary Design

Status: **DESIGN ONLY — no credentials added, no database changes, no writes approved**

## Objective

Make it technically impossible for the Shadow v2 runner's persistence credentials to mutate production `public.positions`, even if the Python allow-list guard is bypassed or the runner contains a bug.

The current runner uses `SUPABASE_SERVICE_ROLE_KEY`. That credential is privileged and can bypass RLS; a Python wrapper is not a security boundary. Do not enable `--write` while that remains true.

## Required architecture

Use two distinct data-plane credentials and keep the source and sink clients separate:

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

## Current state

As of 2026-10-15, the runner's `--write` path is disabled. `shadow_v2_db_guard.py` is useful defense-in-depth only; it does not satisfy credential isolation. No production data/schema/grants/secrets were changed and no Shadow v2 rows were written as part of this design.
