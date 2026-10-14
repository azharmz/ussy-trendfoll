# EXIT-CAND-003 Shadow v2 — Integration & Operational Readiness Audit

Date: 2026-10-14
Branch: `research/exit-cand-003-shadow-v2-no-time-cap`
Status: **IMPLEMENTATION TESTED; NOT OPERATIONALLY ACCEPTED; NOT DEPLOYED**

## Verified

- Focused workflow `.github/workflows/exit-candidate003-shadow-v2-tests.yml` is `workflow_dispatch` only, checks out this research branch, and runs only `test_exit_candidate003_shadow_v2.py`.
- Successful focused workflow: [run 38552172388](https://github.com/azharmz/ussy-trendfoll/actions/runs/38552172388), 8/8 tests passed.
- Selected workflow review:
  - `.github/workflows/daily.yml`: manual `workflow_dispatch` only; production pipeline has a concurrency group `ussy-trendfoll-production`.
  - `.github/workflows/exit-candidate003-development.yml`: `push` limited to `research/exit-development-hypotheses` and selected paths, plus manual dispatch.
  - `.github/workflows/exit-candidate003-validation.yml`: manual dispatch only.
  - `.github/workflows/cand003-shadow-session-ledger.yml`: push limited to its dedicated research branch and listed paths, plus manual dispatch.
- `main.py` imports and invokes `exit_candidate003_shadow.run_shadow(...)` (v1). It does **not** import or invoke v2. This is the correct no-production-change state, but means v2 has no operational session runner yet.
- V2 reuses the existing shadow and session-ledger tables with the distinct `contract_version`; the composite uniqueness constraints were previously verified read-only. No schema migration is currently indicated.
- V2 module reads production positions for comparison and writes only versioned shadow rows/session evidence. Its code does not issue writes to `positions`.

## Readiness blockers / limitations

1. **No v2 runner wiring:** Do not add v2 to production `main.py`. A separately gated research runner is required, with an explicit input/as-of date and no production writes.
2. **Operational workflow topology audit is partial:** The relevant workflows above were inspected, but this is not a complete enumeration of every workflow in the repository. Therefore no workflow run, scheduled execution, or database write is authorized by this audit.
3. **No live v2 cohort:** No v2 rows were seeded and no v2 session evidence was written. Forward-only operation and actual table permissions remain unverified in practice.
4. **Coverage gap:** Current v2 focused tests cover the frozen exit rules and ledger replay invariants. They do not yet test the full registration/update path against a faithful Supabase client or assert that the production `positions` table receives no mutation calls.
5. **Comparator issue remains:** The frozen validation comparison used mismatched gap-fill semantics; do not use its apparent improvement as proof of edge. A new paired research run must apply the same executable fill rules to both sides.
6. The row-level divergence query for four existing v1 cases was blocked by the tool safety layer; their individual causes remain unknown.

## Decision

**PASS:** focused unit tests and selected static integration checks.

**NOT READY:** operational v2 observation, automated daily execution, strategy promotion, or production changes.

## Safe next steps

- Add tests for late-bootstrap rejection, production-table write isolation, and end-to-end session advancement using a faithful fake client.
- Implement a standalone/manual-only research runner on this branch; it must not be imported by production `main.py`.
- Complete the all-workflow trigger audit and verify required secrets/permissions without exposing them.
- Review the runner and execution plan before any live v2 write. Until then, keep v2 tables untouched.
