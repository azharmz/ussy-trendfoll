# EXIT-CAND-002 — Executable Ratcheting Risk Representation

Status: **FROZEN PRE-OUTCOME DEVELOPMENT CONTRACT / NOT VALIDATED / NOT PRODUCTION**

EXIT-CAND-002 replaces the invalid EXIT-CAND-001 representation. It is a new candidate ID; no EXIT-CAND-001 candidate outcomes may be used as evidence for this contract.

## Research question

Can the already-frozen Chandelier methodology provide a risk-preserving ratchet without introducing infeasible sell-stop fills, while changing only the fixed-stop state evolution and retaining the current EMA20 trend exit?

## Frozen parameters

No parameter search is authorized.

- Entry: T+1 Open, unchanged.
- Initial hard-risk stop: `entry_price - 2 * ATR14(T0)`, unchanged from CURRENT.
- Chandelier methodology: 22-bar highest high minus `3 * ATR22` (Wilder ATR), retained from the independently frozen methodology representation.
- EMA20 close-loss trend exit: retained.
- Observation boundary: 45 trading days; this is an evaluation boundary, not evidence that day 45 is an optimal exit.

## Executable activation rule

The initial hard-risk stop is the only operative stop at entry.

For each completed trading day `t`, compute the Chandelier candidate using information available through the close of `t`. It may become the operative sell-stop for day `t+1` only if all of the following are true at the close of `t`:

1. `chandelier_t` is finite;
2. `chandelier_t < close_raw_t` — the proposed long sell-stop is below the known market close when it is armed;
3. `chandelier_t > operative_stop_t` — the stop ratchets upward only.

Then:

`operative_stop_{t+1} = chandelier_t`

otherwise:

`operative_stop_{t+1} = operative_stop_t`.

This rule has no arbitrary switch day. The initial stop naturally remains active until a trailing level becomes both higher and executable.

## Daily execution sequence

For each day `t >= T+1`:

1. Enter T+1 at Open when applicable.
2. The stop active during day `t` was frozen no later than the prior close (except the initial stop, which is defined at T+1 Open from T0 ATR).
3. If `low_raw_t <= operative_stop_t`, exit at `operative_stop_t`.
4. Else, if day 45 is reached, record `observation_boundary` at that day's close.
5. Else, if `close_raw_t < EMA20_t`, exit at that close as `trend_exit`.
6. Only after surviving the day, use day-`t` information to arm/ratchet the stop for `t+1` under the activation rule above.

## Feasibility invariants

The development runner MUST fail closed if any candidate event violates:

- a risk-stop exit price is above that day's high;
- a risk-stop exit price is below that day's low beyond ordinary exact-stop semantics (the stop must lie within `[low, high]` on a touched day);
- the operative stop decreases after entry;
- a Chandelier level is armed when it is not strictly below the prior close;
- any day-t trailing value is used to determine a day-t stop touch.

## Comparator and development decision

Comparator is CURRENT, unchanged.

EXIT-CAND-002 advances to a separately frozen untouched-validation protocol only if, on the governed development corpus:

1. median realized return is strictly greater than CURRENT;
2. positive-return fraction is not lower than CURRENT;
3. median MAE-to-exit is not worse than CURRENT (candidate median MAE must be greater/equal, i.e. less negative);
4. all feasibility invariants pass;
5. CURRENT reproduces the established EXIT-ISO-001 mature-45 baseline within numerical tolerance.

These are Pareto-style criteria; no tolerance/grid is introduced to rescue the candidate.

## Prohibited

No ATR-period grid, multiplier grid, EMA grid, switch-day grid, profit target, momentum/gap filter, holding-day optimization, or post-outcome representation change is allowed. Failure means EXIT-CAND-002 fails; it is not patched under the same candidate ID.
