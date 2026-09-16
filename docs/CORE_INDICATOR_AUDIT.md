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

Current evidence closes the formula/semantic classification for most components, but the **exact legacy-vs-current comparison is not yet complete component-by-component**. Therefore no legacy value is inferred where the existing audit evidence does not establish it.

- [ ] C01 Trend / EMA
- [ ] C02 Stage Analysis
- [ ] C03 Relative Strength vs SPY
- [ ] C04 Liquidity
- [ ] C05 Price floor
- [ ] C06 ATR / volatility tightness
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 0 / 10 final legacy-vs-current verdicts.**

This does not mean prior audit work is incomplete or discarded. It means the new denominator requires an explicit legacy comparison before a component receives its final Core verdict.

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Terminal canonical EMA20/50/150/200 uses governed `adj_close` state; historical feature rows retain legacy raw-close EWM basis | Terminal: `MATCH` / `VALID USSY DEFINITION`; historical-vs-terminal basis: `MISMATCH` | T0 causal | **OPEN — exact legacy baseline to record** | Quantify whether basis difference changes historical classifications; do not treat terminal production state as invalid merely because research history differs |
| C02 | Stage Analysis | Weekly close vs SMA30w plus three-observation MA slope mapped to Stage1–4 | `APPROXIMATION` | Weekly W-FRI + backward-as-of verified causal | **OPEN — exact legacy baseline to record** | Decide whether current field should remain explicitly Weinstein-inspired approximation; no automatic rebuild required |
| C03 | RS vs SPY | 63-session stock `adj_close` return minus SPY 63-session return; PASS >=0, NEAR >=-0.02 | `VALID USSY DEFINITION`; horizon/threshold rationale still `NEEDS_EVIDENCE` | Exact-date benchmark merge; causal when benchmark available | **OPEN — exact legacy baseline to record** | Corporate-action basis is appropriate; compare legacy horizon/threshold before deciding change |
| C04 | Liquidity | 50-session mean raw share volume, min 20; PASS >=300k, NEAR >=240k | `MISMATCH` around split-sensitive windows; threshold rationale separately open | T0 causal; corporate-action unit consistency defect identified | **OPEN — exact legacy baseline to record** | FSE-014 correction spec is already frozen; keep remediation in Extended track rather than blocking all Core components |
| C05 | Price floor | Raw close >=$10 PASS; >=$8 NEAR | `VALID USSY DEFINITION`; threshold rationale `NEEDS_EVIDENCE` | T0 close causal | **OPEN — exact legacy baseline to record** | Retain as nominal-price rule unless legacy/evidence comparison supports change |
| C06 | ATR / volatility tightness | ATR14 plus `vcp_tightness = 100 - ATR percentile(63)` | ATR: `MATCH`; VCP label: `MISMATCH` with literal VCP morphology | T0 causal | **OPEN — exact legacy baseline to record** | Strong candidate for rename/re-document as volatility-tightness proxy rather than rebuilding VCP inside this audit |
| C07 | Pivot / breakout | Pivot proxy = rolling raw high 60, min20; Tradability compares T0 close with shifted prior-row pivot | Pivot-as-O'Neil semantics: `MISMATCH`; rolling-high breakout: `VALID USSY DEFINITION` | Breakout T0 is causal; executable after T0 close | **OPEN — exact legacy baseline to record** | Decide intended label: rolling-high/Donchian-like breakout vs chart-base pivot; avoid silently claiming O'Neil pivot |
| C08 | Breakout volume | Current raw volume percentile in rolling 50 including current; confirmation >=80 | `APPROXIMATION` | T0 causal | **OPEN — exact legacy baseline to record** | FSE-015 proved Sep-14 mass anomaly was upstream incomplete volume, not percentile-formula failure; compare legacy semantics before changing formula |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime; excluded from Investability but included in hard-filter contract | `MATCH` architecture / `VALID USSY DEFINITION` | Backward-as-of; empirical freshness audit passed | **OPEN — exact legacy baseline to record** | Preserve distinction between Investability and hard-filter consumers |
| C10 | Investability / Tradability | Investability = Trend + Liquidity + RS + Price non-compensatory aggregation; Tradability = breakout + volume confirmation + tightness; production position entry intentionally retains separate backtest-parity contract | Aggregation contract traced; dual downstream contract = `VALID USSY DEFINITION` | T0 decision semantics traced; T+1 realistic execution path documented | **OPEN — exact legacy baseline to record** | Compare legacy aggregation/entry contract directly; do not silently unify alert and position-entry contracts |

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

1. Recover exact legacy formulas/contracts from repository history/code rather than memory.
2. Fill legacy column for C01–C10.
3. Compare current vs legacy mechanically and identify changed outputs where practical.
4. Close each Core row with a final verdict and one action: `RETAIN`, `RENAME / REDOCUMENT`, `CORRECT`, or `RESEARCH SEPARATELY`.
5. Produce one concise final Legacy-vs-Current conclusion before any optional Extended Engineering backlog is resumed.

Production remains untouched throughout this Core audit.