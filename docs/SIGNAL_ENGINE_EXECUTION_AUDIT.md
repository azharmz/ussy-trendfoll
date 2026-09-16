# Signal Engine Execution Audit

Status: **DIAGNOSTIC / NO PRODUCTION LOGIC CHANGED**

Audit date: 2026-09-16

Scope: actual R2 production path `R2 READY -> FEATURES -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST/ALERT` on branch `research/exit-development-hypotheses`.

Classification vocabulary: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD/UNUSED`.

## Actual execution map

`r2_main.py` -> `load_ready_dataset()` -> `build_feature_store_from_r2()` -> legacy feature builder with stock ingestion replaced by R2 READY -> `apply_shared_ema_terminal()` -> `compute_hard_filter()` -> `compute_decision_layer()` -> latest common market date -> candidate admission `investability_status >= NEAR_PASS` -> alert/watchlist persistence -> production position/exit path -> CAND-003 observational shadow.

Benchmark/regime inputs (SPY, QQQ, VIX, sector ETFs) are still downloaded through `feature_engine`; stock OHLCV comes from R2 READY.

## Findings

| Area | Actual implementation | Classification | Audit conclusion |
|---|---|---|---|
| R2 stock source | stock-universe download replaced by R2 READY | MATCH | Production stock features use governed READY. |
| Shared terminal EMA basis | terminal EMA20/50/150/200 and stack replaced with governed `adj_close` state | MATCH | Latest decision row uses canonical adjusted-price EMA state with lineage/equivalence checks. |
| Historical EMA rows | legacy feature builder computes EMA from `close_raw` | MISMATCH | Only terminal rows are migrated; retrospective rows retain raw-close EMA facts. |
| EMA stack | `adj_close > EMA20 > EMA50 > EMA150 > EMA200` at terminal | VALID USSY DEFINITION | Frozen USSY bullish alignment, not literal Minervini Trend Template. |
| Minervini label | hard-filter docstring calls trend criterion Minervini Trend Template + Weinstein Stage | MISMATCH | Implementation lacks explicit rising 200-day average and 52-week high/low Trend Template conditions. |
| Weekly source | `close_raw`, `W-FRI`, `.last()` | VALID USSY DEFINITION | Deterministic weekly proxy. |
| 30-week MA | rolling 30 weekly closes | MATCH | Matches frozen USSY definition. |
| MA30W slope | strict 3-observation rise/fall, otherwise Flat | APPROXIMATION | Short slope proxy rather than full Stage Analysis context. |
| Stage1-4 | price vs MA30W plus short slope | APPROXIMATION | Stage2/4 directional proxies; Stage1/3 especially lack prior-cycle/base/distribution context. |
| Weekly temporal merge | Friday-labelled weekly rows merged backward to daily rows | MATCH | Mon-Thu cannot see a future Friday label; Friday uses contemporaneous Friday close. Weekly state updates on Friday only. |
| RS stock return | 63-session `close_adj` return | MATCH | Adjusted-price return is appropriate for relative return. |
| RS benchmark | stock 63-session return minus SPY 63-session return | VALID USSY DEFINITION | Excess 63-day return vs SPY, not an IBD RS Rating. |
| RS threshold | PASS >=0; NEAR_PASS >=-0.02 | VALID USSY DEFINITION | Frozen USSY threshold. |
| Liquidity | avg raw share volume 50d; PASS >=300k, NEAR >=240k | VALID USSY DEFINITION | Share-volume gate, not dollar-volume liquidity. |
| Price floor | raw close PASS >=$10, NEAR >=$8 | VALID USSY DEFINITION | Explicit USSY gate. |
| Market regime | SPY raw close vs SMA50/SMA200 | VALID USSY DEFINITION | Bullish/Neutral/Bearish portfolio-regime proxy. |
| Hard filter | trend + liquidity + RS + price + regime, non-compensatory | VALID USSY DEFINITION | Distinct from Investability by design; production entry uses this five-component aggregate. |
| Investability | trend + liquidity + RS + price, excludes regime | MATCH | Structural candidate admission layer; candidate threshold is >= NEAR_PASS. |
| Breakout pivot | 60-session structure high, shifted one day before T0 comparison | MATCH | T0 close compares with prior pivot state, excluding T0 from its own breakout threshold. |
| Breakout execution | T0 signal; realistic fill assigned from next trading-day open | MATCH | Consistent with T0 signal / T+1 Open execution constraint. |
| Volume confirmation | rolling 50-session current-volume percentile >=80 | MATCH | Frozen formula/threshold; Sep14 systemic anomaly was upstream partial-bar contamination and is closed. |
| VCP tightness | `100 - ATR14 percentile over 63d` | APPROXIMATION | Source itself describes a proxy; not canonical VCP morphology. |
| Tradability PASS | breakout + volume + tightness | VALID USSY DEFINITION | Status tier only; tightness is not production entry gate. |
| Tradability NEAR_PASS | breakout without all PASS subconditions | VALID USSY DEFINITION | Weak-candidate tier, not confirmed entry. |
| Production entry gate | `hard_filter_status == PASS` + breakout + volume | MATCH | Verified directly in `positions.register_new_positions`; tightness is not required. |
| T+1 realistic entry | pending T0 position later filled with first subsequent `open_raw` | MATCH | `fill_realistic_entry_prices` implements next available trading-day open. |
| `pct_off_52w_high` | computed but absent from current decision gates | DEAD/UNUSED | Context feature only. |
| `rs_sector` / RS persistence | computed but absent from current decision gates | DEAD/UNUSED | Context/diagnostic feature only. |
| VIX volatility regime | computed but absent from current decision gates | DEAD/UNUSED | Does not currently gate candidates. |

## Highest-priority audit consequence — historical EMA basis

Current-day Investability uses canonical adjusted EMA facts, while retrospective `decided` rows use legacy raw-close EMA calculations. Historical lifecycle/validation studies therefore must not assume a uniform adjusted-EMA contract. This is a semantic consistency defect, not evidence of look-ahead. Remediation is not authorized by this audit; because it can alter historical classifications it requires development -> untouched validation before production change.

## Stage-analysis conclusion

The Stage1-4 implementation is a deterministic USSY proxy around weekly close, SMA30W, and a three-observation slope. It should be described as an approximation rather than faithful Weinstein Stage Analysis.

## Temporal/look-ahead conclusion

No direct T0-close-as-executable-entry defect was found. Breakout shifts pivot state by one session, weekly merge does not expose future Friday values to Mon-Thu, and realistic entry is filled from the first subsequent trading-day open.

## Sep10 first-admission attribution

A read-only reconstruction was run for all 61 symbols whose first persisted watchlist date is 2026-09-10, comparing frozen current component logic on 2026-09-04 versus 2026-09-10. Audit run `35068878141` completed successfully with 61/61 reconstructed rows.

Target Sep10 reconstruction: 57 PASS, 4 NEAR_PASS. On Sep04 under the same reconstructed logic: 39 were already PASS and 22 were FAIL. Overall transitions were therefore:

- PASS -> PASS: 39
- FAIL -> PASS: 20
- FAIL -> NEAR_PASS: 2

Component attribution is sharply concentrated in Trend:

- trend: 22 FAIL -> PASS; 39 PASS -> PASS
- liquidity: 1 NEAR_PASS -> PASS; otherwise unchanged
- price: 1 NEAR_PASS -> PASS; otherwise unchanged
- RS: unchanged for all 61

The 22 Sep04 FAIL names all improved through Trend. This supports a real trend-component transition for that subset. However, **39/61 were already PASS on Sep04 under the same current reconstruction yet were not persisted until Sep10**. Therefore the +61 first-admission jump cannot be explained as a pure market-state transition. A historical execution/input/lineage discontinuity remains to be identified for those 39 names.

Caveat: Sep04/Sep10 reconstruction intentionally uses the historical legacy `close_raw` EMA path because canonical shared `adj_close` EMA replacement applies only to the terminal row. This reproduces current retrospective semantics but does not prove the exact code/data lineage that originally produced the persisted Sep04 watchlist.

## Next diagnostic

Trace why the 39 reconstructed `PASS -> PASS` symbols were absent from the persisted Sep04 watchlist: distinguish historical universe coverage/backfill boundary, R2 migration timing, code/config lineage, and persistence/run coverage. Do not tune thresholds or rewrite historical watchlist evidence.
