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

C01 and C02 are closed. Remaining components still require an explicit legacy-vs-current comparison before receiving a final Core verdict.

- [x] C01 Trend / EMA
- [x] C02 Stage Analysis
- [ ] C03 Relative Strength vs SPY
- [ ] C04 Liquidity
- [ ] C05 Price floor
- [ ] C06 ATR / volatility tightness
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 2 / 10 final legacy-vs-current verdicts.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | **Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`**, consumed from the shared `ussy-data` EMA state by `r2_shared_ema.apply_shared_ema_terminal()`. The underlying legacy `feature_engine.py` still computes finite-window EWM from `close_raw`, but those legacy EMA facts are replaced on each terminal production row; they are not the canonical current T0 EMA state. | `MATCH` / `VALID USSY DEFINITION` for current terminal production. Historical/research feature rows that retain raw-close finite-window EWM remain a separate basis/initialization mismatch and must not be confused with current terminal production. | T0 causal; shared EMA state must align to the current READY lineage and as-of date. | **CLOSED.** Legacy = finite-window `EMA(close_raw)` in `feature_engine.py`. Current production = governed long-history recursive `EMA(adj_close)`. Migration commit `f35c3fb0376b7342e73efe7a55419a1fb30a07f9` explicitly changed terminal production trend state to canonical shared adjusted EMA after shadow validation. | **RETAIN current production contract.** Migration shadow: 1,226 securities; 16 EMA-stack changes, 15 Trend changes, 5 Hard Filter changes, 5 Investability changes, 5 candidate-membership changes, but 0 Tradability and 0 Actionable changes. Historical/research consistency remains Extended-audit work. |
| C02 | Stage Analysis | Weekly close is derived from daily `close_raw` with `resample("W-FRI").last()`. SMA30w is a 30-week simple moving average. Slope is `Up` only when the last three SMA30w observations are strictly increasing, `Down` only when strictly decreasing, otherwise `Flat`. Stage2 = price > SMA30w + Up; Stage4 = price < SMA30w + Down; Stage3 = price > SMA30w + Flat/Down; all remaining evaluable states = Stage1. | `APPROXIMATION` — a compact Weinstein-inspired stage proxy, not a full quantitative implementation of all Stage Analysis morphology/transition concepts. | **PASS / causal.** Weekly facts are Friday-labelled and consumed through backward-as-of semantics. Tests explicitly verify Mon–Thu cannot observe the current Friday bucket, Friday-holiday weeks do not become visible early, and Monday holidays do not shift the week label. | **CLOSED / MATCH legacy-to-current implementation.** The earliest repository version of `feature_engine.py` available in history (`94b78f008d0a003ed5cf37c53e3fd4253122c259`, 2026-08-01) contains the same W-FRI / SMA30w / three-observation slope / Stage1–4 mapping as the current branch. No later Stage migration/override analogous to canonical EMA was found. | **RETAIN + REDOCUMENT.** There is no legacy-to-current formula drift to remediate. Keep the feature as the existing USSY stage proxy, but describe it explicitly as a Weinstein-inspired approximation rather than implying exhaustive canonical Stage Analysis. No production formula change is justified by the legacy comparison. |
| C03 | RS vs SPY | 63-session stock `adj_close` return minus SPY 63-session return; PASS >=0, NEAR >=-0.02 | `VALID USSY DEFINITION`; horizon/threshold rationale still `NEEDS_EVIDENCE` | Exact-date benchmark merge; causal when benchmark available | **OPEN — exact legacy baseline to record** | Corporate-action basis is appropriate; compare legacy horizon/threshold before deciding change |
| C04 | Liquidity | 50-session mean raw share volume, min 20; PASS >=300k, NEAR >=240k | `MISMATCH` around split-sensitive windows; threshold rationale separately open | T0 causal; corporate-action unit consistency defect identified | **OPEN — exact legacy baseline to record** | FSE-014 correction spec is already frozen; keep remediation in Extended track rather than blocking all Core components |
| C05 | Price floor | Raw close >=$10 PASS; >=$8 NEAR | `VALID USSY DEFINITION`; threshold rationale `NEEDS_EVIDENCE` | T0 close causal | **OPEN — exact legacy baseline to record** | Retain as nominal-price rule unless legacy/evidence comparison supports change |
| C06 | ATR / volatility tightness | ATR14 plus `vcp_tightness = 100 - ATR percentile(63)` | ATR: `MATCH`; VCP label: `MISMATCH` with literal VCP morphology | T0 causal | **OPEN — exact legacy baseline to record** | Strong candidate for rename/re-document as volatility-tightness proxy rather than rebuilding VCP inside this audit |
| C07 | Pivot / breakout | Pivot proxy = rolling raw high 60, min20; Tradability compares T0 close with shifted prior-row pivot | Pivot-as-O'Neil semantics: `MISMATCH`; rolling-high breakout: `VALID USSY DEFINITION` | Breakout T0 is causal; executable after T0 close | **OPEN — exact legacy baseline to record** | Decide intended label: rolling-high/Donchian-like breakout vs chart-base pivot; avoid silently claiming O'Neil pivot |
| C08 | Breakout volume | Current raw volume percentile in rolling 50 including current; confirmation >=80 | `APPROXIMATION` | T0 causal | **OPEN — exact legacy baseline to record** | FSE-015 proved Sep-14 mass anomaly was upstream incomplete volume, not percentile-formula failure; compare legacy semantics before changing formula |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime; excluded from Investability but included in hard-filter contract | `MATCH` architecture / `VALID USSY DEFINITION` | Backward-as-of; empirical freshness audit passed | **OPEN — exact legacy baseline to record** | Preserve distinction between Investability and hard-filter consumers |
| C10 | Investability / Tradability | Investability = Trend + Liquidity + RS + Price non-compensatory aggregation; Tradability = breakout + volume confirmation + tightness; production position entry intentionally retains separate backtest-parity contract | Aggregation contract traced; dual downstream contract = `VALID USSY DEFINITION` | T0 decision semantics traced; T+1 realistic execution path documented | **OPEN — exact legacy baseline to record** | Compare legacy aggregation/entry contract directly; do not silently unify alert and position-entry contracts |

## C01 evidence note — canonical adjusted EMA migration

C01 is closed using repository evidence rather than the current contents of `feature_engine.py` alone.

The legacy feature engine still contains raw-close EWM calculations. That implementation remains relevant for historical/research rows and as the pre-migration baseline, but it no longer defines the terminal production EMA contract.

Production migration commit `f35c3fb0376b7342e73efe7a55419a1fb30a07f9` (`Migrate TrendFoll to canonical shared adjusted EMA`) established the governed shared `adj_close` EMA20/50/150/200 terminal state with long-history bootstrap, recursive persisted updates, READY-lineage/equivalence validation, and terminal stack `adj_close > EMA20 > EMA50 > EMA150 > EMA200`.

**C01 final Core action: `RETAIN`.** Historical raw-close/finite-window representation is separate Extended engineering/research consistency work.

## C02 evidence note — Stage Analysis

Repository history for `feature_engine.py` shows only the original file commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` (2026-08-01) for this path. Its `compute_weekly_stage_features()` implementation is mechanically the same Stage contract present on the audit branch:

- daily `close_raw` -> `W-FRI` last close;
- rolling SMA30w;
- three-point monotonic SMA slope classification;
- Stage2/Stage4/Stage3 mapping followed by Stage1 fallback.

Unlike C01, no separate canonical Stage migration/terminal override was identified. Therefore C02 is not a legacy-vs-current drift problem: the legacy definition is the current definition.

Temporal correctness has separate regression coverage in `tests/test_weekly_stage_temporal.py`. The tests establish that backward-as-of consumption prevents Monday–Thursday rows from seeing the still-future Friday-labelled weekly bucket, and explicitly cover Friday and Monday holiday edge cases.

The remaining caveat is semantic rather than mechanical: this formula is a simplified stage classifier. It should not be documented as though it captures the complete Weinstein Stage Analysis methodology.

**C02 final Core action: `RETAIN + REDOCUMENT`.** No production formula correction is indicated by the legacy comparison.

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

1. C01 closed: legacy finite raw-close EMA -> current canonical long-history adjusted-close EMA; action `RETAIN`.
2. C02 closed: Stage formula unchanged from original repository implementation; action `RETAIN + REDOCUMENT` as a Weinstein-inspired approximation.
3. Recover exact legacy Relative Strength contract and trace current RS consumer path for C03.
4. Continue C04–C10 using repository history/code rather than assuming visible legacy code equals current behavior.
5. Compare changed outputs mechanically where practical.
6. Close each remaining Core row with one action: `RETAIN`, `RENAME / REDOCUMENT`, `CORRECT`, or `RESEARCH SEPARATELY`.
7. Produce one concise final Legacy-vs-Current conclusion before optional Extended Engineering backlog resumes.

Production remains untouched throughout this Core audit.