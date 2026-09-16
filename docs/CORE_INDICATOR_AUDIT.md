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

C01 through C04 are closed. Remaining components still require an explicit legacy-vs-current comparison before receiving a final Core verdict.

- [x] C01 Trend / EMA
- [x] C02 Stage Analysis
- [x] C03 Relative Strength vs SPY
- [x] C04 Liquidity
- [ ] C05 Price floor
- [ ] C06 ATR / volatility tightness
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 4 / 10 final legacy-vs-current verdicts.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `MATCH` / `VALID USSY DEFINITION` | T0 causal; READY-lineage/as-of governed. | **CLOSED.** Legacy finite `EMA(close_raw)` -> current canonical recursive `EMA(adj_close)`. | **RETAIN.** Historical/research consistency is Extended work. |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope; compact Stage1–4 mapping. | `APPROXIMATION` | **PASS / causal** via backward-as-of weekly semantics. | **CLOSED / MATCH.** Same formula exists in original repository implementation and current path. | **RETAIN + REDOCUMENT** as Weinstein-inspired approximation. |
| C03 | RS vs SPY | 63-session adjusted-close stock return minus same-basis SPY return; PASS >=0, NEAR >=-0.02. | `MATCH` / `VALID USSY DEFINITION` as 63-session excess return vs SPY. | **PASS / causal.** | **CLOSED / MATCH.** Same formula and thresholds in original repository state. | **RETAIN.** Horizon/threshold rationale remains separate research question. |
| C04 | Liquidity | **Current production still uses the legacy formula:** `avg_volume_50d = rolling_mean(volume_raw, 50, min_periods=20)`; PASS >=300k, NEAR_PASS >=240k. R2 changes the stock data source to READY but maps READY `volume` directly to `volume_raw`; there is no production split-normalization overlay analogous to EMA. | `MISMATCH` for the intended share-liquidity meaning in windows spanning share-count-changing corporate actions. Raw share counts before and after a split are in different units, so their unnormalized arithmetic mean is not consistently comparable. Outside affected windows the formula remains coherent as average daily shares traded. Threshold rationale remains separately `NEEDS_EVIDENCE`. | The rolling calculation itself is T0-causal, but unit consistency across a historical split window is defective. The frozen correction contract is also explicitly as-of causal: only split events effective through T0 may normalize a T0 window; future events must not back-propagate. | **CLOSED / MATCH legacy-to-current production.** Original `feature_engine.py` already used raw `volume_raw` rolling 50/min20, and original `hard_filter.py` already used 300k/240k thresholds. Current R2 production retains those same semantics. Therefore this is **not new current-vs-legacy drift**; it is a legacy defect still present in current production. | **CORRECT (governed remediation), not RETAIN.** FSE-014 already froze the minimal correction: preserve share-liquidity semantics/window/min-period/thresholds, but express historical volumes on each T0 share-unit basis using explicit split/share factors. Research-only implementation exists and its CI contract gate passed. Production adoption remains a separate governed decision; Core does not silently modify production. |
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

Legacy and current both implement adjusted-close 63-session excess return versus SPY, with unchanged PASS >=0 / NEAR_PASS >=-0.02 thresholds. Evidence 11 supports adjusted-return basis around corporate actions.

**C03 final Core action: `RETAIN`.**

## C04 evidence note — Liquidity

The original repository implementation at `94b78f008d0a003ed5cf37c53e3fd4253122c259` defines `avg_volume_50d` as a rolling 50-session arithmetic mean of `volume_raw` with `min_periods=20`. Its hard-filter thresholds are already PASS >=300,000 and NEAR_PASS >=240,000. Current R2 production maps READY `volume` directly to `volume_raw` and reuses `feature_engine.build_feature_store()`; unlike terminal EMA, no current production liquidity override exists. C04 is therefore legacy=current at the formula level.

That equality does not make the formula correct across split-sensitive windows. Evidence 11 established that raw observations around corporate actions can be materially non-interchangeable, and specifically classified the rolling raw-share-volume feature as a corporate-action-sensitive window requiring a correction specification. The defect is dimensional: pre- and post-split share volumes may represent the same economic activity in different share units.

FSE-014 Evidence 13 has already frozen the minimal correction contract rather than changing the economic feature. `avg_volume_50d` remains average daily **share** liquidity; window=50, min_periods=20, and thresholds 300k/240k remain fixed for the correction cycle. Historical raw volumes inside a T0 window are converted to the T0 share-unit basis using explicit split/stock-dividend share factors effective in `(t, T0]`. Dollar volume and `adj_close/close`-derived volume factors are explicitly rejected for this correction cycle.

The research-only implementation `liquidity_split_adjustment.py` implements that causal contract without changing `feature_engine.py`. Commit `5e0e91046c30165abeef02857435d5f553ee0c63` introduced the prototype. The frozen FSE-014 CI research gate at run `35080840497`, head `593e8f699494e7e155e95e1835eaf4e98f754056`, completed successfully; job `104744193463` reports the `Run frozen FSE-014 contract tests` step as successful.

This makes the Core conclusion straightforward: **the current liquidity feature has not regressed relative to legacy; legacy and current share the same defect.** The correct Core action is nevertheless `CORRECT`, because the mismatch is material to the intended share-liquidity contract in split-sensitive windows and a minimal governed correction is already specified and research-tested.

**C04 final Core action: `CORRECT` under FSE-014 governance.** Production remains unchanged by this audit; production adoption of the frozen correction is a separate governed remediation step.

## Existing deep evidence retained

The following work remains authoritative supporting evidence rather than being repeated:

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: FSE-013 effective-date lifecycle correction passed research contract/regression and untouched validation V2; production decision remains separate.
- Evidence 11: corporate-action semantics for RS, liquidity, and nominal price.
- Evidence 12: Sep-14 partial-volume incident; TrendFoll percentile formula behaved as implemented; residual upstream repair was handled separately.
- Evidence 13: FSE-014 split-normalized share-liquidity correction specification is frozen and its research contract gate has passed; production adoption remains separate.

## Scope boundary

### Core Indicator Audit — primary now

Close the ten rows above by extracting the exact legacy definition and comparing it directly with current behavior. Do not open a new engineering workstream merely because a current indicator is an approximation. A correction is required only when the mismatch is material to the intended signal contract.

### Extended Engineering Audit — retained, not reset

`FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md` preserves the 269-item audit, completed checks, incident evidence, correction governance, tests, and production-decision gates. It can continue selectively for material findings and remediation.

## Next execution sequence

1. C01 closed: `RETAIN`.
2. C02 closed: `RETAIN + REDOCUMENT`.
3. C03 closed: `RETAIN`.
4. C04 closed: legacy=current raw-share-volume rolling mean, but both retain the split-unit defect; action `CORRECT` under frozen FSE-014 governance.
5. Recover exact legacy nominal price-floor contract and compare current consumer path for C05.
6. Continue C06–C10 using repository history/code rather than assuming visible legacy code equals current behavior.
7. Close each remaining Core row with one action: `RETAIN`, `RENAME / REDOCUMENT`, `CORRECT`, or `RESEARCH SEPARATELY`.
8. Produce one concise final Legacy-vs-Current conclusion before optional Extended Engineering backlog resumes.

Production remains untouched throughout this Core audit.