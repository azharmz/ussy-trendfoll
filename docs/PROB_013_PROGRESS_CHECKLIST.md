# PROB-013 — Progress Checklist

Current marker: **RC-004 SUPPORTED → EXIT-CAND-003 DEVELOPMENT PASS → UNTOUCHED VALIDATION PASS → PRODUCTION SHADOW IMPLEMENTED → OPERATIONAL EVIDENCE NEXT → NO PRODUCTION CHANGE**

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
- [ ] Apply `sql/schema_exit_candidate003_shadow.sql` to production Supabase before first live shadow run
- [ ] Collect shadow operational evidence
- [ ] Complete separate `STOP-EXEC-001` CURRENT gap-through audit before any production promotion decision
- [ ] Explicit production promotion/rejection governance decision

Frozen constraints remain: no post-validation tuning of EXIT-CAND-003; no immediate production exit change; near-trigger forward validation remains a separate workstream.

## Shadow implementation commits

- engine: `d7a66cf2fab893beff2528e044b3b9d93cfe88f4`
- persistence schema: `a769102ba0a23c9832a4a794239555ea37932e9e`
- unit tests: `f722e2219f437e54ac0cf03a4b090e524adb897f`
- legacy/main pipeline wiring: `9d17355a75593a76f8167207908568e885c9a775`
- R2 production pipeline wiring: `668026c092354a855aa663b3465c5683c6a0771f`
