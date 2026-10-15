# EXIT-CAND-003 Shadow v2 — Integration & Operational Readiness Audit

Date: 2026-10-14
Branch: `research/exit-cand-003-shadow-v2-no-time-cap`
Status: **TESTS PASS; DRY-RUN PASS; NOT LIVE; NOT DEPLOYED**

## Verified implementation

- Focused workflow [run 38554618008](https://github.com/azharmz/ussy-trendfoll/actions/runs/38554618008) passed after the runner adapter fix. It compiled `exit_candidate003_shadow_v2.py` and `run_exit_candidate003_shadow_v2.py`; all **11 focused tests passed**.
- Tests now cover: no time cap; stop/trend execution ordering; idempotent and divergent ledger replay; late-bootstrap rejection; closed-position exclusion; and a full session advancement proving no mutation calls to production `positions`.
- Standalone runner: `run_exit_candidate003_shadow_v2.py`. It is not imported by `main.py`; it requires an explicit `--as-of-date`, validates the exact latest R2 READY date, derives EMA20 directly from validated READY `close_raw` using production's `ewm(span=20, adjust=False)` formula, defaults to dry-run, and requires both `--write` and `USSY_CAND003_SHADOW_V2_WRITE_ACK=I_UNDERSTAND_SHADOW_ONLY` for persistence.
- Actual read-only dry-run [run 38555455926](https://github.com/azharmz/ussy-trendfoll/actions/runs/38555455926) passed for R2 READY date **2026-10-13**: `active_v2=0`, `active_positions_without_v2=19`; output confirmed no database writes attempted. This is a scope preview, not a live observation.
- Manual-only runner workflow: `.github/workflows/exit-candidate003-shadow-v2-runner.yml`. It has no push or schedule trigger, defaults to dry-run, requires exact write acknowledgement for write mode, and has isolated concurrency group `exit-cand-003-shadow-v2-research`.
- Test workflow `.github/workflows/exit-candidate003-shadow-v2-tests.yml` has been restored to `workflow_dispatch` only after the isolated run. The one-time temporary push trigger was branch- and path-scoped, then removed immediately after the run started.
- The only new workflow run from that trigger was the focused v2 test run 38554050377. No live runner workflow was invoked.

## Complete workflow-trigger topology audit

The branch's `.github/workflows` directory contains **40 workflow files**. All 40 trigger declarations were inspected.

- Workflows with push triggers are restricted by branch and/or explicit paths. Branch-scoped workflows targeting other research/diagnostic branches cannot run from this v2 branch.
- The few unscoped `push` triggers are path-filtered to unrelated Trend Filter, signal-path diagnostic, or NEAR_TRIGGER files. None of the changed v2 module, runner, v2 tests, v2 workflow, or v2 documentation paths match those filters.
- `.github/workflows/daily.yml` has a schedule and manual dispatch, but scheduled events run on the default branch; the v2 research branch does not change the default-branch workflow.
- Test trigger was restored to manual-only after the successful focused test. Runner trigger was also restored to manual-only after the successful dry-run. No non-v2 workflow was triggered by these changes.
- Two earlier temporary runner attempts failed before any write (first due to importing the wrong adapter, second due to a malformed temporary date-output newline). A third dry-run passed. One earlier adapter-based run and a queued duplicate may remain in GitHub Actions until the runner timeout/concurrency queue resolves; they are read-only and do not invoke shadow persistence.
- Result: **PASS for trigger blast-radius assessment of this branch's v2 changes**. This is a trigger topology review, not a review of all workflow job side effects or repository secrets.

## Data and production isolation

- Production `main.py` continues to import and invoke v1 only; no v2 imports or calls were added.
- The standalone runner calls only the v2 shadow module after explicit write opt-in. It does not call production exit/stop/alert/dashboard mutators.
- V2 uses the distinct `contract_version` in the existing shadow and session-ledger tables. Composite uniqueness constraints were previously verified read-only; no schema migration was made.
- **No v2 rows were seeded; no Supabase writes were performed; no production position, stop, exit, dashboard, or alert state was changed.**
- Write-mode runner and live database permissions have not been exercised. This is intentional until operational review is complete.

## Dry-run result (2026-10-14)

- Runner [dry-run 38555455926](https://github.com/azharmz/ussy-trendfoll/actions/runs/38555455926) completed successfully using R2 READY date **2026-10-13**, and independently confirmed the latest feature date is also **2026-10-13**.
- Scope reported: **0 existing active v2 shadows; 21 active production positions without a v2 row; 19 have valid entry/ATR fields**.
- Prospective-cohort preview: **1 genuine T+1 position** and **18 late-bootstrap positions rejected**. The remaining 2 active positions lack valid entry/ATR data. This prevents retrospective shadow initialization from manufacturing skipped exit evidence.
- The latest R2 READY date was **2026-10-13**, so the snapshot was stale relative to the current date (2026-10-15). **Do not seed/write v2 using this stale snapshot.** Refresh/verify R2 READY freshness first.
- Log confirms `mode=DRY-RUN` and `no database writes attempted`. No v2 rows were created; no production state changed.
- After the cohort-preview runner change, regression workflow [run 38672141509](https://github.com/azharmz/ussy-trendfoll/actions/runs/38672141509) passed: runner/module compile plus **11/11 focused tests**.
- Runner now computes EMA20 directly from validated R2 READY OHLC rows using the production EMA formula, avoiding unrelated benchmark/sector downloads. The standalone runner is not imported by production `main.py`.

## Remaining blockers before live observation

1. Review the runner and its dry-run output on the actual R2 READY snapshot, confirming the as-of date and eligible cohort before any write.
2. Verify the service-role permission boundary and row counts during an explicitly approved first write; do not use a production workflow or production `main.py`.
3. Do not treat prior candidate-vs-current performance as evidence of edge: the frozen comparison had mismatched gap-fill semantics. A new paired research run must use the same executable fill rules for both sides.
4. Four v1 divergence cases remain undiagnosed at individual-bar level because the row-level query was blocked by the tool safety layer.

## Decision

**PASS:** 11 focused tests, full workflow-trigger topology review, and one actual read-only dry-run.

**NOT YET APPROVED:** live v2 observation, any Supabase write, automated daily execution, strategy promotion, or production changes.

Dry-run result: R2 READY date `2026-10-13`, 19 active production positions without v2 state, zero existing v2 rows. Review the cohort before approving any first write. Do not select write mode until the row-registration scope and service-role boundary are explicitly accepted.
