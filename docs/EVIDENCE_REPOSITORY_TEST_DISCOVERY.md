# Evidence — Repository Test Discovery and CAND-003 Reporting

**Date:** 2026-10-14  
**Status:** REPOSITORY-WIDE PYTEST CI ACTIVE / 104 TESTS PASS / REPORTING QUIRK FIXED

## Test discovery finding

The repository had a mix of `unittest.TestCase` tests and top-level pytest-style `test_*` functions. Several existing workflows used `python -m unittest discover -s tests`, which does not collect top-level pytest functions. Some pytest files had their own targeted workflows, but there was no single repository-wide run.

Examples of top-level pytest-style files found during the audit included `tests/test_candidate_lifecycle.py`, `tests/test_near_trigger_shadow.py`, `tests/test_near_trigger_validation.py`, `tests/test_prob017_position_identity.py`, `tests/test_sector_cache_coverage.py`, `tests/test_signal_path_diagnostic.py`, `tests/test_stop_exec001.py`, and `tests/test_trend_filter_candidate.py`. Several are covered by focused workflows; the new suite provides one complete collection path for all test files.

## Changes and validation

- PR [#18](https://github.com/azharmz/ussy-trendfoll/pull/18) added `.github/workflows/repository-tests.yml`, which installs test dependencies and runs `python -m pytest -q tests` on relevant pull requests and via manual dispatch.
- The first full run surfaced six stale test failures (102 passed, 6 failed): lifecycle fixtures omitted the required current-universe argument; DIAG-003 test dates mixed strings and timestamps; a position test still expected the removed `MAX_HOLDING_DAYS` constant; and the STOP-EXEC-001 test fixture placed the supposed stop event on the entry bar. Those tests/fixtures were corrected without changing production trading behavior or the frozen historical audit contract.
- PR #18 merged as `68050f7db5e5b7cf393a54249b95e58b9b60b66d`. Workflow run `38554600137` passed: **102 passed, 4 warnings**.

## Reporting-only defect found and fixed

`run_exit_candidate003_development.py` emits CAND-003 stop exits as `risk_stop_gap` or `risk_stop_touch`, but previously called `base.stop_timing()`, which only counted `risk_stop`. Consequently the development summary field `stop_touch_timing.stop_events` could report zero while the detailed `exit_reasons` showed stop exits.

PR [#19](https://github.com/azharmz/ussy-trendfoll/pull/19) added a CAND-003-specific reporting helper that aggregates both risk-stop reasons for timing statistics while leaving their detailed reason counts intact and preserving CURRENT's `stop_loss` reporting. Two focused regression tests were added. PR #19 merged as `22dca70a65d6c4487087df329ca7366a8713d5cb`. Workflow run `38554865357` passed: **104 passed, 4 warnings**.

## Scope and remaining note

- These changes are test harness, fixture, and development-summary reporting corrections only.
- No CURRENT production exit semantics, stop parameters, CAND-003 frozen parameters, or shadow state were changed by this work.
- Four warnings remain in the complete suite, including pandas `Timestamp.utcnow` deprecation warnings in `positions.py`; they are not test failures and are not silently folded into this work item.

## Completion

Repository-wide test discovery and the `stop_touch_timing` reporting-only debt are **DONE / EVIDENCE RECORDED**. Future pull requests touching the repository test suite receive full pytest collection through `.github/workflows/repository-tests.yml`.