# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **FOCUSED TESTS, CREDENTIAL BOUNDARY, AND CURRENT-DATE READ-ONLY DRY-RUN PASSED; OPERATIONAL RESEARCH REVIEW STILL REQUIRED**

## Latest verified run (2026-10-16)

GitHub Actions [run 38887143847](https://github.com/azharmz/ussy-trendfoll/actions/runs/38887143847) completed successfully for as_of_date=2026-10-15.

Verified in the job log:

- Authenticated as ussy_shadow_v2_runner; no elevated flags or role memberships.
- Effective table grants matched the least-privilege contract.
- Read/RLS counts: positions=80, v2=0, v2_sessions=0.
- Denied as expected: UPDATE/DELETE on positions, DELETE on Shadow rows, and UPDATE on Shadow sessions.
- Dry-run: as_of=2026-10-15, R2_latest=2026-10-15, mode=DRY-RUN.
- Cohort preview: genuine_T1_today=1, late_bootstrap_rejected=12, no_post_entry_bar=0, missing_entry_date=0.
- Runner reported that no production exit/stop/alert/dashboard functions were called and no database writes were attempted.

The first attempt on 2026-10-14 failed because the direct database host resolved to IPv6 and the GitHub-hosted runner reported Network is unreachable on port 5432. The Session Pooler URI resolved this connectivity issue.

## Focused tests

GitHub Actions [run 38884771979](https://github.com/azharmz/ussy-trendfoll/actions/runs/38884771979) completed successfully on 2026-10-16.

- Python compilation passed for the isolated runner, module, guard, and database boundary probe.
- Shadow v2 unit tests: **11 passed**.
- Database guard allow-list tests: **8 passed**.
- Checkout log confirms tested research commit:  a96b8590e4725aafad0d198b259a6742febae51e.

## Decision

Keep one Supabase project and use the dedicated PostgreSQL login ussy_shadow_v2_runner with least-privilege grants and RLS policies. Do not use production service_role for the Shadow v2 runner.

- Production project: rggtylvlrzzesrtumqzj.
- The runner requires SHADOW_V2_DATABASE_URL; it has no fallback to privileged credentials.
- Keep the dashboard-generated Session Pooler URI in GitHub Actions secret SHADOW_V2_DATABASE_URL. Never share the URI or password in chat, commits, logs, or screenshots.

## Gate A — role and grants (passed in latest run)

The actual authenticated role was ussy_shadow_v2_runner; rolsuper=false, rolcreatedb=false, rolcreaterole=false, rolbypassrls=false, NOINHERIT, and no role memberships. Effective table grants matched the expected contract:

- positions: SELECT only.
- exit_candidate003_shadow: SELECT, INSERT, UPDATE.
- exit_candidate003_shadow_sessions: SELECT, INSERT.
- No DELETE/TRUNCATE on Shadow tables and no mutation on positions.

Credential-level negative checks passed; no data rows were changed.

## Gate B — RLS policies (provisioned; credential reads passed)

RLS is enabled on all three tables. Policies for the dedicated role:

- positions: SELECT only, USING (true).
- exit_candidate003_shadow: SELECT, INSERT, UPDATE; write checks constrain contract_version = 'exit-cand-003-shadow-v2'.
- exit_candidate003_shadow_sessions: SELECT and INSERT only; insert check constrains the same contract version.

Do not use BYPASSRLS as a shortcut. Existing policies for other roles must not be changed as part of this work.

## Gate C — next steps

1. Focused tests are complete and green; no push triggers were added.
2. Latest R2 READY date is verified as 2026-10-15 by the successful daily pipeline run and matching Shadow v2 dry-run.
3. Review the prospective cohort before any write authorization. The current preview contains one genuine T+1 candidate, 12 late-bootstrap candidates rejected, and no missing post-entry bars or entry dates.
4. Keep WRITE_MODE_ENABLED = False. No first Shadow v2 write is authorized by these successful checks. Require separate explicit approval after the operational research review and governance gate.

## Safety status

No Shadow v2 writes have been made or authorized. Production exit logic and main.py remain unchanged. Focused tests, credential boundary checks, and a dry-run against the latest verified R2 date passed; prospective cohort review and any later write authorization remain pending.
