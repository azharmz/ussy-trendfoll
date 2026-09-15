# EXIT-CAND-001 — Development Invalidation Record

Status: **INVALID / EXECUTION-FEASIBILITY DEFECT / DO NOT VALIDATE / DO NOT USE OUTCOMES**

## Provenance

- Frozen representation: `docs/EXIT_CANDIDATE_REPRESENTATION_001.md`
- Development workflow run: `34933926726`
- Head SHA: `ad14cadefd4bae99c24aa4d25b160c9cd0d3b2bd`
- Artifact: `exit-candidate001-development-3`
- Artifact ID: `10383425149`
- Artifact SHA256: `fa3b3d16bcf288265ca1cb55d922f1a51f28f664471698ce6a12209dae49c441`

## Defect

The implementation initialized the candidate operative stop as:

`max(initial_stop, prior_chandelier)`

A pre-entry Chandelier value can already be above the entry/current tradable price. The daily-bar simulator then treated `low <= stop` as a stop touch and filled exactly at that stop. For a long sell-stop this can create infeasible fills above the day's reachable market path, including day-1 exits above entry when the day's high never reached the recorded exit price.

This is a material execution-feasibility defect, not a reporting defect.

## Governance consequence

All EXIT-CAND-001 and EXIT-CAND-001B development outcomes from this run are invalid as candidate evidence. They must not be used for candidate selection, validation, or production decisions.

The CURRENT control remains useful only as a corpus/implementation consistency check because it reproduced the already-established EXIT-ISO-001 baseline.

EXIT-CAND-001 is retired. It will not be patched in place. A new candidate ID must be frozen before any new candidate outcome is observed.
