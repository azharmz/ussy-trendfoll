# EXIT-CAND-003 — Untouched Validation Results (2026-10-14)

Status: **VALIDATION GATE PASS / NOT PRODUCTION**

- Frozen protocol: `docs/EXIT_CAND_003_VALIDATION_PROTOCOL.md`
- Frozen candidate: `docs/EXIT_CANDIDATE_REPRESENTATION_003.md`
- Workflow run: [38536712930](https://github.com/azharmz/ussy-trendfoll/actions/runs/38536712930)
- Evidence artifact: `exit-candidate003-validation-4` (artifact ID `11881090706`)
- R2 READY snapshot / evaluation boundary: `2026-08-28`

## Corpus integrity

| Evidence | Result |
|---|---:|
| Deterministically ranked development securities | 100 (ranks 1–100) |
| Validation securities | 100 (ranks 101–200) |
| Development/validation security overlap | 0 |
| Validation securities with eligible research rows | 86 |
| Eligible onsets before exact pairing | 1,532 |
| Exact paired comparable events | 1,525 |

Historical universe membership is based on the current R2 READY snapshot, not point-in-time membership; this study is not survivorship-bias-free. This is a **cross-sectional security holdout**, not a future-time holdout. Both groups use the same historical evaluation boundary.

## Frozen gate results

| Metric | CURRENT | EXIT-CAND-003 | Gate |
|---|---:|---:|---|
| Median realized return | -3.069% | -2.098% | PASS — candidate higher by 0.972 percentage points |
| Positive-return fraction | 33.25% | 35.02% | PASS — candidate higher by 1.77 percentage points |
| Median MAE-to-exit | -4.319% | -3.627% | PASS — candidate less adverse by 0.693 percentage points |
| Median MFE-to-exit | +4.866% | +4.332% | Descriptive; not a gate |
| Median holding | 16 trading days | 12 trading days | Descriptive; not a gate |
| Exact paired event count | 1,525 | 1,525 | PASS |
| Feasibility invariants | — | PASS | PASS |
| Development/validation overlap | — | 0 | PASS |

Exit reasons:

- **CURRENT:** 780 stop-loss, 443 EMA20 trend exit, 302 45-day boundary.
- **EXIT-CAND-003:** 169 gap-through stops, 1,146 intraday stop touches, 162 EMA20 trend exits, 48 observation boundaries.

The median of paired event-level return deltas is 0.0%; this is distinct from the 0.972 percentage-point difference between the two group medians. The frozen protocol compares the latter for its gate.

## Comparator limitation

Per the frozen protocol, CURRENT retains the exact earlier comparator semantics, including its theoretical stop fill when a daily low crosses the stop. It is **not** retrofitted to gap-aware fills in this experiment. The separate stop-execution audit remains open, so these results do not establish the live production fill model's comparative edge.

## Verification and governance

- The two focused EXIT-CAND-003 test modules passed.
- The full repository test suite still reports four unrelated errors in `test_effective_date_state_validation.py` involving missing `date` columns / `KeyError: 'date'`. The workflow preserves that result as baseline visibility and does not let it block the focused exit validation. Those failures were not modified as part of this exit experiment.
- The workflow was restored to `workflow_dispatch` only after the one-time run; the dispatch marker was removed. No sibling workflow ran.
- No production exit logic, production positions, strategy thresholds, or database rows were changed by this validation.

## Terminal verdict

**EXIT-CAND-003 = DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION.**

This PASS authorizes only a separate productionization/shadow-design decision phase. It does not authorize an immediate production exit change. The candidate must remain observational until the productionization phase explicitly resolves the comparator-fill limitation, operational evidence requirements, and acceptance controls.
