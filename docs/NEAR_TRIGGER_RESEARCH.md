# NEAR_TRIGGER Research Governance

Status: **DEVELOPMENT-FROZEN / SHADOW-ONLY / NOT PRODUCTION-VALIDATED**

This work does not change the existing Investability or Tradability definitions, position-entry rules, or exit rules.

## Data boundary

Development evidence used the trusted R2 ready snapshot reported by the research run as `2026-08-28`, covering 367,203 daily rows across 1,226 ready securities.

Breakout onset is defined as:

`has_breakout[t] == True AND has_breakout[t-1] == False`

Pre-event observations must:

- have Investability >= `NEAR_PASS`
- have `has_breakout == False`
- have a non-negative distance to the prior pivot

## Refined development evidence

Independent breakout onsets: **8,497**.

Median distance before onset:

| Lead | Distance to prior pivot | ATR-normalized distance |
|---|---:|---:|
| T-1 | 1.79% | 0.49 ATR |
| T-2 | 2.82% | 0.77 ATR |
| T-3 | 3.03% | 0.82 ATR |
| T-5 | 3.56% | 0.96 ATR |

Forward onset probability for monitored, non-breakout observations showed monotonic separation by distance. The nearest ATR quintile (`0–0.602 ATR`, median 0.335 ATR) had onset rates of approximately:

- 23.85% within 1 trading day
- 35.34% within 2 trading days
- 43.12% within 3 trading days
- 51.57% within 5 trading days

The farthest ATR quintile (`>2.237 ATR`, median 2.83 ATR) had approximately:

- 0.35% within 1 trading day
- 1.31% within 2 trading days
- 2.55% within 3 trading days
- 6.07% within 5 trading days

ATR-normalized distance separated near-term breakout probability slightly more cleanly than raw percentage distance.

## Frozen development candidate

For shadow observation only:

- Investability >= `NEAR_PASS`
- no breakout yet
- `0 <= distance_to_prev_pivot_atr <= 0.60`

The value **0.60 ATR** is frozen as the development candidate because it corresponds to the nearest empirical quintile boundary in the refined development corpus. It must not be tuned against future validation outcomes.

Implementation: `near_trigger_shadow.py`.

# PRE-REGISTERED FORWARD VALIDATION PROTOCOL

Status: **FROZEN BEFORE OUTCOME REVIEW**

The purpose of forward validation is only to determine whether the frozen 0.60 ATR proximity rule deserves promotion from shadow-only alertability to production alert-state semantics. It is **not** a profitability test and does not authorize pre-breakout entries.

## 1. Untouched validation boundary

Only genuinely new market bars after the development boundary may contribute to the one-shot validation verdict.

- Development R2 snapshot boundary: `2026-08-28`.
- Formal Cycle 1 accumulation starts on **2026-09-15**.
- Any observation whose required forward outcome window overlaps already-inspected development data is excluded.
- Once the validation outcome set is opened for formal verdict calculation, the 0.60 ATR rule and the criteria below may not be changed within that cycle.

## 2. Validation unit: independent shadow episode

Daily bars are **not** treated as independent observations.

A new shadow episode begins only when a symbol changes from:

`near_trigger_shadow == False → True`

while still satisfying:

- Investability >= `NEAR_PASS`
- `has_breakout == False`
- non-negative ATR-normalized pivot distance
- `distance_to_prev_pivot_atr <= 0.60`

Consecutive days inside the same shadow state belong to the same episode and count once.

A symbol may start a later new episode only after first leaving the shadow state and subsequently re-entering it. This prevents one long-lived setup from creating pseudo-replicated observations.

## 3. Forward outcomes

For each independent shadow episode start, measure whether an **independent breakout onset** occurs within:

- 1 trading day
- 2 trading days
- 3 trading days
- 5 trading days

Breakout onset remains frozen as:

`has_breakout[t] == True AND has_breakout[t-1] == False`

Also record whether the setup becomes no longer monitored before any breakout onset. This is the `invalidation_before_breakout` diagnostic.

## 4. Control population: independent control episodes

The primary control is defined at the **episode level**, not as repeated daily bars, so the lift denominator is comparable to the shadow-episode numerator.

A new control episode begins only when a symbol changes from not being in the eligible farther-distance state to being in that state:

`control_state == False → True`

where `control_state` requires:

- Investability >= `NEAR_PASS`
- `has_breakout == False`
- non-null ATR-normalized pivot distance
- `distance_to_prev_pivot_atr > 0.60`

Consecutive days in the farther-distance control state count as one control episode. A later control episode for the same symbol requires leaving the state and subsequently re-entering it.

For diagnostics, control episodes should additionally be stratified by their start distance into:

- `(0.60, 1.10] ATR`
- `(1.10, 1.59] ATR`
- `(1.59, 2.237] ATR`
- `> 2.237 ATR`

These boundaries are inherited from the already-inspected development quintiles and are not to be refit on validation data.

**Pre-start governance correction:** the initial implementation counted shadow states as independent episodes but farther-distance controls as daily rows. That creates a non-comparable lift denominator. This was corrected to independent control episodes on **2026-09-14**, before the formal Cycle 1 start date and before any Cycle 1 outcomes were available. The correction therefore does not contaminate the untouched validation period.

## 5. Minimum evidence before verdict

Do **not** issue PASS/FAIL until all of these are met:

- at least **150 independent shadow episodes**
- at least **75 unique symbols** represented among shadow episodes
- at least **40 independent breakout onsets within 5 trading days** among those episodes
- at least one matured independent control episode is available for lift calculation
- every episode included in the verdict has a complete 5-trading-day forward observation window unless an onset or invalidation occurs earlier

Until all conditions are met, status remains:

`FORWARD VALIDATION ACCUMULATING / NO VERDICT`

## 6. Pre-registered primary PASS criteria

Promotion requires **all** primary criteria below:

1. **3-day absolute onset rate >= 20%** for independent shadow episodes.
2. **5-day absolute onset rate >= 30%** for independent shadow episodes.
3. **3-day lift >= 1.50x** versus eligible independent farther-distance control episodes.
4. **5-day lift >= 1.50x** versus eligible independent farther-distance control episodes.

The absolute-rate floors are deliberately below the development estimates (43.12% at 3d and 51.57% at 5d) so validation tests persistence of useful separation rather than exact replication of development magnitude.

The lift requirement prevents a high absolute rate during a universally strong breakout regime from being mistaken for distance-specific predictive value.

## 7. Secondary diagnostics — reported but not tunable gates

Always report, but do not use to silently rescue a failed primary verdict:

- 1-day and 2-day onset rates and lift
- `invalidation_before_breakout` rate
- median ATR distance at episode start
- unique-symbol concentration
- sector concentration, if sector coverage is sufficiently complete
- market-regime breakdown, if each reported regime has adequate sample size
- outcome rates by the frozen farther-distance control strata

No new threshold may be introduced after outcomes are inspected.

## 8. Verdict rules

### PASS

If minimum evidence is met and all four primary PASS criteria are met:

`PRODUCTION-VALIDATED FOR ALERTABILITY`

This permits a separate production change to redefine true `NEAR_TRIGGER` as the validated proximity state. It does **not** change entry rules or make pre-breakout rows tradable.

### FAIL / DEFERRED

If minimum evidence is met but one or more primary criteria fail:

`DEFERRED / NOT PRODUCTION-VALIDATED`

Do not retune 0.60 ATR on the same validation corpus.

A future research cycle may propose a new development candidate only after explicitly opening a new development phase with a new evidence boundary.

### INSUFFICIENT

If minimum evidence is not met:

`FORWARD VALIDATION ACCUMULATING / NO VERDICT`

## 9. Production promotion boundary

Even after a PASS verdict, promotion is a separate governed change.

Expected lifecycle after successful validation:

`WATCH → NEAR_TRIGGER → ACTIONABLE → LOST_TRADABILITY / INVALIDATED`

where:

- `WATCH` = monitored/investable but not within the validated proximity boundary
- `NEAR_TRIGGER` = monitored, no breakout, and `0 <= distance_to_prev_pivot_atr <= 0.60`
- `ACTIONABLE` = existing production Investability/Tradability entry semantics; unchanged by this research

The current production `alert_state.py` still uses `NEAR_TRIGGER` as a broad monitored/non-actionable label. That semantic mismatch remains intentionally unresolved until validation passes.

## 10. No post-validation tuning

The following are frozen for this validation cycle:

- 0.60 ATR boundary
- shadow episode-start definition
- independent control episode definition
- breakout-onset definition
- 1/2/3/5-day horizons
- minimum evidence requirements
- 3-day and 5-day absolute-rate floors
- 1.50x lift gates
- control-distance definition and diagnostic ATR strata

Changing any of these after formal outcome inspection invalidates the cycle as untouched validation.
