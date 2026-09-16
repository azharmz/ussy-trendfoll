# Full Signal Engine Audit — Evidence 10: Effective-Date State Semantics

Status: **REFINED CORRECTION IMPLEMENTED + REGRESSION PASS + UNTOUCHED VALIDATION V2 PASS / PRODUCTION DECISION PENDING / NO PRODUCTION CHANGE**

## Trigger

Evidence 09 found four READY securities whose terminal row was older than the global latest market date. This evidence follows that condition through the downstream production path before any production correction is authorized.

## Observed input condition

R2 READY guarantees sufficient rolling history but does not currently guarantee that every READY security has a row on the global latest market date.

Observed snapshot from Evidence 09:

- global latest market date: `2026-09-14`
- stale-terminal READY securities: 4 / 1,227
- `ZTEK`: last row `2026-09-10`
- `WILC`: last row `2026-09-03`
- `JFB`: last row `2026-09-03`
- `YYGH`: last row `2026-09-11`

## Production selection behavior

`r2_main.py` establishes one global `as_of_date` from the maximum feature-store date and constructs the current snapshot using only rows whose `date == as_of_date`.

Therefore stale-terminal READY securities are **not** compared cross-sectionally using their older terminal rows. They are absent from the current decision snapshot.

Classification for E9 cross-sectional comparison risk: **MATCH / COMMON EFFECTIVE DATE ENFORCED BY CURRENT SNAPSHOT SELECTION**.

The production entry point also retains a separate `universe` derived from every ticker in current R2 READY and computes `missing_latest = universe - latest`. This means the information needed to distinguish current-universe membership from common-date evaluability already exists at the orchestration layer.

## Downstream semantic consequence

Absence from the current snapshot is not neutral in every downstream consumer.

The original state model conflated signal invalidation with absence of a current-date row. The first research correction separated `INVALIDATED` from `DATA_UNAVAILABLE`, but subsequent trace exposed a second distinction: absence from `latest` can mean either a current READY member lacks a common-date row or a historical/watchlist symbol is no longer in the current READY universe.

Three materially different cases must therefore remain separate:

1. **Signal invalidation** — current-date evaluation exists and Investability falls below monitoring threshold.
2. **Data unavailable / stale terminal data** — symbol remains in current READY but lacks a common-date row.
3. **Out of current universe** — historical/watchlist symbol is not a member of current READY.

The common-date snapshot selection itself is correct. The defect was downstream information loss when state consumers did not receive current-universe membership.

Classification: **MISMATCH — CURRENT SNAPSHOT ABSENCE WAS UNDER-SPECIFIED WITHOUT CURRENT-UNIVERSE MEMBERSHIP**.

## Refined frozen intended contract

The correction must preserve these invariants:

1. Current cross-sectional decisions use one common `as_of_date` only.
2. A stale historical row must never be substituted as a current signal row.
3. `INVALIDATED` requires a current-date evaluation whose Investability is below monitoring threshold.
4. `DATA_UNAVAILABLE` means current R2 READY membership exists but the common-date row does not.
5. A historical/watchlist symbol absent from current R2 READY uses `OUT_OF_UNIVERSE`.
6. `OUT_OF_UNIVERSE` is neither `INVALIDATED` nor `DATA_UNAVAILABLE`.
7. Neither absence state may create `ACTIONABLE`, a new watch signal, or a production entry.
8. Historical watchlist/lifecycle facts remain immutable.
9. Restoration of current data resumes ordinary evaluation from current facts.
10. Universe re-entry is evaluated from current facts; stale prior signal state is not substituted.
11. Active positions retain fail-closed/fail-fast current-data protection.
12. T0-close / T+1-open execution semantics remain unchanged.

## Research implementation

The refined contract has now been implemented **only on `research/exit-development-hypotheses`**:

- `alert_state.py`: `compute_alert_transitions(latest, previous_watchlist, current_universe)` now distinguishes `DATA_UNAVAILABLE` from `OUT_OF_UNIVERSE` and rejects a `latest` snapshot containing symbols outside the supplied current universe. Refined implementation commit: `b5a7eade27b07124168ff1c0f737b35f8ac53322`.
- `candidate_lifecycle.py`: lifecycle construction/writing now receives explicit current-universe membership and preserves the same three-way semantics. Refined implementation commit: `5fc5fd70ba84d69fa6959aa139ef19e31d10efd1`.
- `r2_main.py`: derives `current_universe` from current READY and passes it to both downstream consumers. Refined orchestration commit: `160e5b042f5ebc74ac46e7a05c59bdf28b2912e3`.
- Existing alert/lifecycle tests were updated only for the explicit-universe interface; dedicated contract tests were expanded to 12 cases. Test commits include `cf58e1b0aae84094668bc934a1fc8dbaf7bc185b`, `6ec002185871686d3255f8256d81ba3c691fa02c`, and `58ccdd383ff197d033f2a874ed705e02ce5d645c`.

No production branch mutation is authorized or implied by these research commits.

## Regression evidence

### Run #9 — refined contract

Workflow: `Signal Engine Effective-Date State Audit`

- run: `35063691151`
- job: `104689249389`
- head: `58ccdd383ff197d033f2a874ed705e02ce5d645c`
- result: **SUCCESS**
- dedicated refined contract tests: **12 / 12 PASS**

### Run #10 — contract + downstream regression

Workflow update commit: `11d7eed5af2f509e16c109d311c7ac113f66fa30`.

- run: `35063901480`
- job: `104689883526`
- result: **SUCCESS**
- refined effective-date contract: **12 / 12 PASS**
- existing alert-state regression: **5 / 5 PASS**
- candidate-lifecycle module was included and produced no failure.

## Untouched governed validation

A separate validation suite was created after development/regression closure and kept outside the development characterization suite.

### Validation V1 — invalid harness, retained as evidence

The first frozen validation execution failed because four scenarios omitted the required `date` field from input fixtures. The implementation raised `KeyError: 'date'` before the intended semantic assertions could be evaluated. One independent fail-closed scenario passed.

- run: `35066426578`
- job: `104697632849`
- result: **FAILURE — VALIDATION HARNESS INPUT-CONTRACT ERROR**
- tests: 5 total; 1 semantic scenario reached/passed; 4 errored on missing required `date` input.

V1 was not edited after execution to manufacture a pass. It remains immutable evidence of an invalid validation harness.

### Validation V2 — corrected fixture contract, frozen before first execution

A new V2 suite was created with only the fixture-contract defect corrected before its first execution. It uses a mixed population and independently exercises alert/lifecycle three-way state separation, present failure versus two absence causes, re-entry from current facts, and fail-closed snapshot/universe inconsistency.

- frozen validation-suite commit: `d6e8045b4408a8553c3e1a5d0b118a2afcf181f2`
- workflow execution commit: `b0cff605b5fad22beef8032a5db725258ae35c95`
- workflow: `Signal Engine Effective-Date Untouched Validation V2`
- run: `35066531313`
- job: `104697955901`
- result: **SUCCESS**
- untouched validation: **5 / 5 PASS**

No implementation file was modified between V1 diagnosis and V2 execution. The V2 result therefore closes the governed untouched-validation gate for this correction.

## Correction boundary

The implemented research correction remains confined to orchestration membership propagation, alert-state semantics, candidate lifecycle semantics, tests, and research-only audit workflows. It does **not** change R2 OHLCV facts, feature formulas, Investability/Tradability aggregation, terminal EMA calculation, production entry formula, historical persisted observations, or active-position fail-fast behavior.

## Governance disposition

For this effective-date finding, the technical evidence chain is now complete through governed validation:

`root cause -> refined frozen correction spec -> research implementation -> 12/12 contract PASS -> downstream regression PASS -> untouched validation V2 5/5 PASS`

The next gate is an **explicit production decision**. A passing validation does not itself authorize deployment. Production remains unchanged until that decision is recorded in the full-audit governance context.
