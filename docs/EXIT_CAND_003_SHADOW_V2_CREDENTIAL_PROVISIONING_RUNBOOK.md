# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **CREDENTIAL BOUNDARY AND READ-ONLY DRY-RUN PASSED; FOCUSED TEST WORKFLOW AND RESEARCH REVIEW PENDING**

## Latest verified run (2026-10-16)

GitHub Actions [run 38833603075, attempt 2](https://github.com/azharmz/ussy-trendfoll/actions/runs/38833603075) completed successfully after changing `SHADOW_V2_DATABASE_URL` to the Session Pooler URI.

Verified in the job log:

- Authenticated as `ussy_shadow_v2_runner`; no elevated flags or role memberships.
- Effective table grants matched the least-privilege contract.
- Read/RLS counts: `positions=69`, `v2=0`, `v2_sessions=0`.
- Denied as expected: UPDATE/DELETE on `positions`, DELETE on Shadow rows, and UPDATE on Shadow sessions.
- Dry-run: `as_of=2026-10-14`, `R2_latest=2026-10-14`, `mode=DRY-RUN`.
- Cohort preview: `genuine_T1_today=2`, `late_bootstrap_rejected=15`, `no_post_entry_bar=0`, `missing_entry_date=0`.
- Runner reported that no production exit/stop/alert/dashboard functions were called and no database writes were attempted.

The first attempt failed because the direct database host resolved to IPv6 and the GitHub-hosted runner reported `Network is unreachable` on port 5432. The second attempt succeeded via Session Pooler. This historical failure is resolved.

## Decision

Keep one Supabase project and use the dedicated PostgreSQL login `ussy_shadow_v2_runner` with least-privilege grants and RLS policies. Do not use production `service_role` for the Shadow v2 runner.

- Production project: `rggtylvlrzzesrtumqzj`.
- The runner requires `SHADOW_V2_DATABASE_URL`; it has no fallback to privileged credentials.
- Keep the dashboard-generated Session Pooler URI in GitHub Actions secret `SHADOW_V2_DATABASE_URL`. Never share the URI or password in chat, commits, logs, or screenshots.

## Gate A — role and grants (passed in latest run)

The actual authenticated role was `ussy_shadow_v2_runner`; `rolsuper=false`, `rolcreatedb=false`, `rolcreaterole=false`, `rolbypassrls=false`, `NOINHERIT`, and no role memberships. Effective table grants matched the expected contract:

- `positions`: SELECT only.
- `exit_candidate003_shadow`: SELECT, INSERT, UPDATE.
- `exit_candidate003_shadow_sessions`: SELECT, INSERT.
- No DELETE/TRUNCATE on Shadow tables and no mutation on `positions`.

Credential-level negative checks passed; no data rows were changed.

## Gate B — RLS policies (provisioned; credential reads passed)

RLS is enabled on all three tables. Policies for the dedicated role:

- `positions`: SELECT only, `USING (true)`.
- `exit_candidate003_shadow`: SELECT, INSERT, UPDATE; write checks constrain `contract_version = 'exit-cand-003-shadow-v2'`.
- `exit_candidate003_shadow_sessions`: SELECT and INSERT only; insert check constrains the same contract version.

Do not use `BYPASSRLS` as a shortcut. Existing policies for other roles must not be changed as part of this work.

## Gate C — next steps

1. Run the focused Shadow v2 test workflow manually and record its result; no push triggers are configured.
2. Review the dry-run cohort and R2 READY freshness. The successful run used `2026-10-14`, so do not treat it as current without refreshing the market snapshot and rerunning with the exact latest READY date.
3. Keep `WRITE_MODE_ENABLED = False`. No first Shadow v2 write is authorized by this successful dry-run. Require separate explicit approval after tests and research review.

## Safety status

No Shadow v2 writes have been made or authorized. Production exit logic and `main.py` remain unchanged. The credential boundary and read-only dry-run passed; focused tests and review of the current prospective T+1 cohort remain pending.
