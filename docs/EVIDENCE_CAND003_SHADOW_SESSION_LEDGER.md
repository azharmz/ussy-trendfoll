# Evidence — CAND-003 Production Shadow Session Ledger

Status: IMPLEMENTED + DATABASE DEPLOYED + CI PASS / FIRST LIVE SESSION EVIDENCE PENDING

Date: 2026-09-16 (Asia/Makassar)
Branch: `research/cand003-shadow-session-ledger`
Shadow contract: `exit-cand-003-shadow-v1`

## What changed

The existing mutable `exit_candidate003_shadow` state remains unchanged in purpose. A separate append-only evidence table, `public.exit_candidate003_shadow_sessions`, now records the frozen per-session shadow inputs, operative stop, HH22/Wilder ATR22/Chandelier, next-session stop, hypothetical exit, and production-position comparison fields.

Application invariant key:

`(position_id, session_date, contract_version)`

Identical replay is idempotent. Divergent evidence for the same invariant key raises a runtime error before mutable shadow state is advanced.

The shadow evaluator still never writes `positions` and production comparison fields are attached only after the hypothetical shadow decision is calculated.

## Frozen execution semantics verified by tests

- gap-through is checked before intraday stop touch and fills at observed Open;
- non-gap touch fills at the operative stop;
- session-t Chandelier can only ratchet the next-session stop;
- survivor evidence records both operative-stop-before and next-operative-stop;
- production comparison data is not an input to the shadow decision;
- identical replay produces one ledger identity;
- divergent duplicate evidence is rejected.

## CI evidence

Workflow: `CAND-003 Shadow Session Ledger`

Authoritative latest tested head at time of implementation: `a8a3ab301d7686f8b811ab303a50f6e05ed3dca9`
Run ID: `35032501740`
Job ID: `104593994330`
Conclusion: `success`

The workflow explicitly runs unittest discovery against `tests/test_exit_candidate003_shadow.py` and greps for named ledger tests, closing the previous bare-pytest-vs-unittest discovery ambiguity.

Observed CI result: **9 tests run, 9 passed**. `python -m py_compile exit_candidate003_shadow.py` also passed.

## Supabase deployment verification

Project: `USSY Trendfoll` (`rggtylvlrzzesrtumqzj`)

Verified after DDL deployment:

- table exists;
- RLS enabled;
- read-only SELECT policy for `anon, authenticated` exists;
- effective table grants are exactly:
  - `anon`: SELECT
  - `authenticated`: SELECT
  - `service_role`: SELECT, INSERT
- service role has no UPDATE/DELETE on the evidence ledger;
- invariant unique constraint is defined in schema;
- covering index for `shadow_id` foreign key was added after performance advisor identified it;
- Supabase security advisor: **0 findings**;
- performance advisor: no remaining unindexed-FK finding; only INFO-level unused-index notices, expected for a newly empty evidence table.

During verification, broad default privileges (`REFERENCES/TRIGGER/TRUNCATE`) inherited by the new public table were detected and removed. The committed schema now uses `REVOKE ALL` followed by explicit least-privilege grants.

## Current operational evidence state

At deployment verification time:

- session ledger rows: `0`
- duplicate invariant keys: `0`

This is expected because the new application code is isolated on the implementation branch and has not been promoted into the authoritative production execution branch. No synthetic production row was inserted merely to manufacture operational evidence.

Therefore the correct terminal state is:

`APPEND-ONLY LEDGER IMPLEMENTED + SCHEMA DEPLOYED + DISCOVERED TESTS PASS + SECURITY VERIFIED → FIRST REAL SHADOW SESSION EVIDENCE PENDING → NO PRODUCTION EXIT CHANGE`

## Governance

No CAND-003 parameter changed. No production exit rule changed. No Investability/Tradability rule changed. No synthetic live evidence was created.
