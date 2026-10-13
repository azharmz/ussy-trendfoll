# DIAG-003 — Exit Conversion / Give-back Evidence

Status: **COMPLETED / OBSERVATIONAL ONLY / NO PRODUCTION CHANGE**

- Workflow: [DIAG-003 Run #1](https://github.com/azharmz/ussy-trendfoll/actions/runs/38392513103)
- Commit: `7a875c3867f25f7c2f133f10598e01cc71f80181`
- Contract: `docs/DIAG_003_EXIT_CONVERSION_CONTRACT.md`
- Snapshot: `2026-08-28`
- Deterministic sample: 100 current R2 readiness securities; 500-bar pre-roll; canonical EMA basis `adj_close`; stock history `history/ohlcv/{security_id}.parquet`.

## Coverage and position eligibility

- 100 histories loaded; 87 securities have eligible history.
- 470,890 eligible decision rows; 1,610 full-history onsets; 1,545 eligible onsets.
- 897 events simulated to a realized exit; 642 subsequent same-symbol onsets were blocked because a simulated position was still active; 6 were censored at the end of available history.
- No event lacked a T+1 bar or had invalid entry/ATR.
- The 897 simulated trades are event-level sequential trades under a one-active-position-per-symbol rule, not a capital-weighted portfolio backtest. Repeated events remain clustered by security.

## Current exit contract results

Frozen exit priority: T+1 open entry; stop at entry open minus 2 × T0 ATR14 when daily low touches it; day-45 close exit; otherwise close below EMA20 exit.

| Metric | Result |
|---|---:|
| Stop-loss exits | 485 / 897 (54.1%) |
| EMA20 trend exits | 203 / 897 (22.6%) |
| Day-45 exits | 209 / 897 (23.3%) |
| Median realized return from T+1 open | -3.58% |
| Positive realized returns | 33.9% |
| Median holding duration | 16 trading bars from T0 |
| Stop/trend exits by future bar 5 | 192 / 897 (21.4%) |
| Median MFE before/at exit under stop-bar convention | +5.77% |
| Median MAE before/at exit under stop-bar convention | -4.20% |
| Median time-to-MFE | 8 future bars |
| Median MFE-to-exit give-back | 7.64 percentage points |

Exit-reason summaries are selection-conditioned:
- Stop-loss exits (N=485): median realized return -5.00%; 180 (37.1% of stop exits) occur by future bar 5.
- EMA20 trend exits (N=203): median realized return +0.58%; median holding duration 20 bars.
- Day-45 exits (N=209): median realized return +8.61%; 92.8% have positive return by construction of surviving the stop/trend exits to the maximum-holding boundary.

These are descriptive results under the frozen rules and sampled corpus. They do not identify a superior replacement stop, EMA exit, or holding period.

## Day-45 counterfactual

- 887 events have a mature 45th future bar; the no-exit T+1-open-to-day-45-close median is +2.27%.
- For the 209 trades that actually reach the current-rule day-45 exit, all have a mature day-90 path in this sample. Median day-90 close return from T+1 open is +11.27%; median best high through day 90 is +19.76%; median best-high gain relative to day-45 close is +9.29%; median low excursion relative to day-45 close is -7.38%.

This survivor cohort is selected: those trades avoided both stop-loss and EMA20 exit until day 45. Post-day-45 continuation demonstrates opportunity and drawdown coexist; it does not prove that removing the cap improves risk-adjusted results. The all-event day-45 figure is explicitly a no-exit holding counterfactual, including trades that the actual rules exited earlier.

## Limitations

1. Current readiness universe is not historical point-in-time membership; survivorship bias remains.
2. The sample spans multiple market eras and is clustered within securities.
3. Daily OHLC cannot determine whether the high occurred before or after a same-day stop. MFE excludes the stop-hit bar; MAE is capped at the assumed stop fill.
4. Overlap suppression follows one-active-position-per-symbol semantics, but this is still not a capital/cash/portfolio simulation.
5. No transaction costs, slippage, liquidity impact, or market-on-close execution modeling is included.
6. These results are not a production validation and do not authorize changes to stop, EMA20, max holding, entry, regime, or alert rules.

## Decision and next step

DIAG-003 pipeline and repository tests **PASS**. The current-rule sample shows frequent stop exits, a low positive-return fraction among simulated trades, and meaningful MFE-to-exit give-back; day-45 survivors also show both post-cap continuation and drawdown. This supports keeping exit conversion as an open research question, not immediately changing exits.

Next: audit the known position-history duplicate/identity issue (PROB-017) before using linked forward-position outcomes as canonical. Keep that engineering audit separate from this full-history event reconstruction. Any exit-rule hypothesis must be separately frozen and validated on untouched data.
