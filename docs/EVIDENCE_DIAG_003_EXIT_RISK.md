# Evidence — DIAG-003 Exit / Risk Conversion

Status: **EVIDENCE-LOCKED / OBSERVATIONAL / NO PRODUCTION CHANGE AUTHORIZED**

## Provenance

- Workflow: `DIAG-003 Exit Risk Conversion`
- Run: `34925589287` / run #1
- Job: `104242837631`
- Head SHA: `4302cf94490092e1bd32d0adb3690e86b625f058`
- Conclusion: **SUCCESS**
- Repository tests: **12/12 PASS**
- Artifact: `diag003-exit-risk-1`
- Artifact ID: `10379612069`
- Artifact ZIP SHA256: `172218adf26189ec54739e6c0379bef192857ceb0b6ba515ec8fdbe9be06be33`

The diagnostic contract was frozen in `docs/DIAG_003_EXIT_RISK_CONTRACT.md` before results were observed.

## Governed corpus

- R2 readiness snapshot: `2026-08-28`.
- Deterministic 100-security sample, same research-history framework as DIAG-001/002.
- Full R2 stock history with frozen 500-bar pre-roll.
- Canonical historical EMA basis: `adj_close`.
- Feature store: 519,288 rows.
- Eligible independent entry-ready onsets: 1,545.
- Usable exit paths: 1,545.
- 45-bar-mature paths: 1,524.
- Entry anchor: executable T+1 Open.

## Current-rule realization

Across all 1,545 paths:

- stop loss: 848 exits (54.9%);
- EMA20 trend exit: 353 (22.8%);
- 45-day max holding: 337 (21.8%);
- censored: 7 (0.5%);
- median realized return: **-3.51%**;
- positive realized-return rate: **32.70%**;
- median holding time: **16 trading bars**;
- median MFE experienced through exit: **+5.48%**;
- median MAE experienced through exit: **-4.76%**;
- median give-back from maximum close to realized exit: **-6.19%**.

The 1,524 fully 45-bar-mature paths give essentially the same current-rule result: median realized return **-3.46%**, positive rate **33.01%**, and median holding time 16 bars.

## Early failure

Stop-touch rate from the T+1-open anchored 2 ATR stop:

- within 1 bar: **1.88%**;
- within 3 bars: **11.65%**;
- within 5 bars: **20.27%**;
- within 10 bars: **35.04%**.

The fraction whose checkpoint close is below entry remains near one half: 48.16% at day 1, 46.86% at day 3, 48.25% at day 5, and 48.48% at day 10.

EMA20-loss incidence is much lower early: 0.26% by day 1, 2.07% by day 3, 4.34% by day 5, and 12.85% by day 10.

Interpretation: the corpus does **not** look like a simple immediate post-entry collapse. Stop exposure accumulates materially over the first 10 bars while early EMA20-loss is relatively uncommon.

## Opportunity and risk continue developing

Median high-based MFE / low-based MAE by checkpoint:

| Horizon | Median MFE | Median MAE |
|---|---:|---:|
| 5 bars | +2.57% | -2.50% |
| 10 bars | +3.69% | -3.58% |
| 20 bars | +5.63% | -5.25% |
| 45 bars | +9.09% | -7.86% |

Among 45-bar-mature paths:

- median time to 45-bar MFE: **27 bars**;
- median time to 45-bar MAE: **21 bars**;
- median fraction of eventual 45-bar MFE already observed by day 5: **32.4%**;
- by day 10: **49.3%**;
- by day 20: **80.7%**.

This supports a path-development interpretation: substantial favorable excursion often arrives after the median current-rule holding period of 16 bars. It does not by itself establish that holding longer is optimal, because adverse excursion also expands with horizon.

## Frozen day-45 counterfactual

For the exact same 1,524 45-bar-mature entries:

- current-rule median realized return: **-3.46%**;
- current-rule positive rate: **33.01%**;
- day-45 close return when earlier current-rule exits are ignored: **+1.70% median**;
- day-45 positive rate: **56.43%**.

This is a large descriptive divergence and establishes that **exit/risk conversion is a material root-cause candidate in this corpus**.

It does **not** establish that the correct strategy is to hold every trade for 45 days. The counterfactual deliberately ignores path risk and earlier exits, while the same corpus has median MAE45 of -7.86%. Nor does it identify which current rule (2 ATR stop, EMA20 exit, 45-day maximum, or their interaction) should change.

## Root-cause verdict

`RC-004 — Exit / risk conversion`

Verdict: **SUPPORTED AS A MATERIAL ROOT CAUSE / MECHANISM NOT YET ISOLATED**.

What is supported:

1. The current exit stack converts this event corpus into materially weaker realized outcomes than the underlying 45-bar endpoint distribution.
2. Stop-loss is the dominant realized exit reason.
3. Favorable excursion commonly continues to develop beyond the median current holding time.
4. The earlier valid-history finding that T+1-to-T+5 median return does not broadly decay is consistent with this result.

What is not supported/authorized:

- removing the stop;
- changing the 2 ATR multiplier;
- replacing or changing EMA20;
- changing the 45-day maximum;
- adding a profit target;
- treating the 45-day counterfactual as a production strategy;
- claiming portfolio-level profitability.

## Required next governance step

DIAG-003 closes diagnosis of whether exit/risk conversion matters, but not which mechanism or replacement is correct.

Before any exit-rule development, create a separate evidence-backed development hypothesis set. Candidate hypotheses must be justified independently (methodology/literature and/or pre-registered decomposition), frozen before outcome comparison, and then subjected to untouched validation. No parameter grid search or post-validation tuning is authorized from this evidence.

## Boundaries

- Universe membership is current R2 readiness, not historical point-in-time membership; survivorship bias remains.
- Independent event paths are not a portfolio/capital simulation.
- Daily OHLC cannot identify intraday ordering; production stop priority/fill assumptions are reproduced.
- The diagnostic evaluates the current exit stack as implemented; it does not establish causal contribution of each exit component separately.
