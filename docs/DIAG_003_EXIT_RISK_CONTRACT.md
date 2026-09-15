# DIAG-003 — Exit / Risk Conversion Contract

Status: **DEVELOPMENT-FROZEN DIAGNOSTIC CONTRACT / OBSERVATIONAL ONLY**

## Question

Given independent entry-ready onsets and executable T+1-open entries, how do the **existing** TrendFoll exit/risk rules convert post-entry price paths into realized outcomes?

This diagnostic does not search for a better stop, EMA, holding period, or profit target.

## Corpus

- Same current R2 readiness universe authority and deterministic SHA256-ranked 100-security sample as governed DIAG-001/002.
- R2 `backtest/ohlcv/{security_id}.parquet` full history.
- Frozen 500-bar pre-roll.
- Canonical historical EMA basis: `adj_close`.
- Evaluation ends at the R2 readiness snapshot date.
- Independent entry-ready onset detected on the full stream before restricting T0 to `research_eligible`.
- Entry fill: **next trading bar open (T+1 open)**.
- Only entries with sufficient forward history for the requested measurement are included in that measurement.

## Frozen current exit contract under audit

The diagnostic must reproduce the current `positions.py` semantics without modifying them:

1. ATR is frozen at T0 (`atr14_at_entry`).
2. Filled stop = `T+1 open - 2 * ATR14(T0)`.
3. Stop event when `low_raw <= stop_price`; assumed fill exactly at stop price.
4. Max holding = 45 trading days from the signal/entry-date convention used by production.
5. Trend exit when `close_raw < ema20`; fill at that day's close.
6. Exit priority on a bar: stop -> max_holding -> trend_exit.
7. One path is evaluated independently per onset; portfolio overlap/capital constraints are outside DIAG-003.

## Pre-registered measurements

### Current-rule realization

For every mature event:
- exit reason;
- exit day index from T+1 fill;
- realized return from T+1 open;
- MFE and MAE experienced before/current exit;
- maximum close reached before/current exit;
- give-back from maximum close to realized exit;
- whether the stop was touched;
- first close below EMA20;
- whether day-45 max holding was reached before another exit.

### Early failure

Descriptive only:
- stop touch within 1, 3, 5, and 10 trading bars after T+1 entry;
- negative close return at 1, 3, 5, and 10 bars where mature;
- first close below EMA20 within 1, 3, 5, and 10 bars.

These horizons are measurement checkpoints, not candidate exit thresholds.

### Time-to-opportunity / time-to-risk

For forward horizons through 45 trading bars:
- day of maximum high-based favorable excursion;
- day of minimum low-based adverse excursion;
- MFE and MAE through 5, 10, 20, and 45 bars where mature;
- fraction of eventual 45-bar MFE already observed by day 5/10/20.

### Day-45 counterfactual

For events with 45 forward bars, report return from T+1 open to the 45th forward close **ignoring earlier current-rule exits**. This is a diagnostic counterfactual only. It does not authorize removing stops or EMA20 exits.

Compare descriptively with current-rule realized return for the same 45-bar-mature subset.

## Output summaries

Report whole-corpus and 45-bar-mature summaries:
- N;
- exit-reason distribution;
- realized return median and positive rate;
- median days held;
- MFE/MAE and give-back medians;
- early-failure rates;
- time-to-MFE/time-to-MAE medians;
- checkpoint excursion summaries;
- day-45 counterfactual comparison.

No optimization, grid search, alternate ATR multiplier, alternate EMA period, alternate max-holding period, or best-exit selection is permitted in this run.

## Interpretation discipline

DIAG-003 may diagnose where current conversion appears to lose or protect value. It cannot itself authorize a strategy change. In particular:
- a better day-45 counterfactual does not prove stops/trend exits should be removed;
- a worse day-45 counterfactual does not prove 45 days is optimal;
- stop-hit frequency does not authorize changing 2 ATR;
- EMA20 timing does not authorize changing EMA period;
- time-to-MFE does not authorize a profit target.

Any alternative exit hypothesis must be separately evidence-backed, development-frozen, then untouched-validated with no post-validation tuning.

## Known boundaries

- Current R2 readiness universe is not historical PIT membership; survivorship bias remains.
- This is independent-event path analysis, not portfolio-level backtest attribution.
- OHLC daily bars cannot resolve intraday ordering when both favorable and adverse levels occur on the same bar; current production stop priority/fill assumptions are reproduced where applicable.
