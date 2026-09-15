# Exit Development Hypotheses — Post DIAG-003

Status: **PRE-OUTCOME HYPOTHESIS SET / NOT A PRODUCTION CONTRACT / NOT YET VALIDATED**

## Why this document exists

DIAG-003 established `RC-004`: the current exit/risk stack materially weakens realized outcomes in the governed event corpus, but DIAG-003 did not isolate which exit component is responsible and does not authorize tuning.

This document therefore defines a small, conceptually distinct hypothesis set **before** comparing alternative exit outcomes. It is intended to prevent parameter mining.

## Evidence boundary

Known from governed repo evidence:
- current stack = fixed initial 2 ATR stop + EMA20 close-loss + 45-trading-day maximum;
- on the 45-bar-mature DIAG-003 subset, current-rule median realized return was -3.46% / 33.01% positive versus the frozen day-45 endpoint counterfactual +1.70% / 56.43% positive;
- stop loss was the dominant exit reason;
- median current holding time was 16 bars while median time-to-45-bar-MFE was 27 bars;
- both MFE and MAE widen with horizon.

These facts motivate mechanism isolation, not a choice of replacement parameters.

## External methodology boundary

The hypothesis family is constrained by established trend-following concepts rather than a search over arbitrary numbers:

1. **Trend-state exit** — moving-average rules are a standard trend-following representation; research comparing momentum and moving-average rules supports MA-based trend-state signals as a legitimate mechanism class.
2. **Ratchet/trailing volatility stop** — ATR trailing stops are a recognized path-dependent trend/risk mechanism in which the operative stop can ratchet upward rather than remain permanently anchored to entry.
3. **Hard-loss protection + trend exit** — conceptually separates catastrophic/initial risk control from normal trend termination instead of asking one fixed entry-anchored volatility stop to perform both roles.

External literature is methodology support only. It does not prove that any candidate works in the USSY universe.

## Candidate mechanism set

### H-EXIT-01 — Trend-state primary exit

Hypothesis: the position should normally remain open while its short-term trend state remains intact, with the existing EMA20 close-loss used as the primary normal exit mechanism; the initial hard-risk stop remains as protection, but the arbitrary 45-day maximum is not treated as evidence-backed trend termination.

Purpose: isolate whether the fixed 45-day cap is truncating valid trends and whether EMA20 can serve as the normal trend-state exit.

Not authorized yet:
- removing the hard stop;
- changing EMA20 to another period;
- declaring unlimited holding production-valid.

### H-EXIT-02 — Ratcheting volatility-risk exit

Hypothesis: after entry, risk protection should be allowed to move upward with favorable price development rather than remain fixed forever at `entry - 2*ATR(T0)`.

Mechanism class: monotonic ATR-based trailing stop, conceptually `S_t = max(S_{t-1}, reference_price_t - k*ATR_t)`.

Purpose: test whether a path-adaptive risk mechanism better converts extended favorable excursions while preserving a bounded downside mechanism.

Frozen restriction for the next development stage: **do not grid-search `k`**. A multiplier may only be selected from an independently justified methodology contract before outcome comparison.

### H-EXIT-03 — Initial-risk then trend-management separation

Hypothesis: early failure protection and mature-trend management are different jobs. Keep an explicit initial-loss guard during the vulnerable post-entry phase, then allow trend-state/path-adaptive management to govern surviving positions.

Purpose: directly address DIAG-003's combination of accumulating stop touches in the first 10 bars and later median time-to-MFE.

Frozen restriction: no optimization of a switch day is allowed. A phase-transition condition must be structural (for example, a predefined risk-state or trend-state event) and frozen before outcome comparison.

## Explicitly excluded from the first development cycle

To avoid outcome mining, the following are excluded unless new independent evidence justifies a separate hypothesis:
- brute-force ATR multiplier grids;
- EMA period grids;
- fixed holding-day grids;
- arbitrary profit-target grids;
- combinations selected because they maximize CAGR/median return on the DIAG-003 corpus;
- post-hoc gap/momentum thresholds;
- portfolio sizing optimization.

## Development sequence

1. **Mechanism-isolation diagnostic (next):** replay the same governed event paths with one current exit component removed/isolated at a time, using only existing parameters and the frozen day-45 observation boundary. This is attribution, not candidate optimization.
2. Use that isolation evidence plus authoritative methodology to select at most **one primary and one fallback** development representation.
3. Freeze all representation details before evaluating development outcomes.
4. Run development evaluation on a designated development corpus.
5. Freeze the candidate.
6. Run untouched validation on a separately designated validation corpus with no post-validation tuning.
7. Production change requires explicit validation PASS and governance update.

## Immediate next diagnostic: EXIT-ISO-001

Question: within the current exit stack, which existing component is most associated with the conversion loss?

Pre-registered counterfactuals, all using existing parameters only and a maximum observation horizon of 45 forward bars:
- **CURRENT:** 2 ATR fixed stop + EMA20 + day-45 maximum.
- **NO_STOP:** EMA20 + day-45 maximum; ignore fixed 2 ATR stop.
- **NO_EMA20:** fixed 2 ATR stop + day-45 maximum; ignore EMA20 exit.
- **DAY45_ONLY:** day-45 close only; ignore stop and EMA20 (already conceptually represented in DIAG-003, reproduced for exact comparability).

No alternative ATR multiplier, EMA period, or holding horizon is permitted in EXIT-ISO-001.

Primary attribution outputs:
- median realized return and positive rate;
- return distribution/IQR;
- exit-reason distribution;
- median holding time;
- MFE/MAE to realized exit;
- give-back;
- pairwise per-event delta versus CURRENT;
- fraction improved/worsened versus CURRENT.

Interpretation is component attribution only. The best counterfactual is **not automatically the development candidate** because removing a risk control can mechanically improve endpoint returns while worsening path risk.

## Governance

No production semantic changes are authorized by this document. `positions.py` remains unchanged until a separately frozen candidate passes untouched validation.
