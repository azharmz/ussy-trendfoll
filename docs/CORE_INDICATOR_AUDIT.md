# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

Extended engineering audit: `docs/FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md`

Evidence/findings register: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose

This is the primary completion track for the original signal-engine question:

> Are the indicators used by current USSY TrendFoll valid for their stated purpose, how do they differ from the legacy engine, and are those differences material to trading decisions?

The 269-item Full Signal Engine Audit is retained as the **Extended Engineering Audit**. Its completed evidence remains valid and is not reset. Engineering remediation, upstream durability, provenance, and production-governance work do not block completion of this Core Indicator Audit unless they prevent a defensible indicator verdict.

## Completion rule

For each production-relevant component, close these questions:

1. What did legacy use?
2. What does current use?
3. Is the current formula implemented as intended?
4. Is the stated interpretation supported by what the formula actually measures?
5. Is the signal temporally causal at T0 close / executable under the governed T+1 model where relevant?
6. Is the difference from legacy material to screening/trading decisions?
7. Final verdict and action: retain, rename/re-document, correct, or research separately.

Controlled verdicts remain: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.

## Core progress

C01 through C03 are closed. Remaining components still require an explicit legacy-vs-current comparison before receiving a final Core verdict.

- [x] C01 Trend / EMA
- [x] C02 Stage Analysis
- [x] C03 Relative Strength vs SPY
- [ ] C04 Liquidity
- [ ] C05 Price floor
- [ ] C06 ATR / volatility tightness
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 3 / 10 final legacy-vs-current verdicts.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `MATCH` / `VALID USSY DEFINITION` | T0 causal; READY-lineage/as-of governed. | **CLOSED.** Legacy finite `EMA(close_raw)` -> current canonical recursive `EMA(adj_close)`. | **RETAIN.** Historical/research consistency is Extended work. |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope; compact Stage1–4 mapping. | `APPROXIMATION` | **PASS / causal** via backward-as-of weekly semantics. | **CLOSED / MATCH.** Same formula exists in original repository implementation and current path. | **RETAIN + REDOCUMENT** as Weinstein-inspired approximation. |
| C03 | RS vs SPY | Stock 63-session return is `close_adj[t] / close_adj[t-63] - 1`; SPY uses the same `compute_return_n()` default adjusted-close basis; `rs_spy = stock_return_63d - spy_return_63d`. Hard-filter classification is PASS >= 0, NEAR_PASS >= -0.02, otherwise FAIL. Current R2 adapter changes the stock data source to governed READY but deliberately reuses `feature_engine.build_feature_store()` for RS and benchmarks; only terminal EMA is separately overridden. | `MATCH` legacy-to-current formula / `VALID USSY DEFINITION` for a 63-session excess-return-vs-SPY feature. It is **not** an IBD/O'Neil cross-sectional RS Rating. The choice of 63 sessions and -2pp NEAR_PASS band remains a design rationale question, not an implementation mismatch. | **PASS / causal.** Stock and SPY returns use observations at or before T0 and SPY is merged by exact `date`. Missing same-date benchmark return remains missing rather than being forward-filled from a future date. | **CLOSED / MATCH.** Original `feature_engine.py` and `hard_filter.py` at commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` already use the same adjusted-close 63-session excess return and the same 0 / -0.02 thresholds. Repository history shows no later formula migration for RS. | **RETAIN.** No legacy-to-current drift to correct. Evidence 11 empirically supports adjusted-close stock-return semantics around corporate actions: 23/31 audited event rows had >5pp raw-vs-adjusted 63-session return gaps. Keep horizon/threshold justification as separate `NEEDS_EVIDENCE`; do not tune it merely to create a difference from legacy. |
| C04 | Liquidity | 50-session mean raw share volume, min 20; PASS >=300k, NEAR >=240k | `MISMATCH` around split-sensitive windows; threshold rationale separately open | T0 causal; corporate-action unit consistency defect identified | **OPEN — exact legacy baseline to record** | FSE-014 correction spec is already frozen; keep remediation in Extended track rather than blocking all Core components |
| C05 | Price floor | Raw close >=$10 PASS; >=$8 NEAR | `VALID USSY DEFINITION`; threshold rationale `NEEDS_EVIDENCE` | T0 close causal | **OPEN — exact legacy baseline to record** | Retain as nominal-price rule unless legacy/evidence comparison supports change |
| C06 | ATR / volatility tightness | ATR14 plus `vcp_tightness = 100 - ATR percentile(63)` | ATR: `MATCH`; VCP label: `MISMATCH` with literal VCP morphology | T0 causal | **OPEN — exact legacy baseline to record** | Strong candidate for rename/re-document as volatility-tightness proxy rather than rebuilding VCP inside this audit |
| C07 | Pivot / breakout | Pivot proxy = rolling raw high 60, min20; Tradability compares T0 close with shifted prior-row pivot | Pivot-as-O'Neil semantics: `MISMATCH`; rolling-high breakout: `VALID USSY DEFINITION` | Breakout T0 is causal; executable after T0 close | **OPEN — exact legacy baseline to record** | Decide intended label: rolling-high/Donchian-like breakout vs chart-base pivot; avoid silently claiming O'Neil pivot |
| C08 | Breakout volume | Current raw volume percentile in rolling 50 including current; confirmation >=80 | `APPROXIMATION` | T0 causal | **OPEN — exact legacy baseline to record** | FSE-015 proved Sep-14 mass anomaly was upstream incomplete volume, not percentile-formula failure; compare legacy semantics before changing formula |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime; excluded from Investability but included in hard-filter contract | `MATCH` architecture / `VALID USSY DEFINITION` | Backward-as-of; empirical freshness audit passed | **OPEN — exact legacy baseline to record** | Preserve distinction between Investability and hard-filter consumers |
| C10 | Investability / Tradability | Investability = Trend + Liquidity + RS + Price non-compensatory aggregation; Tradability = breakout + volume confirmation + tightness; production position entry intentionally retains separate backtest-parity contract | Aggregation contract traced; dual downstream contract = `VALID USSY DEFINITION` | T0 decision semantics traced; T+1 realistic execution path documented | **OPEN — exact legacy baseline to record** | Compare legacy aggregation/entry contract directly; do not silently unify alert and position-entry contracts |

## C01 evidence note — canonical adjusted EMA migration

C01 is closed using repository evidence rather than the current contents of `feature_engine.py` alone. Production migration commit `f35c3fb0376b7342e73efe7a55419a1fb30a07f9` established the governed shared adjusted-close EMA terminal contract.

**C01 final Core action: `RETAIN`.**

## C02 evidence note — Stage Analysis

The original repository implementation and current Stage path use the same W-FRI / SMA30w / three-observation slope / Stage1–4 mapping. Temporal regression coverage verifies backward-as-of weekly visibility, including holiday edge cases.

**C02 final Core action: `RETAIN + REDOCUMENT`.**

## C03 evidence note — Relative Strength vs SPY

The legacy baseline is explicit in the original repository state. `RS_LOOKBACK_DAYS = 63`; `compute_return_n(..., col="close_adj")` calculates adjusted-close 63-session return. `build_feature_store()` applies the same helper to both each stock and SPY, joins SPY by exact `date`, and defines `rs_spy = return_63d - spy_return_63d`. The original hard-filter thresholds are already PASS >= 0 and NEAR_PASS >= -0.02.

The current R2 path does not replace this formula. `r2_feature_engine.build_feature_store_from_r2()` maps governed READY `adj_close` to the legacy contract's `close_adj`, substitutes only the stock OHLCV source, and executes `feature_engine.build_feature_store()` for the feature formulas and benchmark downloads. Its only explicit post-build indicator migration is terminal canonical EMA. Therefore current RS semantics remain the legacy RS semantics, but the stock facts now come from governed READY.

Corporate-action Evidence 11 materially supports the adjusted-return basis. Across 31 identified corporate-action-sensitive event rows, 23 had an absolute raw-vs-adjusted 63-session return gap greater than five percentage points, with a maximum gap of 62.55 percentage points. This means raw close is not an interchangeable basis for this return feature.

The feature should be described precisely as **63-session excess return versus SPY**, not as an IBD/O'Neil RS Rating. Whether 63 sessions is the best horizon for the strategy, and whether -2 percentage points is the right NEAR_PASS band, remains `NEEDS_EVIDENCE`; that is a research/design question rather than evidence that the current implementation is wrong.

**C03 final Core action: `RETAIN`.** No formula correction is indicated by the legacy comparison or corporate-action evidence.

## Existing deep evidence retained

The following work remains authoritative supporting evidence rather than being repeated:

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: FSE-013 effective-date lifecycle correction passed research contract/regression and untouched validation V2; production decision remains separate.
- Evidence 11: corporate-action semantics for RS, liquidity, and nominal price.
- Evidence 12: Sep-14 partial-volume incident; TrendFoll percentile formula behaved as implemented; residual upstream repair was handled separately.
- Evidence 13: FSE-014 split-normalized share-liquidity correction specification is frozen; this is an engineering remediation track, not a reason to hold every Core verdict open.

## Scope boundary

### Core Indicator Audit — primary now

Close the ten rows above by extracting the exact legacy definition and comparing it directly with current behavior. Do not open a new engineering workstream merely because a current indicator is an approximation. A correction is required only when the mismatch is material to the intended signal contract.

### Extended Engineering Audit — retained, not reset

`FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md` preserves the 269-item audit, completed checks, incident evidence, correction governance, tests, and production-decision gates. It can continue selectively for material findings and remediation.

## Next execution sequence

1. C01 closed: `RETAIN`.
2. C02 closed: `RETAIN + REDOCUMENT`.
3. C03 closed: unchanged 63-session adjusted excess return vs SPY; `RETAIN`.
4. Recover exact legacy liquidity contract and compare it with current R2 path and the already-frozen FSE-014 split-adjustment correction contract for C04.
5. Continue C05–C10 using repository history/code rather than assuming visible legacy code equals current behavior.
6. Close each remaining Core row with one action: `RETAIN`, `RENAME / REDOCUMENT`, `CORRECT`, or `RESEARCH SEPARATELY`.
7. Produce one concise final Legacy-vs-Current conclusion before optional Extended Engineering backlog resumes.

Production remains untouched throughout this Core audit.