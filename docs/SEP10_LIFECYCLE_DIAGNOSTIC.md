# Sep-10 Lifecycle Diagnostic — +61

Status: **CLOSED AS EXPLAINABLE MIGRATION / UNIVERSE-EXPANSION EFFECT**

This document is diagnostic evidence for the full signal-engine audit. It does not authorize a production rule change.

## Question

Why did lifecycle history contain 61 symbols with `first_watch_date = 2026-09-10`?

## Evidence chain

1. The legacy production pipeline used `main.py` and a hard-coded 197-symbol universe.
2. Legacy Actions run `34421332220` (job `102697198642`) executed on 2026-09-10 UTC from commit `05645e2aabc922f7bf673ef60a34d53e6ef22d2e`.
3. That run's latest market date was `2026-09-09`, not 2026-09-10, and it produced zero candidates from the 197-symbol legacy universe before later failing in position tracking on a NaN JSON serialization error.
4. Production was subsequently migrated from legacy `main.py` to R2-backed `r2_main.py`; commit `97ea8f03a9edd4c145e53857fb83a117bab350f7` is the production-path migration boundary identified during the audit.
5. Lifecycle integration smoke run `34789586106`, triggered from commit `553169647723c67f65011c7ae7bda3f1a07e937d`, completed successfully and uploaded candidate lifecycle artifact `candidate-lifecycle-43` (artifact ID `10328095915`, SHA256 `c596487a495a9fbb70accc875eb6b3517e05abfa1720a501a143356e5131f6b0`).
6. The artifact contains 161 lifecycle rows: 100 with a first-watch date before 2026-09-10 and exactly 61 with `first_watch_date = 2026-09-10`.
7. All 61 of those symbols were compared against the legacy 197-symbol production universe. Intersection: **0 / 61**.

## Root cause

The +61 population is not a mass transition of 61 previously evaluated securities from `FAIL` to `NEAR_PASS/PASS`.

Their prior production-engine state under the legacy universe was effectively:

`NOT EVALUATED / OUTSIDE LEGACY UNIVERSE`

When production coverage migrated to the much broader R2 READY universe, those securities became evaluable. Lifecycle reconstruction/persistence then recorded 61 newly covered securities associated with the 2026-09-10 market snapshot/history boundary.

Therefore the primary explanation is:

**UNIVERSE EXPANSION + PRODUCTION MIGRATION + LIFECYCLE INTEGRATION**

not a synchronized feature-engine transition.

## Classification

- Mass signal-engine transition hypothesis: **DISPROVEN as primary cause**.
- Legacy-universe contamination hypothesis: **DISPROVEN**. The 61 are specifically outside the legacy universe.
- Migration/universe-expansion explanation: **SUPPORTED**.
- Sep-10 +61 diagnostic: **CLOSED / EXPLAINABLE**.

This closure does not validate every feature formula. The independent full signal-engine audit remains active, including Stage, VCP/tightness, pivot semantics, volume semantics, EMA basis consistency, benchmark freshness, and downstream lifecycle/alert consumers.