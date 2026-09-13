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

## Validation boundary

The development corpus has already been inspected, so it cannot serve as untouched validation for this boundary.

Production promotion therefore requires genuinely new evidence, preferably future R2 bars not used in this development cycle. Forward validation should measure at minimum:

- count of shadow observations
- independent breakout onset within 1/2/3/5 trading days
- calibration/base rate relative to farther-distance monitored observations
- invalidation rate before breakout
- stability across symbols/sectors and market regimes where sample size permits

No post-validation tuning of the 0.60 ATR boundary is allowed within the same validation cycle. If it fails, verdict should be `DEFERRED / NOT PRODUCTION-VALIDATED` rather than tuned on the validation sample.
