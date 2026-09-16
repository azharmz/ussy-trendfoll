# Full Signal Engine Audit — Investability + Tradability

Status: **AUDIT IN PROGRESS / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

> **Operational audit control:** use `docs/FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md` as the primary detailed checklist and progress ledger. This file remains the evidence, analysis, and findings register. Audit work should update the checklist as tasks are completed.

## Governance

This audit is independent of EXIT-CAND-003. Production changes are forbidden until the audit, root-cause register, correction candidates, tests, validation, and explicit production decision are complete.

Audit classifications: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.

## Checklist

- [x] A. Trace actual production entry point and execution path
- [x] B. Trace R2 ready ingestion and feature adapter
- [x] C. Trace hard filter and decision layer
- [ ] D. Complete feature-by-feature audit matrix
- [ ] E. Complete Investability audit
- [ ] F. Complete Tradability audit
- [ ] G. Complete Stage Analysis audit against authoritative methodology
- [ ] H. Complete data/warm-up audit
- [ ] I. Complete temporal/look-ahead audit
- [ ] J. Complete findings register and correction candidates
- [ ] K. Tests/validation for approved corrections
- [ ] L. Current-R2 funnel only after engine audit is clean

## A. Actual production execution map

GitHub Actions `.github/workflows/daily.yml` executes `python r2_main.py`.

Actual current path:

`R2 production/ready/current.json`
→ `r2_ready.load_ready_dataset()`
→ manifest/schema/checksum/security-id validation
→ `r2_ready.to_feature_contract()`
→ `r2_feature_engine.build_feature_store_from_r2()`
→ legacy `feature_engine.build_feature_store()` with R2 stock OHLCV injected
→ benchmark OHLCV still downloaded independently by `feature_engine`
→ per-symbol EMA / structure / volume / RS / weekly stage
→ `r2_shared_ema.apply_shared_ema_terminal()`
→ terminal-row canonical EMA(adj_close) replacement only
→ `hard_filter.compute_hard_filter()`
→ `decision_layer.compute_decision_layer()`
→ latest-date selection
→ Investability >= NEAR_PASS candidate/watchlist selection
→ near-trigger shadow (separate research)
→ position coverage / previous watchlist
→ alert-state transitions
→ watchlist upsert / lifecycle
→ notification on state change
→ production position entry/exit path
→ EXIT-CAND-003 observational shadow last.

### Important architectural observation

The R2 adapter does **not** make the complete engine R2-only. It replaces stock-universe OHLCV, while `feature_engine.build_feature_store()` still downloads SPY/QQQ/VIX/sector ETF benchmark data externally. Therefore stock facts and benchmark facts have different ingestion/readiness contracts and potentially different session/freshness semantics.

## Findings register

| ID | Severity | Component | Classification | Finding |
|---|---|---|---|---|
| FSE-001 | HIGH | Stage Analysis | APPROXIMATION | Current Stage1–4 classifier uses only weekly close vs 30-week SMA plus a 3-observation monotonic SMA slope. It contains no prior-cycle/base/top context, support/resistance, breakout/breakdown, volume, or RS context. Stage1 vs Stage3 is therefore a mechanical approximation, not faithful full Weinstein stage identification. |
| FSE-002 | HIGH | VCP/tightness | MISMATCH | `vcp_tightness = 100 - ATR percentile(63d)` measures low current ATR relative to its recent distribution. It does not identify a sequence of volatility contractions and must not be interpreted as literal Minervini VCP morphology. |
| FSE-003 | HIGH | Pivot semantics | MISMATCH | `pivot_high` is a 60-session rolling maximum including the current bar. Tradability shifts this one row to `prev_pivot_high`, avoiding the most obvious current-bar self-comparison, but the value remains a rolling high rather than a validated O'Neil/base pivot. |
| FSE-004 | MEDIUM | Volume confirmation | APPROXIMATION | Breakout volume percentile uses a 50-session rolling distribution that includes current volume. It is a contemporaneous percentile rank, not a historical-only reference distribution and not the same semantic as O'Neil-style volume increase versus normal/average volume. |
| FSE-005 | HIGH | EMA basis consistency | MISMATCH | Legacy feature history computes EMA and stack from raw close. `r2_shared_ema` replaces EMA facts and stack only on each symbol's terminal row using canonical adj_close long-history state. Historical rows used by lifecycle/research therefore retain a different EMA basis/initialization contract than the terminal production row. |
| FSE-006 | MEDIUM | Price/EMA semantic consistency | VALID USSY DEFINITION | Terminal EMA stack is explicitly `adj_close > EMA20 > EMA50 > EMA150 > EMA200`, while price-floor and breakout remain raw-price rules. This can be a defensible internal split, but documentation must state it explicitly and tests must protect it. |
| FSE-007 | MEDIUM | Benchmark ingestion | NEEDS_EVIDENCE | SPY/QQQ/VIX/sector ETF data are downloaded live through the legacy feature engine rather than governed by the R2 ready snapshot. Alignment uses exact-date merges for RS and backward as-of merge for regime. Freshness/session mismatch risk requires empirical audit. |
| FSE-008 | HIGH | R2 warm-up | NEEDS_EVIDENCE | Most stock features are calculated from the rows present in the ready Parquet. Canonical long-history state currently repairs terminal EMA only. Stage30w, 52-week high, RS63, pivot60, ATR percentile63 and volume windows still depend on R2-ready history depth and must be checked against actual readiness distribution. |
| FSE-009 | INFO | Regime architecture | MATCH | Decision-layer Investability correctly excludes regime. However `hard_filter_status` still includes regime; audit downstream consumers to ensure they do not accidentally substitute it for Investability. |
| FSE-010 | MEDIUM | Breakout temporal semantics | MATCH | Tradability compares T0 raw close to a shifted prior-row rolling high, so the current bar is not inside the pivot used for the T0 breakout decision. Signal is knowable only after T0 close; executable-entry governance remains T+1 Open. |
| FSE-011 | MEDIUM | Downstream decision contracts | VALID USSY DEFINITION | Watchlist/actionability and production-position entry intentionally use different downstream contracts: alerts are Investability/Tradability based, while production entry preserves the governed hard-filter + breakout + volume-confirmation backtest-parity contract. The distinction must remain explicit rather than being silently unified. |
| FSE-012 | LOW | Entry-price semantics | VALID USSY DEFINITION | Position registration preserves T0 trigger facts while realistic execution is evaluated at the first available T+1 Open using T0 ATR for the provisional stop. Naming/documentation must distinguish trigger price from executable entry price. |
| FSE-013 | HIGH | Effective-date lifecycle state | MISMATCH | Common-date cross-sectional selection is correct, but downstream alert/candidate lifecycle previously treated absence of a current-date row as signal `INVALIDATED`. Evidence 10 freezes the intended distinction: current-date evaluation failure is invalidation; unavailable current data is a separate non-actionable data state. Research-branch correction and dedicated regression tests exist; production remains unchanged pending governed validation. |
| FSE-014 | HIGH | Liquidity / corporate actions | MISMATCH | Raw-share-volume rolling windows can span structurally incomparable pre/post split share-count units. Evidence 11 empirically confirms exposure in the corporate-action-sensitive population. A governed correction specification is still required before any production change. |
| FSE-015 | HIGH | R2 READY volume completeness | MISMATCH | Evidence 12 shows the Sep-14 READY terminal volume population was materially incomplete: 933/1,223 securities were below every prior-50 volume observation. The unchanged diagnostic on refreshed finalized Sep-15 data falls to 19/1,220 and normal volume ratios, validating the TrendFoll percentile formula and observed new-session finalization. Historical same-date reconciliation remains open because append-only upstream updates do not themselves repair an already persisted partial bar. |

## Initial feature matrix

| Feature | Intended semantics | Actual formula/basis | Temporal semantics | Status | Finding |
|---|---|---|---|---|---|
| EMA20/50/150/200 terminal | structural trend state | governed recursive EMA on `adj_close` from shared R2 indicator state | T0 state aligned to ready snapshot | MATCH | Canonical terminal state is explicitly validated against current ready lineage. |
| EMA history | historical trend state | legacy pandas EWM on `close_raw`, `adjust=False` | includes current close at each row | MISMATCH | Different basis/state contract from terminal canonical EMA. |
| ema_stack_aligned terminal | ordered structural trend | `adj_close > EMA20 > EMA50 > EMA150 > EMA200` | known after T0 close | VALID USSY DEFINITION | Internal quantitative trend definition; not claimed as literal source definition. |
| Stage | Weinstein-inspired lifecycle stage | weekly raw close; SMA30w; slope from last 3 MA observations; price/slope lookup | weekly state backward-filled/as-of to daily | APPROXIMATION | Insufficient context for faithful Stage1/Stage3 lifecycle distinction. |
| RS vs SPY | stock outperformance vs market | stock adj-close 63d return minus SPY adj-close 63d return | exact-date benchmark merge | VALID USSY DEFINITION | Arithmetic meaning of >0 is 63-session excess simple return; evidence for horizon/threshold still pending. |
| avg_volume_50d | liquidity proxy | mean raw share volume, 50d, min 20 | includes T0 volume | NEEDS_EVIDENCE | Threshold rationale and split-volume semantics pending. |
| price floor | avoid low-priced securities/data-quality risk | raw close >= 10 PASS; >=8 NEAR | T0 close | NEEDS_EVIDENCE | Threshold rationale pending. |
| pivot_high | resistance/pivot proxy | raw high rolling max 60d, min20 | includes current row, then shifted 1 row by tradability | MISMATCH | Not a validated chart-pattern pivot. |
| breakout | actionable close breakout | `close_raw(T0) > pivot_high(T-1)` | known after T0 close | VALID USSY DEFINITION | Valid rolling-high breakout definition, but should not be labeled O'Neil pivot breakout. |
| breakout volume percentile | unusual volume proxy | percentile of current raw volume within rolling 50 incl. current | known after T0 close | APPROXIMATION | Historical-only comparator not used. |
| ATR14 | volatility/risk | Wilder-style EWM of raw-price true range | current bar included | MATCH | Formula materially represents ATR. |
| vcp_tightness | structure tightness proxy | `100 - ATR percentile 63d` | current ATR included | MISMATCH | Low-volatility proxy, not VCP contraction sequence. |
| base_length_days | local consolidation proxy | backward scan within 8% dynamic high band, max120 | current and prior bars only | APPROXIMATION | Bespoke USSY structure heuristic; not authoritative base morphology. |
| market_regime | portfolio environment | SPY raw close vs SMA50/SMA200 | backward as-of merged to stock rows | VALID USSY DEFINITION | Internal three-state regime; downstream usage audit pending. |

## Source/evidence boundary

Authoritative methodology and USSY quantitative representation must remain separate. IBD first-party educational material defines buy points from recognized chart bases, so a generic rolling maximum is not automatically an O'Neil pivot. The current VCP field is explicitly described in code as a placeholder inverse ATR percentile and must be treated as a volatility-tightness proxy. Weinstein Stage Analysis is a lifecycle/chart-context framework around weekly price, the 30-week MA and additional technical context; the current four-way rule is therefore recorded as an approximation pending the dedicated source audit.

## Sep-10 lifecycle diagnostic addendum

The detailed operational checklist includes a dedicated Sep-4 through Sep-10 workflow-continuity audit and a symbol-level reconstruction of the Sep-10 lifecycle jump: cumulative 100 -> +61 first-time -> 161, while current Investability >= NEAR_PASS was 85. The diagnostic explicitly tests market movement, pipeline continuity, R2 snapshot lineage, code/config changes, feature/warm-up effects, Stage/EMA/RS transitions, and other state-machine defects without presuming the jump is anomalous.

Legacy-universe contamination is treated as closed/disproven under the established membership result: current R2 READY 1,227; lifecycle 161; 161/161 present in current R2 READY; legacy-only 0.

## Evidence 10–12 audit addendum

Evidence 10 separates effective-date availability from genuine signal invalidation and freezes the intended state contract before correction. Evidence 11 closes the empirical corporate-action checks for RS, liquidity, and nominal price semantics: adjusted-close RS is appropriate for corporate-action-adjusted return comparison; nominal raw-close price floor remains a valid explicit USSY definition; raw-share-volume windows are corporate-action sensitive and require a correction specification. Evidence 12 identifies the Sep-14 mass terminal-volume anomaly as an upstream READY completeness defect rather than a TrendFoll percentile-formula defect. The post-refresh Sep-15 rerun validates new-session finalization behavior but does not close historical same-date reconciliation.

## Next audit milestone

Follow `docs/FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md` in order. Immediate remaining governance includes historical READY reconciliation, effective-date universe-removal semantics, feature methodology/threshold evidence, untouched validation, and final production decision. Production remains untouched.
