# EXIT-CAND-001 — Risk-Preserving Ratchet + Trend Management

Status: **FROZEN PRE-OUTCOME DEVELOPMENT REPRESENTATION / NOT PRODUCTION-VALIDATED**

## Evidence boundary

EXIT-ISO-001 isolated the current fixed entry-anchored 2 ATR stop as the primary component associated with conversion loss, while removing EMA20 did not improve the aggregate outcome. Removing all risk controls increased adverse excursion materially. Therefore the next development representation must preserve explicit downside protection while allowing risk management to advance with a favorable path.

External methodology constrains the representation to a classic Chandelier-style volatility trail: a long stop is anchored to a recent/highest high and offset by ATR, with a monotonic ratchet so the effective stop never moves downward. Common Chandelier defaults are 22 periods and 3 ATR; these values are adopted here as an independently specified methodology representation and MUST NOT be tuned on the EXIT-ISO/DIAG-003 corpus.

## Primary candidate — EXIT-CAND-001

Long-only representation, matching the current TrendFoll long-entry domain.

### Entry

Unchanged from governed TrendFoll research:

- signal at T0;
- executable entry at T+1 Open.

### Initial hard-risk state

At entry, preserve the existing initial hard-risk protection:

`initial_stop = entry_price - 2 * ATR14(T0)`

This is not being claimed optimal. It is retained so the candidate tests management of an existing risk budget rather than simply deleting downside protection.

### Ratcheting volatility state

Starting after entry, calculate a classic Chandelier-style long trail using independently specified defaults:

- lookback = 22 daily bars;
- ATR period = 22 daily bars;
- multiplier = 3.0;
- raw trail = `HH22_t - 3 * ATR22_t`;
- effective trail = `max(previous_effective_stop, raw_trail)`.

The operative stop can therefore tighten but never loosen.

At all times:

`effective_stop_t = max(initial_stop, prior_effective_stop, HH22_t - 3*ATR22_t)`

No profit threshold, switch day, break-even trigger, momentum threshold, or post-hoc activation rule is permitted.

### Stop execution sequencing

To avoid same-bar look-ahead, the stop executable during trading day `t` is the stop frozen from information available through the prior completed daily bar. Today's high/ATR may update the stop only for the next trading day.

If `low_t <= operative_stop_t`, exit at the operative stop price. This preserves the existing conservative intraday stop-touch execution convention.

### Trend management

Retain the existing canonical EMA20 trend-state exit:

- if no stop was touched on the day and `close_raw_t < ema20_t`, exit at that day's close.

Stop has priority over the close-based EMA20 exit when both conditions occur on the same day.

### Observation/development horizon

For the first development evaluation only, retain the existing 45-forward-bar observation boundary so results remain directly comparable with DIAG-003 / EXIT-ISO-001. Day 45 is a **censoring/comparison boundary**, not evidence that 45 days is an optimal production exit horizon.

If still open at day 45, report the day-45 close as `observation_boundary` separately from stop/trend exits.

## Fallback candidate — EXIT-CAND-001B

Fallback is the same initial hard-risk + monotonic Chandelier risk mechanism **without EMA20 termination**, retaining the 45-bar observation boundary. It exists only to determine whether the independently specified ratchet can stand as the normal path-management mechanism if the primary candidate's EMA20 interaction proves problematic.

No other representation is authorized in this development cycle.

## Frozen metrics

Compare CURRENT, EXIT-CAND-001, and EXIT-CAND-001B on exactly the same mature events:

- median realized/observed return;
- positive fraction;
- Q25/Q75;
- median holding bars;
- exit-reason distribution;
- median MFE and MAE to exit/boundary;
- median give-back;
- stop-touch timing;
- paired event delta versus CURRENT;
- improved/worsened/unchanged fractions.

Risk preservation is mandatory in interpretation. A return improvement accompanied by uncontrolled deterioration in adverse excursion cannot by itself qualify the candidate.

## Prohibited development actions

- no 2.5/3.0/3.5 ATR comparison;
- no alternate Chandelier lookback comparison;
- no ATR-period comparison;
- no EMA-period comparison;
- no optimized activation/switch day;
- no profit-target grid;
- no entry-rule modification;
- no selection based on CAGR;
- no post-hoc subgroup threshold.

Any change to 22/3.0, execution sequencing, EMA20, initial 2 ATR protection, or the 45-bar development boundary after outcome inspection invalidates this candidate ID and requires a new independently justified hypothesis cycle.

## Development gate

Development results may classify the candidate as `PROMISING`, `MIXED`, or `REJECTED`. They cannot authorize production.

Only a frozen candidate that survives a subsequently designated untouched validation corpus with no post-validation tuning can be considered for production governance.
