# Signal Engine Execution Audit

Status: **DIAGNOSTIC / NO PRODUCTION LOGIC CHANGED**

Audit date: 2026-09-16

Scope: actual R2 production path `R2 READY -> FEATURES -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST/ALERT` on branch `research/exit-development-hypotheses`.

Classification vocabulary: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD/UNUSED`.

## Actual execution map

`r2_main.py`
-> `load_ready_dataset()`
-> `build_feature_store_from_r2()`
-> `feature_engine.build_feature_store()` with stock-universe ingestion replaced by R2 READY
-> `apply_shared_ema_terminal()`
-> `compute_hard_filter()`
-> `compute_decision_layer()`
-> latest common market date
-> candidate admission `investability_status >= NEAR_PASS`
-> alert transition / watchlist persistence
-> production position/exit path
-> CAND-003 observational shadow.

Important boundary: benchmark/regime inputs (SPY, QQQ, VIX, sector ETFs) are still downloaded through `feature_engine`; stock OHLCV comes from R2 READY.

## Findings

| Area | Actual implementation | Classification | Audit conclusion |
|---|---|---|---|
| R2 stock source | `r2_feature_engine` replaces stock-universe download with R2 READY | MATCH | Production stock features are sourced from governed READY rather than the legacy static universe. |
| Shared terminal EMA basis | `r2_shared_ema` replaces terminal EMA20/50/150/200 and stack with governed `adj_close` state | MATCH | Latest decision row uses canonical adjusted-price EMA state and verifies READY lineage/equivalence. |
| Historical EMA rows | `feature_engine.compute_ema_features()` computes historical EMA from `close_raw` | MISMATCH | Only terminal rows are migrated. Historical `decided` rows retain raw-close EMA facts. This matters to any retrospective lifecycle/validation logic using historical trend status. Do not describe the entire feature history as canonical adj-close EMA. |
| EMA stack definition | terminal: `adj_close > EMA20 > EMA50 > EMA150 > EMA200` | VALID USSY DEFINITION | Valid frozen USSY bullish alignment. It is not a literal Minervini Trend Template implementation. |
| Minervini label in hard-filter docstring | comments call trend criterion `Minervini Trend Template + Weinstein Stage` | MISMATCH | Implementation lacks canonical Trend Template elements such as explicit rising 200-day average and 52-week high/low conditions. Label overstates fidelity; logic itself is frozen USSY logic. |
| Weekly source | `close_raw`, resampled `W-FRI`, `.last()` | VALID USSY DEFINITION | Deterministic weekly proxy derived from daily bars. |
| 30-week MA | simple rolling 30 weekly closes | MATCH | Matches frozen USSY definition. |
| MA30W slope | strictly increasing/decreasing over only three MA observations; else Flat | APPROXIMATION | Deterministic short slope proxy, not a full Stage Analysis trend/context model. |
| Stage2 | price > MA30W and slope Up | APPROXIMATION | Reasonable Stage2 proxy, but no broader base/cycle context. |
| Stage4 | price < MA30W and slope Down | APPROXIMATION | Reasonable Stage4 proxy. |
| Stage3 | price > MA30W with Flat/Down slope | APPROXIMATION | Simplified distribution-stage proxy. |
| Stage1 | all remaining valid combinations | APPROXIMATION | Residual bucket can mix basing/recovery states; lacks prior-cycle/context evidence. |
| Weekly temporal merge | weekly stage is merged backward to daily rows | BUG | `resample("W-FRI").last()` labels an in-progress week at Friday even when source data only exists through Mon-Thu; `merge_asof(..., direction="backward")` prevents Mon-Thu from seeing that future Friday label. Friday rows can use that week's Friday close, which is contemporaneous at daily close. No direct future-row leak was found in this merge, but the weekly feature changes only on Friday. |
| RS stock return | 63-session `close_adj` return | MATCH | Adjusted-price return is appropriate for relative return measurement. |
| RS benchmark | stock 63-session return minus SPY 63-session return | VALID USSY DEFINITION | This is excess 63-day return vs SPY, not an IBD RS Rating. |
| RS threshold | PASS >= 0; NEAR_PASS >= -0.02 | VALID USSY DEFINITION | Explicit frozen USSY threshold; no evidence in code that it is a canonical external threshold. |
| Liquidity | avg raw volume 50d; PASS >=300k, NEAR >=240k | VALID USSY DEFINITION | Share-volume gate only; it is not dollar-volume liquidity. |
| Price floor | raw close PASS >=$10, NEAR >=$8 | VALID USSY DEFINITION | Explicit USSY gate. |
| Market regime feature | SPY raw close vs SMA50/SMA200 | VALID USSY DEFINITION | Bullish/Neutral/Bearish proxy. |
| Regime in `hard_filter_status` | included as fifth non-compensatory hard-filter component | MISMATCH | `decision_layer` states regime is a separate portfolio gate and Investability excludes it, but `hard_filter_status` still includes regime. Current candidate admission does not use `hard_filter_status`, reducing direct effect, but naming/contract is inconsistent. |
| Candidate admission | latest Investability >= NEAR_PASS | MATCH | Current watchlist admission is structural Investability only; Tradability is retained as a separate current-entry condition. |
| Breakout pivot | structure computes rolling 60-session high including current bar; Tradability uses previous day's `pivot_high` via shift(1) | MATCH | Effective breakout threshold excludes T0 by using prior pivot state; T0 close is compared to prior 60-session high. |
| Breakout execution semantics | signal uses T0 close; production position path later fills realistic entry at next trading-day open | MATCH | Consistent with T0 signal / T+1 Open executable-entry constraint. |
| Volume confirmation | rolling 50-session current-volume percentile >=80 | MATCH | Formula and threshold match frozen contract; Sep14 anomaly was upstream data contamination, now remediated. |
| VCP tightness | `100 - ATR14 percentile over 63d` | APPROXIMATION | Explicit placeholder/proxy in source, not canonical VCP morphology. |
| Tradability PASS | breakout + volume + tightness | VALID USSY DEFINITION | This is status classification only. Production position entry separately requires hard-filter PASS + breakout + volume and does not require tightness. |
| Tradability NEAR_PASS | any breakout that is not PASS, including no volume and no tightness | VALID USSY DEFINITION | Deliberate weak-candidate bucket, not a confirmed entry. |
| Production entry gate | README documents hard-filter PASS + breakout + volume | NEEDS_EVIDENCE | README and orchestration point to `positions.register_new_positions`; exact implementation should remain covered by dedicated entry-path validation rather than inferred solely from docs. |
| `pct_off_52w_high` | computed but not used by hard filter/decision layer | DEAD/UNUSED | Present as feature but absent from current Investability/Tradability decision path. |
| `rs_sector` / RS persistence | computed but not used by current hard filter/decision layer | DEAD/UNUSED | Diagnostic/context features, not current decision gates. |
| VIX volatility regime | computed and merged, but not used by current hard filter/decision layer | DEAD/UNUSED | Does not currently gate candidates. |
| `hard_filter_status` vs Investability | hard filter includes regime; Investability recomputes only trend/liquidity/RS/price | VALID USSY DEFINITION | Two different aggregates exist. Candidate selection explicitly uses Investability; production entry may still use hard-filter status, so the distinction must remain explicit. |

## Highest-priority audit consequence

The principal execution inconsistency is **historical EMA basis**. The latest terminal row is governed canonical `adj_close`, but all earlier feature rows are produced by legacy `close_raw` EMA calculations. Therefore:

1. current-day Investability uses canonical adjusted EMA facts;
2. retrospective analyses over `decided` can use a different EMA basis before the terminal date;
3. historical lifecycle/validation studies must not silently assume a uniform adjusted-EMA contract across the full history.

This is an audit finding, not authorization to rewrite production history. A remediation requires its own development -> untouched validation cycle because it can alter historical classifications and research outcomes.

## Stage-analysis conclusion

The current Stage1-4 implementation is a deterministic USSY proxy around weekly close, SMA30W, and a three-observation slope. It should be documented as an approximation, not as faithful Weinstein Stage Analysis. Stage1 and Stage3 in particular do not model prior-cycle/base/distribution context.

## Temporal/look-ahead conclusion

No direct T0-close-as-executable-entry defect was found in the inspected orchestration: decision state is formed at the latest close and the position layer is responsible for T+1 realistic entry. Breakout correctly shifts the rolling pivot by one session before comparing T0 close. Weekly stage is backward-merged from Friday labels and therefore does not expose a future Friday weekly value to Mon-Thu rows.

The historical EMA mixed-basis issue is a semantic consistency defect rather than a classic look-ahead leak.

## Next diagnostic

Before any remediation, attribute the 2026-09-10 `+61` first-admission jump at the component level (`trend_status`, `stage`, EMA alignment, liquidity, RS, price) using the frozen current code/data lineage. The purpose is to determine which component transitions explain the jump without tuning thresholds after observing the outcome.
