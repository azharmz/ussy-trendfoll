# Full Signal Engine Audit — Evidence 05: Downstream Consumers

Status: **DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Scope

Static field-by-field trace of `r2_main.py`, `alert_state.py`, `database.py`, `candidate_lifecycle.py`, and `positions.py` on the audit branch.

## 1. Watchlist / alert contract

`r2_main.py` builds `candidates` from the latest market-date rows where `investability_status >= NEAR_PASS`.

`compute_alert_transitions()` receives the **full latest universe**, not the candidate subset. Monitoring is defined exclusively by Investability >= NEAR_PASS.

State mapping:

| Condition | State |
|---|---|
| Investability < NEAR_PASS / unknown | INVALIDATED |
| Investability PASS + Tradability PASS | ACTIONABLE |
| otherwise monitored | NEAR_TRIGGER |

Transition semantics:

- unseen monitored + actionable -> ACTIONABLE
- unseen monitored + non-actionable -> NEW_WATCH
- prior non-actionable -> actionable -> ACTIONABLE
- prior actionable -> non-actionable monitored -> LOST_TRADABILITY
- monitored transition into NEAR_TRIGGER -> NEAR_TRIGGER
- prior monitored absent from current full latest universe, or current Investability < NEAR_PASS -> INVALIDATED

Important: `hard_filter_status` is not used by alert-state logic.

Classification: **MATCH** with current watchlist/alert architecture.

## 2. Watchlist persistence

`upsert_watchlist()` receives only latest `candidates`, therefore only Investability >= NEAR_PASS rows are persisted for a date.

Persisted fields are:

- symbol/date/close_raw
- investability_status/tradability_status
- has_breakout/has_volume_confirmation/has_tight_structure
- regime_status/market_regime
- explanation_text

Conflict key is `(symbol,date)`. A candidate leaving monitoring is not deleted; it simply receives no new row. Historical state is therefore durable.

Classification: **MATCH**.

## 3. Candidate lifecycle

Lifecycle is derived from persistent watchlist history plus the full current latest universe. It does not insert a second production lifecycle table.

`first_watch_date` is therefore the first date on which the symbol was persisted with Investability >= NEAR_PASS, not the first date the symbol existed in R2 and not necessarily a signal-transition date.

Current monitored state again uses Investability >= NEAR_PASS. Current actionable uses the alert-state definition Investability PASS + Tradability PASS.

This directly supports the Sep-10 +61 disposition: first-seen lifecycle rows can arise from newly evaluated universe membership without a prior FAIL->NEAR/PASS transition.

Classification: **MATCH**.

## 4. Production position entry is a separate contract

Production position registration intentionally does **not** use the watchlist ACTIONABLE contract.

`register_new_positions()` requires:

1. `hard_filter_status == PASS`
2. `has_breakout == True`
3. `has_volume_confirmation == True`

It does **not** require `has_tight_structure` and therefore does not require `tradability_status == PASS`.

The code documents this as an explicit backtest-parity contract: `hard_filter_status` includes regime, while Investability intentionally excludes regime; tight structure was not a hard entry gate in the validated historical backtest.

Classification: **VALID USSY DEFINITION / INTENTIONAL CONTRACT SPLIT**, not evidence that `hard_filter_status` is accidentally substituted for Investability.

Consequence: **ACTIONABLE alert != production position-entry predicate**. A symbol can satisfy one contract without satisfying the other. This semantic split must remain explicit in documentation/UI and must not be silently collapsed during correction work.

## 5. T0 signal versus T+1 realistic execution

At T0 close, a newly registered production position stores:

- `entry_date = T0`
- `entry_price = close_raw(T0)` for historical/backtest parity
- `atr14_at_entry = ATR14(T0)`
- provisional stop = close(T0) - 2*ATR14(T0)

The code explicitly states that this T0 close is not a realistic human fill because the notification is available after the close.

On a later pipeline run, `fill_realistic_entry_prices()` searches feature history for the first market row strictly after `entry_date` and assigns `realistic_entry_price = open_raw` of that row. It then reanchors the active stop to:

`T+1 Open - 2 * ATR14(T0)`

Thus the forward/executable entry representation is **T+1 Open**, while `entry_price` remains the legacy/backtest trigger-price field.

Classification: **MATCH**, with a naming caveat: `entry_price` is trigger/backtest price, not realistic execution price.

## 6. Ordering in the daily pipeline

Authoritative order is:

1. full decision calculation through T0 close
2. alert transitions/watchlist/lifecycle
3. fill pending realistic T+1 entries from prior signals
4. align active stops
5. check exits
6. register new T0 signals
7. run EXIT-CAND-003 observational shadow

Therefore a new T0 signal cannot receive a fabricated T+1 fill during the same run. The realistic fill is deferred until a later row exists.

Classification: **MATCH**.

## 7. Findings

### FSE-011 — dual downstream contracts

Severity: **MEDIUM (semantic/governance risk)**

Classification: **VALID USSY DEFINITION / INTENTIONAL CONTRACT SPLIT**

Watchlist ACTIONABLE = Investability PASS + Tradability PASS.
Production entry = hard-filter PASS + breakout + volume confirmation.
These are intentionally different. Any frontend, alert, research, or audit that equates ACTIONABLE with production-entry eligibility will be wrong.

### FSE-012 — entry-price field semantics

Severity: **MEDIUM (interpretation risk)**

Classification: **VALID USSY DEFINITION WITH NAMING CAVEAT**

`entry_price` is T0 close/backtest trigger price. `realistic_entry_price` is the executable T+1 Open representation. Performance analysis intended to represent executable trading must use the latter once available.

## Checklist disposition

Static evidence closes A11, A12, A13, A14, A15, and A16 at the code-contract level. Empirical database consistency remains a separate evidence task; these checkmarks do not claim that every persisted historical row is clean.
