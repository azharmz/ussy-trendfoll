# EDGE-ECON-001 — Frozen Economic Conversion Contract

Status: **FROZEN PRE-OUTCOME / NOT PRODUCTION**

Purpose: combine the already OOS-supported EDGE-CAND-001 entry representation with the already OOS-supported EXIT-CAND-003 risk/exit representation without parameter tuning.

## Frozen combined representation
- T0: current TrendFoll independent entry-ready onset.
- T+1: observe acceptance only; qualify iff T+1 close >= T0 prev_pivot_high.
- Entry: T+2 Open.
- Initial stop: entry - 2 * ATR14(T0).
- Chandelier: HH22 - 3 * WilderATR22.
- EMA20 close-loss retained.
- 45 sessions observation boundary.
- Chandelier ratchets upward only and day-t value can arm for t+1 only.
- Gap-through stop execution uses actual daily open exactly as EXIT-CAND-003.

No pivot margin, retest requirement, gap/momentum threshold, ATR grid, Chandelier grid, EMA grid, holding grid, target, or subgroup optimization.

## Evaluation corpus
Use the same untouched security ranks 101–200. This is an economic-conversion follow-up on a previously inspected holdout, **not a second untouched/OOS validation**. Results must be labelled accordingly.

## Comparators
On accepted T+1 events only:
A. CURRENT-ACCEPTED: hypothetical current exit stack entered T+2 Open, with initial stop re-anchored to T+2 entry using ATR14(T0).
B. EDGE+EXIT003: frozen EXIT-CAND-003 mechanics entered T+2 Open.

This isolates exit/risk conversion conditional on the frozen acceptance representation. It does not compare against rejected events.

## Costs
Report gross and deterministic round-trip cost sensitivities of 0, 5, 10 and 20 bps per side. Net return = gross return - 2*cost_bps/10000. This is a reporting sensitivity grid, not a selection rule.

## Required reporting
- event count / unique symbols
- median and mean gross/net return
- positive rate
- median hold, MFE, MAE
- exit reasons
- calendar-year median/positive rate for 10 bps/side
- 2022–2026 aggregate separately
- top-symbol share
- comparison versus CURRENT-ACCEPTED

## Interpretation
No production promotion gate is defined here. This run answers whether the combined representation survives realistic cost sensitivity and whether recent-period behavior remains problematic. Production remains unchanged.
