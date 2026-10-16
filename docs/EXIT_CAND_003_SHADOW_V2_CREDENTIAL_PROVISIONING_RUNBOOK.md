# EXIT-CAND-003 Shadow v2 — Credential Provisioning Runbook

Status: **FOCUSED TESTS, CREDENTIAL BOUNDARY, AND CURRENT-DATE READ-ONLY DRY-RUN PASSED; PROSPECTIVE COHORT IDENTIFIED; NO WRITE AUTHORIZED**

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
- Checkout log confirms tested research commit: a96b8590e4725aafad0d198b259a6742febae51e.

## Prospective T+1 cohort review (read-only)

A read-only query of active production positions missing a v2 shadow, reconciled with the runner's 2026-10-15 dry-run counts, identifies the sole genuine T+1 candidate:

- Position ID 69, symbol CVX.
- Production entry date: 2026-10-14.
- Stored realistic entry price: 222.82000732421875.
- Stored ATR14 at entry: 4.360460976857928.
- The runner found the first post-entry R2 bar on 2026-10-15, matching the requested as-of date; this is the one genuine_T1_today candidate.
- The other 12 valid missing-shadow positions are late-bootstrap candidates and were rejected. No missing post-entry bars or missing entry dates were reported.

This confirms the cohort identity and T+1 date, but is not authorization to write. Before any future write, separately verify the frozen CAND-003 input/stop semantics and all write-path invariants. No shadow rows were created by this review.

## Exact T+1 market-input diagnostic (2026-10-16)

GitHub Actions [run 38887790848](https://github.com/azharmz/ussy-trendfoll/actions/runs/38887790848) completed successfully with the diagnostic-only runner on the research branch. The decoded job log confirms:

- Candidate: position ID 69, CVX; bar date: 2026-10-15.
- OHLC: open 222.820007, high 223.460007, low 218.050003, close 219.320007.
- Runner EMA20: 211.159545.
- Entry: 222.820007; ATR14 at entry: 4.360461; frozen initial stop: 214.099085.
- `low_at_or_below_initial_stop=False`; `close_below_ema20=False`.
- Interpretation limited to the logged checks: neither the initial stop nor the EMA20 close condition would trigger an exit on 2026-10-15. This does not establish whether the Chandelier ratchet would advance the operative stop, because this diagnostic does not emit HH22/ATR22/Chandelier values.
- Role/grant boundary checks passed again; the run reports dry-run only and no database writes attempted.

This is evidence for the first observed session only, not permission to register or update a Shadow row. Before any writer review, add/inspect the frozen Chandelier inputs and verify the session-evidence/persistence invariants; keep `WRITE_MODE_ENABLED = False`.

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
3. Prospective cohort identified as CVX position 69 on its genuine T+1 session; no database writes occurred.
4. Keep WRITE_MODE_ENABLED = False. No first Shadow v2 write is authorized by these successful checks. Require separate explicit approval after the operational research review and governance gate.

## Safety status

No Shadow v2 writes have been made or authorized. Production exit logic and main.py remain unchanged. Focused tests, credential boundary checks, latest-date dry-run, and read-only prospective cohort identification passed. A separate explicit governance decision is still required before any write.
