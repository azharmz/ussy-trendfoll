# DIAG-001 — Signal-to-Outcome Funnel

Status: **DIAGNOSTIC CONTRACT / OBSERVATIONAL / NO PRODUCTION TUNING**

Linked problems: `PROB-008`, `PROB-009`, `PROB-010`, `PROB-011`.

## Question

Where does TrendFoll lose or retain quality along the executable path?

`T-1 -> T0 signal -> T+1 open -> T+1 close -> T+2 -> T+3 -> T+5 -> MFE/MAE -> exit`

This diagnostic must distinguish:
1. pre-signal extension,
2. signal quality at T0,
3. execution decay between T0 and executable T+1 open,
4. early post-entry follow-through/fade,
5. later position/exit outcome.

## Unit of observation

Primary unit: **independent entry-ready onset**, not every repeated breakout bar.

Entry-ready condition follows the audited production/backtest entry gate:
- `hard_filter_status == PASS`
- `has_breakout == True`
- `has_volume_confirmation == True`

An event starts when the condition changes `False -> True` for a symbol. Repeated consecutive entry-ready days are the same episode for the primary analysis. Re-entry after leaving the condition may form a new episode.

This prevents repeated breakout-state bars from dominating the sample.

## Event-level fields

### Identity / T0 state
- symbol
- T0 date
- hard-filter / Investability / Tradability status
- trend, liquidity, RS, price, regime status
- market regime
- breakout volume percentile / volume confirmation
- VCP tightness / tight-structure flag
- previous pivot high
- ATR14 at T0

### T-1 -> T0: pre-entry extension
- T-1 close
- T0 close
- return T-1 close -> T0 close
- T0 close extension above previous pivot, raw %
- T0 close extension above previous pivot, ATR units

Purpose: test whether executable entries deteriorate when the signal day is already extended. This is diagnosis, not a new cutoff search.

### T0 -> T+1: execution bridge
- T+1 open
- gap T0 close -> T+1 open
- T+1 close
- return T+1 open -> T+1 close
- return T0 close -> T+1 close

The executable anchor is T+1 open. T0 close remains the trigger/reference price and must not be reported as an executable fill.

### T+2 / T+3 / T+5 path
From T+1 executable open:
- close return at T+2
- close return at T+3
- close return at T+5
- high-based MFE through each horizon where available
- low-based MAE through each horizon where available

High/low excursion metrics must be explicitly labelled intraday-bar extrema; close-path returns remain separate.

### Position / exit linkage
Where a matching forward paper position exists, attach:
- stored trigger entry price
- realistic entry price
- stop price / ATR at entry
- exit date
- exit price
- exit reason
- realized return from realistic entry where available
- stored/reconstructed MFE/MAE fields where comparable.

Supabase position history is evidence of the production forward tracker, not a substitute for reconstructing the complete historical signal universe.

## Primary funnel

Report counts and attrition through:

`eligible decision rows`
`-> hard-filter PASS`
`-> breakout onset`
`-> volume-confirmed entry-ready onset`
`-> T+1 executable bar available`
`-> T+3 mature`
`-> T+5 mature`
`-> linked forward position (where applicable)`
`-> exit/outcome available (where applicable)`

Missing forward bars must be reported, never silently treated as losses or zero returns.

## Descriptive segmentation

Initial analysis may describe outcomes by:
- T-1 -> T0 momentum/extension,
- T0 -> T+1 opening gap,
- breakout extension above pivot in ATR,
- volume confirmation strength,
- tightness flag/metric,
- regime,
- Investability components.

Quantiles may be used for **descriptive decomposition only**. They are not production thresholds and must not be selected for best return. Any candidate rule arising from the diagnostic requires a separate development contract and later untouched validation.

## Outputs

Machine-readable:
- `signal_path_events.csv` — one row per independent primary event.
- `signal_path_summary.json` — funnel counts, coverage and descriptive aggregate metrics.

Human-readable run summary should state:
- event count,
- T+1/T+3/T+5 maturity coverage,
- linked-position coverage,
- median T-1->T0 move,
- median T0->T+1 gap,
- median executable-entry returns at T+1/T+3/T+5,
- early MFE/MAE,
- no strategy-change verdict unless a separate governed research cycle exists.

## Non-goals

DIAG-001 does **not**:
- change Investability or Tradability,
- change entry, stop, EMA20 exit or max holding,
- redefine production `NEAR_TRIGGER`,
- tune a T-1->T0 momentum threshold,
- tune a T0->T+1 gap threshold,
- prove profitability from the NEAR_TRIGGER <=0.60 ATR research.

## Root-cause handoff

After evidence is generated, classify findings into a Root Cause Map. Only root causes with adequate evidence may become Roadmap items. Roadmap items then receive explicit Development Plan tasks, acceptance criteria and validation requirements.
