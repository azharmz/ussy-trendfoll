# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / C01-C04 REVIEW GATE PASS / C01-C07 CLOSED / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

Extended engineering audit: `docs/FULL_SIGNAL_ENGINE_AUDIT_PROGRESS.md`

Evidence/findings register: `docs/FULL_SIGNAL_ENGINE_AUDIT.md`

## Purpose

This is the primary primitive/component track for the signal-engine correctness question:

> Are the indicators used by current USSY TrendFoll valid for their stated purpose, how do they differ from the legacy engine, and are those differences material to trading decisions?

Core does **not** replace the Full Signal Engine Audit. Core establishes primitive calculations and their semantics. Full Audit retains the end-to-end objective of proving the actual composition and decision path from R2 READY through features, filters, Investability, Tradability, candidate/watchlist, alert, and actionable output.

Audit and remediation remain separate. A finding can justify a correction action without authorizing a production change.

## Completion rule

For each production-relevant component, close these questions:

1. What did legacy use?
2. What does current actually execute?
3. Is the current formula implemented as intended?
4. Is the stated interpretation supported by what the formula actually measures?
5. Is the signal temporally causal at T0 close / executable under the governed T+1 model where relevant?
6. Is the difference from legacy material to screening/trading decisions?
7. Final verdict and action: retain, rename/re-document, correct, or research separately.

Controlled verdicts: `MATCH`, `VALID USSY DEFINITION`, `APPROXIMATION`, `MISMATCH`, `BUG`, `NEEDS_EVIDENCE`, `DEAD / UNUSED`.

## Core progress

- [x] C01 Trend / EMA
- [x] C02 Stage Analysis
- [x] C03 Relative Strength vs SPY
- [x] C04 Liquidity
- [x] C05 Price floor
- [x] C06 ATR / volatility tightness
- [x] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 7 / 10. C01-C04 independent review gate: PASS.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `VALID USSY DEFINITION` for current production terminal contract. | T0 causal. | **CLOSED / CHANGED.** | **RETAIN.** |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope; compact Stage1–4 mapping. | `APPROXIMATION` | PASS / causal. | **CLOSED / MATCH.** | **RETAIN + REDOCUMENT.** |
| C03 | RS vs SPY | 63-session adjusted-close stock return minus same-basis SPY return; PASS >=0, NEAR >=-0.02. | `VALID USSY DEFINITION` as 63-session excess return vs SPY. | PASS / causal. | **CLOSED / MATCH.** | **RETAIN.** |
| C04 | Liquidity | Raw share-volume rolling mean 50/min20; PASS >=300k, NEAR >=240k. | `MISMATCH` in split-sensitive windows. | Raw formula causal; correction must be as-of causal. | **CLOSED / MATCH.** | **CORRECT under FSE-014 governance.** |
| C05 | Price floor | T0 nominal `close_raw`: PASS >=$10, NEAR >=$8. | `VALID USSY DEFINITION`; thresholds `NEEDS_EVIDENCE`. | PASS / T0 causal. | **CLOSED / MATCH.** | **RETAIN.** |
| C06 | ATR / volatility tightness | Raw-OHLC ATR14; inverse 63d ATR-level percentile called `vcp_tightness`; tight >=60. | ATR split-sensitive `MISMATCH`; VCP label `MISMATCH`. | PASS / causal. | **CLOSED / MATCH.** | **CORRECT ATR basis separately + RENAME/REDOCUMENT VCP proxy.** |
| C07 | Pivot / breakout | `pivot_high(t)=max(high_raw[t-59:t])` with min20; decision layer shifts per symbol so `prev_pivot_high(t)=pivot_high(t-1)`; `has_breakout(t)=close_raw(t)>prev_pivot_high(t)`. | `pivot_high` as generic trailing-high/resistance proxy: `VALID USSY DEFINITION`; as O'Neil/base pivot: `MISMATCH`. `has_breakout` as close above prior 60-session trailing high: `VALID USSY DEFINITION`. | **PASS / T0 causal.** Current T0 high cannot enter the reference because Tradability shifts the pivot one row. Signal is known after T0 close and executable T+1 under governed model. | **CLOSED / MATCH.** Original feature and decision layers contain identical rolling-high, shift, and breakout logic. No R2 pivot override exists. | **RENAME / REDOCUMENT, not formula-correct by default.** Preserve if intended rule is 60-session trailing-high breakout; do not call it an O'Neil/base pivot without a separately validated morphology detector. 60/min20 rationale remains `NEEDS_EVIDENCE / RESEARCH SEPARATELY`. |
| C08 | Breakout volume | Raw volume percentile in rolling 50 including current; confirmation >=80. | `APPROXIMATION` | T0 causal | **OPEN** | Sep-14 incident upstream; audit formula/consumer next. |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime. | `VALID USSY DEFINITION` | Backward-as-of. | **OPEN** | Preserve consumer distinction. |
| C10 | Investability / Tradability | Non-compensatory structural vs entry-timing contracts plus separate production-entry parity contract. | Pending final aggregation audit. | T0 / T+1 governed. | **OPEN** | Compare full downstream contracts. |

## C01-C04 independent review gate

**PASS.** C04 remediation remains governed separately.

## C05 evidence note — nominal price floor

Original and current hard filters use identical `close_raw` and $10/$8 thresholds. Current R2 maps READY `close` to `close_raw`; no price-floor overlay exists. This is intentionally a nominal-dollar rule, not an analytical return series. It is T0 causal and material through Investability and hard-filter position entry.

**C05 final verdict: `MATCH` legacy-current + `VALID USSY DEFINITION`; action `RETAIN`.** Threshold rationale remains separate research.

## C06 evidence note — ATR14 and volatility tightness

Legacy and current are mechanically identical. ATR true range uses raw high/low/previous close and Wilder-style EWM; `vcp_tightness` is only `100 - atr_percentile_63d`. The raw ATR state is corporate-action sensitive and materially affects stop distance. The VCP name overstates an inverse ATR-level percentile that does not detect contraction sequences.

**C06 final:** `MATCH` legacy-current; **CORRECT** split-sensitive ATR basis/state under separate governance; **RENAME/REDOCUMENT** VCP field as volatility-tightness proxy. No production change.

## C07 evidence note — pivot and breakout

### Actual formula and current execution

`feature_engine.compute_structure_features()` computes `pivot_high` as the rolling maximum of raw daily high over 60 rows with `min_periods=20`. Because this primitive includes the current row, `pct_from_pivot` on that same row is not itself an actionable breakout test.

The actual consumer is `decision_layer.compute_tradability()`. After sorting by symbol/date, it creates `prev_pivot_high = groupby(symbol).pivot_high.shift(1)` and defines `has_breakout = prev_pivot_high.notna() & (close_raw > prev_pivot_high)`. Algebraically, the T0 reference is therefore the maximum raw high over the prior up-to-60-session window ending T-1, not a maximum that includes T0. This removes the obvious self-comparison problem where T0 close could never exceed T0 high.

Current R2 production changes the stock OHLCV source but leaves structure formulas and decision-layer pivot consumption unchanged; the only terminal feature override in the R2 adapter is EMA. No pivot migration/override was found.

### Legacy comparison

The original repository commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` contains the identical `high_raw.rolling(60,min_periods=20).max()` primitive and the identical per-symbol one-row shift before comparing T0 `close_raw`. Therefore there is no legacy-current regression or semantic drift in C07.

### Semantics

Two interpretations must be separated.

As a **generic trailing-high resistance/breakout rule**, the implementation is coherent: T0 closes above every raw high represented in the prior rolling reference window. Raw price is appropriate for the contemporaneous chart-level breakout rule, subject to the usual fact that corporate actions can reset nominal chart levels; Core does not silently substitute adjusted prices here.

As an **O'Neil/base pivot**, the implementation is not sufficient. A rolling 60-session maximum does not identify a validated base, handle, double-bottom, flat-base, cup, or other morphology and does not establish the chart-specific buy point. FSE-003 therefore remains supported. The correct response is semantic separation, not automatic formula tuning: call this a `60-session trailing-high breakout` (or equivalent) unless a separately validated base/pivot detector is intentionally integrated.

The 60-session lookback and `min_periods=20` are implementation choices whose optimality is not established by Core. They remain methodology research questions rather than implementation bugs.

### Temporal correctness

The breakout decision is T0 causal. Although `pivot_high(t)` contains T0, Tradability never compares T0 close to that same primitive. It compares T0 close to `pivot_high(t-1)`, which contains only observations available through T-1. T0 close is known at the signal close; no T+1 value is used. Under the governed execution contract, an actionable T0 signal can therefore be executed at T+1 Open.

### Materiality and consumers

`has_breakout` is a hard gate in Tradability: without it, Tradability is FAIL regardless of volume/tightness. It is also a direct condition of the production position-registration contract together with hard-filter PASS and volume confirmation. Therefore the primitive/consumer semantics are materially production-relevant.

### C07 disposition

- Legacy vs current: **`MATCH`**.
- `pivot_high` as 60-session trailing-high/resistance proxy: **`VALID USSY DEFINITION`**.
- `pivot_high` interpreted as O'Neil/base pivot: **`MISMATCH`**.
- `has_breakout` as T0 close above prior trailing-high reference: **`VALID USSY DEFINITION`**.
- Temporal causality: **PASS**.
- Materiality: **YES** — hard gate for Tradability and direct production-entry condition.
- Action: **`RENAME / REDOCUMENT`** the semantics; preserve the formula if the intended strategy primitive is trailing-high breakout. Do not silently replace it with O'Neil morphology and do not tune 60/min20 during Core.

**C07 CLOSED. Production remains unchanged.**

## Existing deep evidence retained

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: effective-date lifecycle technical validation closed; production decision separate.
- Evidence 11: corporate-action semantics for RS, liquidity, nominal price; C06 separately identified ATR basis risk.
- Evidence 12: Sep-14 partial-volume incident upstream and closed/verified under its incident scope.
- Evidence 13: FSE-014 split-normalized share-liquidity correction spec frozen; production adoption separate.

## Scope boundary

Core proves primitive/core components. Full Audit remains responsible for composition and actual end-to-end decision semantics. Remediation remains separate.

## Next execution sequence

1. C01-C04 independent review gate: **PASS**.
2. C05: **CLOSED / RETAIN**.
3. C06: **CLOSED / CORRECT ATR split-sensitive basis separately + RENAME/REDOCUMENT VCP proxy**.
4. C07: **CLOSED / RENAME-REDOCUMENT pivot semantics; trailing-high breakout retained**.
5. Resume C08 Breakout Volume Confirmation from actual legacy/current execution path.
6. Continue C09-C10 sequentially.
7. Stop before production remediation requiring separate governed decision.
8. After C10, return to Full Audit composition/end-to-end objective.

Production remains untouched throughout this Core audit.