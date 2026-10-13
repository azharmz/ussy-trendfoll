# DIAG-003 — Exit Conversion / Give-back Contract

Status: **DEVELOPMENT-FROZEN DIAGNOSTIC CONTRACT / OBSERVATIONAL ONLY**

## Question

Under the current TrendFoll exit contract, how do historical entry-ready onsets convert post-entry price excursions into realized exit outcomes, and what does the day-45 holding boundary leave on the table or avoid?

This diagnostic is not a search for replacement exit rules.

## Corpus and event unit

- Universe authority: current R2 readiness universe.
- Deterministic sample: same SHA256-ranked 100-security method as DIAG-001/002.
- Stock history: governed R2 full-history contract via research_history.py.
- Pre-roll: 500 bars; canonical EMA basis: adj_close.
- Event: independent entry-ready False -> True onset, built on the full decision stream, then restricted to research_eligible.
- Execution anchor: next trading bar T+1 open.
- Entry ATR: ATR14 at T0, using the existing feature engine.
- This is an event-level historical simulation, not a portfolio return or a survivorship-bias-free backtest. It honors one-active-position-per-symbol by skipping signal onsets that occur before the prior simulated position exits.

## Frozen current exit logic

Apply the existing production priority on each bar from T+1 onward:
1. **Stop loss:** if low_raw <= entry_open - 2 * ATR14_T0, exit at the stop price.
2. **Maximum holding:** if trading-bar offset from T0 is at least 45, exit at that day's close.
3. **Trend exit:** if close_raw < ema20, exit at that day's close.

The priority order above matches positions.py: stop first, maximum holding second, EMA20 close exit third. The realistic entry is T+1 open; the T0 close is not an executable fill.

For a stop-hit bar, daily OHLC does not reveal whether its high occurred before or after the stop. Therefore MFE excludes the stop-hit bar; MAE includes the stop fill price, not a lower intraday print after the assumed fill. For trend/max-holding exits, excursion includes the exit-day high/low because exit is at the close.

## Frozen measurements

- Exit reason counts and executed/censored/overlapping-onset counts.
- Realized return from T+1 open; positive-return rate; median holding bars.
- Early failure: stop-loss or trend exit by the fifth future trading bar.
- MFE/MAE from executable T+1 open through the observable pre-exit path under the stop-bar convention above.
- Time-to-MFE in future trading bars; first close below EMA20 before or on the exit bar.
- Give-back: MFE return minus realized return; descriptive fraction of positive MFE given back where defined.
- Day-45 counterfactual: close return at the 45th future trading bar, whether or not the simulated trade exited earlier, clearly labeled as a no-exit holding counterfactual rather than a realizable current-strategy return.
- Post-day-45 continuation: among trades whose current-rule exit is max_holding, and only when 90 future bars are available, summarize the best high and close return through future bar 90, plus high/low excursions relative to the day-45 close.

Missing future bars are censored, never treated as zero return or loss. An event without T+1 open cannot be simulated. Onsets occurring before the previous same-symbol simulated trade exits are counted as blocked by the one-active-position rule.

## Interpretation discipline

- Descriptive statistics only; no causal claims, threshold mining, exit-rule tuning, or production changes.
- The current readiness universe is not historical point-in-time membership; survivorship bias remains.
- Historical events are clustered by symbol and may span different market eras.
- The day-45 counterfactual is not directly comparable to current-rule realized returns without accounting for risk exposure and post-exit path.

## Outputs

- diag003_exit_conversion_summary.json
- diag003_exit_conversion_events.csv

No production exit, stop, EMA, holding-period, alert, or entry rule changes are authorized by this diagnostic.
