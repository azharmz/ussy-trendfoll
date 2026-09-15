# EXIT-CAND-003 — Executable Ratcheting Risk With Gap-Through Handling

Status: **FROZEN PRE-OUTCOME DEVELOPMENT CONTRACT / NOT VALIDATED / NOT PRODUCTION**

EXIT-CAND-003 supersedes invalid EXIT-CAND-002. No outcome from invalid predecessors may be used as evidence for this candidate.

## Frozen mechanism
- Entry: T+1 Open, unchanged.
- Initial hard-risk stop: `entry_price - 2 * ATR14(T0)`.
- Chandelier: `HH22 - 3 * WilderATR22`.
- EMA20 close-loss trend exit retained.
- 45 trading days is an observation boundary for the candidate.

## Trailing activation
The initial stop is operative at entry. After a day survives both stop and EMA20 exit, the day-t Chandelier may be armed for t+1 only when finite, strictly below day-t close, and strictly above the current operative stop. The operative stop never decreases. No same-day Chandelier value may affect that day's stop execution.

## Frozen daily-OHLC long sell-stop execution
For the stop already operative at the start of day t:

1. If `open_raw_t <= operative_stop_t`, the market has opened at/below the stop: exit at `open_raw_t` and classify `risk_stop_gap` (CURRENT equivalent remains its governed current semantics and is a comparator only).
2. Else if `low_raw_t <= operative_stop_t`, exit at exactly `operative_stop_t` and classify `risk_stop_touch`.
3. Else no stop exit occurs that day.

This deliberately makes no intraday path assumption beyond what daily OHLC supports. A gap-through stop never receives a better fill than the observed opening price.

If no stop exit occurs: day 45 is recorded as `observation_boundary`; otherwise EMA20 close-loss exits at same-day close. Only after surviving the day may the Chandelier ratchet be armed for t+1.

## Feasibility invariants
Fail closed if:
- a `risk_stop_gap` fill differs from that day's open;
- a `risk_stop_touch` fill is outside that day's `[low, high]`;
- a non-gap stop fill exceeds the operative stop;
- the operative stop decreases;
- a Chandelier is armed unless finite, below the completed day's close, and above the prior operative stop;
- a day-t Chandelier affects day-t stop execution.

## Development comparator and gate
CURRENT is unchanged and must reproduce EXIT-ISO-001 mature-45 baseline exactly within numerical tolerance.

EXIT-CAND-003 advances to separately frozen untouched validation only if all are true:
- median realized return > CURRENT;
- positive-return fraction >= CURRENT;
- median MAE-to-exit >= CURRENT (less negative or equal);
- all feasibility invariants PASS;
- CURRENT baseline reproduction PASS.

No parameter tolerance/grid may rescue a failure.

## Prohibited
No ATR/lookback/multiplier/EMA/switch-day/holding-day grid; no profit target; no entry change; no momentum/gap subgroup rule; no post-outcome representation patch under this candidate ID.
