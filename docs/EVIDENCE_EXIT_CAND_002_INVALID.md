# EXIT-CAND-002 — Development Invalidation Record

Status: **INVALID / GAP-THROUGH EXECUTION CONTRACT MISSING / DO NOT VALIDATE**

## Provenance
- Development workflow run: `34947809994`
- Head SHA: `9d967dfceb9cb2d589b71746f26f54ab89604ce4`
- Repository tests: 12/12 PASS.
- Candidate development terminated fail-closed before summary/artifact outcome creation.

## Defect
First detected case: ACAD, T0 2015-02-17, day 17.

- low: 33.33000183105469
- operative stop: 41.82651020071276
- high: 36.72999954223633

The market gapped through the already-valid operative long sell-stop. The frozen EXIT-CAND-002 contract still required an exact-stop fill, which is infeasible when the day's opening/entire range is below the stop.

This is distinct from EXIT-CAND-001's pre-entry stop-arming defect. EXIT-CAND-002 fixed activation but did not specify gap-through execution.

## Governance consequence
EXIT-CAND-002 is retired without candidate outcomes. It will not be patched in place. A new candidate ID must freeze complete daily-OHLC sell-stop execution before outcomes are observed.
