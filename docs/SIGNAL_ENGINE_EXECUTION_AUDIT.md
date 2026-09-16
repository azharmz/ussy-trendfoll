# Signal Engine Execution Audit

Status: **DIAGNOSTIC / NO PRODUCTION LOGIC CHANGED**

Audit date: 2026-09-16

Scope: actual R2 production path `R2 READY -> FEATURES -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST/ALERT` on branch `research/exit-development-hypotheses`.

Classification vocabulary: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD/UNUSED`.

## Actual execution map

`r2_main.py` -> R2 READY -> feature builder -> canonical terminal EMA overlay -> hard filter -> decision layer -> latest common market date -> Investability >= NEAR_PASS candidate admission -> alert/watchlist -> production positions/exits -> CAND-003 shadow.

Stock OHLCV comes from R2 READY. Benchmark/regime inputs (SPY, QQQ, VIX, sector ETFs) still come through `feature_engine`.

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
| Weekly temporal merge | Friday-labelled weekly rows merged backward to daily rows | MATCH | Mon-Thu cannot see a future Friday label; Friday uses contemporaneous Friday close. |
| RS stock return | 63-session `close_adj` return | MATCH | Adjusted-price return is appropriate for relative return. |
| RS benchmark | stock 63-session return minus SPY 63-session return | VALID USSY DEFINITION | Excess 63-day return vs SPY, not an IBD RS Rating. |
| RS threshold | PASS >=0; NEAR_PASS >=-0.02 | VALID USSY DEFINITION | Frozen USSY threshold. |
| Liquidity | avg raw share volume 50d; PASS >=300k, NEAR >=240k | VALID USSY DEFINITION | Share-volume gate, not dollar-volume liquidity. |
| Price floor | raw close PASS >=$10, NEAR >=$8 | VALID USSY DEFINITION | Explicit USSY gate. |
| Market regime | SPY raw close vs SMA50/SMA200 | VALID USSY DEFINITION | Bullish/Neutral/Bearish portfolio-regime proxy. |
| Hard filter | trend + liquidity + RS + price + regime, non-compensatory | VALID USSY DEFINITION | Production entry uses this five-component aggregate. |
| Investability | trend + liquidity + RS + price, excludes regime | MATCH | Structural candidate layer; admission threshold >= NEAR_PASS. |
| Breakout pivot | 60-session structure high shifted one day before T0 comparison | MATCH | T0 is excluded from its own breakout threshold. |
| Breakout execution | T0 signal; realistic fill assigned from next trading-day open | MATCH | Consistent with T0 signal / T+1 Open execution. |
| Volume confirmation | rolling 50-session current-volume percentile >=80 | MATCH | Frozen formula/threshold; Sep14 upstream partial-bar incident is closed. |
| VCP tightness | `100 - ATR14 percentile over 63d` | APPROXIMATION | Explicit proxy, not canonical VCP morphology. |
| Tradability PASS | breakout + volume + tightness | VALID USSY DEFINITION | Status tier only; tightness is not production entry gate. |
| Tradability NEAR_PASS | breakout without all PASS subconditions | VALID USSY DEFINITION | Weak-candidate tier, not confirmed entry. |
| Production entry gate | hard-filter PASS + breakout + volume | MATCH | Verified directly in `positions.register_new_positions`; tightness not required. |
| T+1 realistic entry | pending T0 position later filled with first subsequent `open_raw` | MATCH | Verified in `fill_realistic_entry_prices`. |
| `pct_off_52w_high` | computed but absent from current decision gates | DEAD/UNUSED | Context feature only. |
| `rs_sector` / RS persistence | computed but absent from current decision gates | DEAD/UNUSED | Context/diagnostic only. |
| VIX volatility regime | computed but absent from current decision gates | DEAD/UNUSED | Does not gate candidates. |

## Highest-priority audit consequence — historical EMA basis

Current-day Investability uses canonical adjusted EMA facts, while retrospective `decided` rows use legacy raw-close EMA calculations. Historical lifecycle/validation studies must not assume a uniform adjusted-EMA contract. This is a semantic consistency defect, not a look-ahead finding. Any remediation can alter historical classifications and therefore requires development -> untouched validation before production change.

## Stage-analysis conclusion

Stage1-4 is a deterministic USSY proxy around weekly close, SMA30W, and a three-observation slope. It should be described as an approximation rather than faithful Weinstein Stage Analysis.

## Temporal/look-ahead conclusion

No direct T0-close-as-executable-entry defect was found. Breakout shifts pivot state by one session, weekly merge does not expose future Friday values to Mon-Thu, and realistic entry is filled from the first subsequent trading-day open.

## Sep10 first-admission attribution — RESOLVED

Read-only audit run `35068878141` reconstructed all 61 symbols whose first persisted watchlist date is 2026-09-10, comparing Sep04 with Sep10 under current retrospective semantics.

- Sep10: 57 PASS, 4 NEAR_PASS.
- Sep04 reconstruction: 39 PASS, 22 FAIL.
- transitions: 39 PASS->PASS, 20 FAIL->PASS, 2 FAIL->NEAR_PASS.
- trend accounted for all 22 component recoveries; RS was unchanged for all 61; liquidity and price each improved for only one name.

The decisive lineage check is the legacy `feature_engine.UNIVERSE`: it contains 197 symbols, and **0 of the 61 Sep10 first-admission symbols are members of that legacy universe**. Therefore the apparent `+61` is a **universe-coverage boundary**, not a 61-name market transition. Those names could not have appeared in watchlist output while the old static 197-symbol ingestion boundary was in force. Once the R2-first universe path exposed the wider READY universe, they became observable to the candidate lifecycle.

The 22 trend improvements describe what those newly visible names did between Sep04 and Sep10 under retrospective reconstruction; they do **not** explain why the names first entered persistence on Sep10. The persistence jump is explained by universe expansion/migration.

Governance consequence: do not interpret the Sep10 +61 as market breadth, threshold behavior, or a signal-engine regime event. Historical lifecycle counts spanning the legacy-universe -> R2-universe boundary are not directly comparable without a common-universe restriction.

Caveat: Sep04/Sep10 reconstruction uses legacy `close_raw` EMA for historical rows because canonical shared `adj_close` EMA replacement currently applies only to the terminal row.

## Next workstream

The Sep10 anomaly is closed as a lineage/universe-boundary effect. The remaining material engine-audit defect is historical EMA basis consistency. Before changing production, create a development-only adjusted-EMA historical candidate, quantify classification deltas versus the frozen legacy historical path, then freeze and run untouched validation. No post-outcome threshold tuning.
