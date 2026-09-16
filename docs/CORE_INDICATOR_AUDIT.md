# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / C01-C04 REVIEW GATE PASS / C01-C08 CLOSED / NO PRODUCTION CHANGE**

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
- [x] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 8 / 10. C01-C04 independent review gate: PASS.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `VALID USSY DEFINITION` | T0 causal. | **CLOSED / CHANGED.** | **RETAIN.** |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope. | `APPROXIMATION` | PASS / causal. | **CLOSED / MATCH.** | **RETAIN + REDOCUMENT.** |
| C03 | RS vs SPY | 63-session adjusted-close stock return minus same-basis SPY return. | `VALID USSY DEFINITION` | PASS / causal. | **CLOSED / MATCH.** | **RETAIN.** |
| C04 | Liquidity | Raw share-volume rolling mean 50/min20. | Split-sensitive `MISMATCH`. | Causal; correction must remain as-of causal. | **CLOSED / MATCH.** | **CORRECT under FSE-014 governance.** |
| C05 | Price floor | T0 nominal `close_raw`: PASS >=$10, NEAR >=$8. | `VALID USSY DEFINITION`; thresholds `NEEDS_EVIDENCE`. | PASS. | **CLOSED / MATCH.** | **RETAIN.** |
| C06 | ATR / volatility tightness | Raw-OHLC ATR14; inverse 63d ATR-level percentile called `vcp_tightness`. | ATR split-sensitive `MISMATCH`; VCP label `MISMATCH`. | PASS. | **CLOSED / MATCH.** | **CORRECT ATR separately + RENAME/REDOCUMENT VCP proxy.** |
| C07 | Pivot / breakout | Prior-row shifted rolling raw high 60/min20; T0 close breakout. | Valid trailing-high breakout; not O'Neil/base pivot. | PASS. | **CLOSED / MATCH.** | **RENAME / REDOCUMENT.** |
| C08 | Breakout volume confirmation | `breakout_volume_percentile(t)=100*mean(volume_raw(window<=50 ending t) <= volume_raw(t))`, min20; confirmation when percentile >=80. Current observation is deliberately part of the empirical distribution. | `VALID USSY DEFINITION` as a contemporaneous **rolling volume-rank confirmation**; `APPROXIMATION` if described as O'Neil-style volume confirmation or volume expansion versus prior average. It is not a historical-only percentile because T0 is included. Raw-volume split-unit caveat inherits C04/FSE-014. | **PASS / T0 causal.** Uses T0 and prior volume only; no future data. T0 inclusion is a semantic design choice, not look-ahead. | **CLOSED / MATCH.** Original feature and decision layers contain identical percentile formula and >=80 consumer threshold. R2 adapter does not override volume features. | **RENAME / REDOCUMENT + inherit FSE-014 correction governance.** Preserve formula if intended primitive is rolling rank. Do not call it canonical/O'Neil volume confirmation. 50/min20/80 rationale remains `NEEDS_EVIDENCE / RESEARCH SEPARATELY`; no tuning in Core. |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime. | `VALID USSY DEFINITION` | Backward-as-of. | **OPEN** | Preserve consumer distinction. |
| C10 | Investability / Tradability | Non-compensatory structural vs entry-timing contracts plus separate production-entry parity contract. | Pending final aggregation audit. | T0 / T+1 governed. | **OPEN** | Compare full downstream contracts. |

## C01-C04 independent review gate

**PASS.** C04 remediation remains governed separately.

## C05-C07 disposition summary

C05 nominal price floor: `MATCH + VALID USSY DEFINITION -> RETAIN`. C06: legacy-current `MATCH`, but raw ATR state is split-sensitive and the VCP label overstates an inverse ATR-level percentile; correction/rename is separately governed. C07: legacy-current `MATCH`; valid trailing-high breakout, not an O'Neil/base pivot; rename/redocument rather than silently replacing the strategy primitive.

## C08 evidence note — breakout volume confirmation

### Actual formula and current execution

`feature_engine.compute_volume_features()` sorts each symbol by date and computes `breakout_volume_percentile` with a rolling 50-session window (`min_periods=20`). For each window the value is:

`100 * mean(window_volume <= current_window_last_volume)`.

Because the last element is T0 itself, T0 is always counted and the theoretical minimum for a full 50-row window is 2%. The metric is therefore an empirical rank of today's raw share volume among the up-to-50 observations ending today. It is not a percentile against an exclusively T-1-and-earlier reference sample.

`decision_layer.compute_tradability()` defines `has_volume_confirmation = breakout_volume_percentile >= 80`. This confirmation affects Tradability PASS/NEAR_PASS. The same boolean is also a direct production position-registration condition together with hard-filter PASS and breakout, so C08 is materially production-relevant.

The current R2 adapter injects READY stock OHLCV into the legacy feature builder and only overlays terminal EMA. It does not replace volume features. Therefore the current production C08 formula is the feature-engine formula above.

### Legacy comparison

Original commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` contains the identical rolling-50/min20 percentile formula. Its original `decision_layer.py` also uses the identical default threshold `volume_percentile_threshold=80` and boolean comparison. There is no legacy-current drift.

### Semantic interpretation

As a **rolling volume-rank confirmation**, the primitive is mathematically coherent. A value >=80 says T0 raw volume ranks at or above roughly the upper fifth of the recent empirical window under the implementation's inclusive-rank convention.

It is not equivalent to a historical-only percentile, because T0 participates in its own reference distribution. This does not create future leakage; it changes the exact statistic being measured. It is also not equivalent to O'Neil-style breakout-volume semantics such as explicit percentage expansion versus average/normal volume. FSE-004's `APPROXIMATION` classification therefore remains valid whenever the field is interpreted as canonical/O'Neil volume confirmation.

The clean documentation name should communicate what is actually measured, e.g. `rolling_volume_rank_50d` / `high_recent_volume_rank`, while `has_volume_confirmation` should be understood as a USSY confirmation rule built from that proxy rather than a claim of authoritative O'Neil semantics.

### Temporal correctness

C08 is T0 causal. The rolling window ends at T0 and contains no future observation. T0 volume is only finalized/knowable after the session close, consistent with the T0-close signal contract and T+1 execution model.

The Sep-14 partial-volume incident does not invalidate this temporal formula. Evidence 12 showed the mass 2% population was caused by incomplete upstream READY T0 volume. After finalized upstream data and targeted historical repair, the same unchanged TrendFoll percentile diagnostic returned to a normal population. Evidence 12 therefore supports the distinction between formula semantics and source-data completeness.

### Corporate-action interaction

C08 uses the same raw share-volume basis implicated by C04/FSE-014. A split changes share units, so a 50-session rank spanning pre/post split observations can compare raw share counts expressed in different units. Rank statistics are less directly scale-sensitive than an arithmetic mean only when the scale is common; across a share-unit discontinuity, ordering itself can change mechanically. Therefore C08 inherits the FSE-014 corporate-action correction dependency. Core does not create a second competing correction formula: any adopted normalized T0-basis share-volume series should be evaluated consistently for both average-liquidity and rolling-rank consumers.

### Threshold/methodology boundary

Core establishes what >=80 means mechanically but does not establish that 80, 50 sessions, or min20 is empirically optimal for the USSY universe/horizon. Those are `NEEDS_EVIDENCE / RESEARCH SEPARATELY` questions. No threshold or lookback tuning is performed here.

### C08 disposition

- Legacy vs current formula/threshold: **`MATCH`**.
- Rolling inclusive volume-rank primitive: **`VALID USSY DEFINITION`**.
- As canonical/O'Neil breakout-volume confirmation: **`APPROXIMATION`**.
- Historical-only percentile interpretation: **not the implemented statistic**; T0 is included by design.
- Temporal causality: **PASS**.
- Data-completeness incident: **upstream Sep-14 incident closed/verified; no formula correction supported by that incident**.
- Corporate-action robustness: **inherits C04/FSE-014 split-unit correction dependency**.
- Materiality: **YES** — affects Tradability tier and is a direct production-entry condition.
- Action: **`RENAME / REDOCUMENT` + evaluate under FSE-014 normalized-volume remediation if/when that correction is adopted.** Do not tune 80/50/min20 during Core.

**C08 CLOSED. Production remains unchanged.**

## Existing deep evidence retained

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: effective-date lifecycle technical validation closed; production decision separate.
- Evidence 11: corporate-action semantics.
- Evidence 12: Sep-14 partial-volume incident; upstream prevention and residual repair verified; no TrendFoll percentile formula correction supported.
- Evidence 13: FSE-014 split-normalized share-liquidity correction spec frozen; production adoption separate. C08 should be regression-tested against the same normalized share-volume basis if that remediation proceeds.

## Scope boundary

Core proves primitive/core components. Full Audit remains responsible for composition and actual end-to-end decision semantics. Remediation remains separate.

## Next execution sequence

1. C01-C04 independent review gate: **PASS**.
2. C05-C08: **CLOSED** under dispositions above.
3. Resume C09 Market Regime from actual benchmark ingestion, formula, temporal merge, legacy/current history, and downstream consumers.
4. Continue C10 aggregation/consumer-contract audit.
5. Stop before production remediation requiring separate governed decision.
6. After C10, return to Full Audit composition/end-to-end objective.

Production remains untouched throughout this Core audit.