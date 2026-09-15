# PROB-013 — Progress Checklist

Current marker: **RC-004 SUPPORTED → EXIT-CAND-003 DEVELOPMENT PASS → UNTOUCHED VALIDATION PASS → PRODUCTION SHADOW IMPLEMENTED + PERSISTENCE DEPLOYED → STOP-EXEC-001 DEFECT CONFIRMED → OPERATIONAL SHADOW EVIDENCE NEXT → NO PRODUCTION CHANGE**

- [x] DIAG-003 exit/risk conversion root cause supported
- [x] EXIT-ISO-001 component attribution evidence-locked
- [x] EXIT-CAND-001 invalidated for execution-feasibility defect
- [x] EXIT-CAND-002 invalidated for missing gap-through execution contract
- [x] EXIT-CAND-003 representation frozen pre-outcome
- [x] EXIT-CAND-003 development run completed
- [x] EXIT-CAND-003 development PASS evidence-locked
- [x] Untouched validation protocol frozen before outcomes
- [x] Validation sample frozen to deterministic ranks 101–200
- [x] Zero development-validation security overlap asserted
- [x] Validation tests/invariants added
- [x] GitHub Actions untouched-validation workflow added
- [x] Untouched validation completed successfully
- [x] Corpus/comparator/feasibility integrity verified
- [x] Frozen validation gate PASS
- [x] Validation PASS evidence-locked
- [x] Separate production shadow plan designed
- [x] Implement non-decisioning production shadow contract (`exit-cand-003-shadow-v1`)
  - immutable 2ATR14(T0) initial guard + HH22 − 3×WilderATR22 Chandelier
  - gap-through fill at observed Open; intraday touch at operative stop
  - next-session-only ratchet; EMA20 retained; 45-session observation boundary
  - dedicated persistence table with unique `(position_id, contract_version)`
  - wired strictly after authoritative production position/exit path
  - shadow module never writes to `positions` and does not feed notifications/decisions
  - frozen-contract and Chandelier unit tests added
- [x] Apply shadow persistence schema to production Supabase
  - RLS enabled
  - read-only `anon`/`authenticated` policy retained
  - explicit Data API grants added for current Supabase defaults
  - `service_role` SELECT/INSERT/UPDATE verified
  - `anon` SELECT verified
- [x] Complete separate `STOP-EXEC-001` CURRENT gap-through audit
  - authoritative run `34967551005` SUCCESS
  - exact paired comparable events `1,524`
  - CURRENT stop events `839`
  - gap-through events `93` (`11.0846%` of CURRENT stop events)
  - median gap slippage vs stop `-1.1347%`; worst `-17.0903%`
  - CURRENT exact-stop execution-feasibility defect confirmed and evidence-locked
  - no production mutation from the audit
- [ ] Collect shadow operational evidence
- [ ] Explicit production promotion/rejection governance decision

Frozen constraints remain: no post-validation tuning of EXIT-CAND-003; no immediate production exit change; near-trigger forward validation remains a separate workstream.

## Shadow implementation commits

- engine: `d7a66cf2fab893beff2528e044b3b9d93cfe88f4`
- initial persistence schema: `a769102ba0a23c9832a4a794239555ea37932e9e`
- unit tests: `f722e2219f437e54ac0cf03a4b090e524adb897f`
- legacy/main pipeline wiring: `9d17355a75593a76f8167207908568e885c9a775`
- R2 production pipeline wiring: `668026c092354a855aa663b3465c5683c6a0771f`
- explicit Supabase Data API grants: `675e4545f4f2a4890dcdda84cc4714e0855cc74d`

## STOP-EXEC-001 evidence

- frozen protocol: `docs/STOP_EXEC_001_AUDIT_PROTOCOL.md`
- runner: `run_stop_exec001.py`
- tests: `tests/test_stop_exec001.py`
- workflow: `.github/workflows/stop-exec001.yml`
- evidence lock: `docs/EVIDENCE_STOP_EXEC_001.md`
- evidence commit: `8feb52dd457662dd912a403e0fcaa92f43f56df6`
