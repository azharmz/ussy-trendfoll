# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / C01-C04 REVIEW GATE PASS / C01-C09 CLOSED / NO PRODUCTION CHANGE**

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
- [x] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 9 / 10. C01-C04 independent review gate: PASS.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Canonical terminal recursive EMA20/50/150/200 on `adj_close`. | `VALID USSY DEFINITION` | T0 causal. | CLOSED / CHANGED. | RETAIN. |
| C02 | Stage Analysis | W-FRI close, SMA30w, 3-observation slope proxy. | `APPROXIMATION` | PASS. | CLOSED / MATCH. | RETAIN + REDOCUMENT. |
| C03 | RS vs SPY | 63-session adjusted-close excess return vs SPY. | `VALID USSY DEFINITION` | PASS. | CLOSED / MATCH. | RETAIN. |
| C04 | Liquidity | Raw share-volume rolling mean 50/min20. | Split-sensitive `MISMATCH`. | Causal. | CLOSED / MATCH. | CORRECT under FSE-014 governance. |
| C05 | Price floor | T0 nominal raw close $10/$8. | `VALID USSY DEFINITION`; thresholds `NEEDS_EVIDENCE`. | PASS. | CLOSED / MATCH. | RETAIN. |
| C06 | ATR / volatility tightness | Raw ATR14 + inverse ATR percentile proxy. | ATR split-sensitive `MISMATCH`; VCP label `MISMATCH`. | PASS. | CLOSED / MATCH. | CORRECT ATR separately + RENAME/REDOCUMENT. |
| C07 | Pivot / breakout | T0 close above shifted prior 60-session trailing high. | Valid trailing-high breakout, not O'Neil pivot. | PASS. | CLOSED / MATCH. | RENAME / REDOCUMENT. |
| C08 | Breakout volume confirmation | Inclusive rolling 50-session raw-volume rank; confirm >=80. | `VALID USSY DEFINITION` as rolling rank; `APPROXIMATION` as O'Neil volume confirmation. | PASS. | CLOSED / MATCH. | RENAME/REDOCUMENT + inherit FSE-014 dependency. |
| C09 | Market regime | Live SPY raw close; SMA50/SMA200; Bullish if close>SMA50>SMA200, Bearish if close<SMA50<SMA200, else Neutral; stock rows consume latest benchmark state at or before stock date through backward `merge_asof`. | `VALID USSY DEFINITION` as an internal three-state SPY trend regime. It is not claimed as a canonical market-timing model. | **PASS for no-future leakage.** Backward-as-of cannot import a future benchmark row. Separate benchmark-vs-R2 freshness/readiness contract remains architectural evidence risk, not formula leakage. | **CLOSED / MATCH.** Original repository has identical SPY SMA50/200 classifier. Current R2 adapter intentionally retains live benchmark downloads and does not override regime. | **RETAIN + REDOCUMENT consumer boundary.** Regime belongs to portfolio-level context; it is included in legacy `hard_filter_status` but deliberately excluded from `investability_status`. Preserve/document that distinction. Governed benchmark ingestion/freshness remains separate Full-Audit hardening, not a C09 formula correction. |
| C10 | Investability / Tradability | Non-compensatory structural vs entry-timing contracts plus separate production-entry parity contract. | Pending final aggregation audit. | T0 / T+1 governed. | OPEN. | Compare full downstream contracts. |

## C01-C04 independent review gate

**PASS.** C04 remediation remains governed separately.

## C05-C08 disposition summary

C05 nominal price floor: `MATCH + VALID USSY DEFINITION -> RETAIN`. C06: raw ATR state is split-sensitive and VCP label overstates an inverse ATR percentile. C07: valid trailing-high breakout, not O'Neil/base pivot. C08: valid rolling volume rank, only an approximation of O'Neil-style volume confirmation and dependent on FSE-014 for split-unit robustness.

## C09 evidence note — market regime

### Actual current execution

The current R2 adapter is intentionally hybrid. It injects governed R2 READY OHLCV only for the stock universe, while `feature_engine.build_feature_store()` continues to call the legacy benchmark downloader for SPY, QQQ, VIX and sector ETFs. The adapter subsequently overlays terminal EMA only; there is no market-regime migration or override.

`compute_market_regime()` sorts SPY by date, calculates simple rolling SMA50 and SMA200 on SPY `close_raw`, and classifies each benchmark row:

- Bullish: `SPY close_raw > SMA50 > SMA200`;
- Bearish: `SPY close_raw < SMA50 < SMA200`;
- Neutral: every other evaluable ordering;
- unavailable until both moving averages exist.

For each stock, the benchmark regime table is joined with `pd.merge_asof(..., direction='backward')`. Thus a stock row dated T0 receives the latest regime observation whose benchmark date is <= T0.

### Legacy comparison

Original repository commit `94b78f008d0a003ed5cf37c53e3fd4253122c259` contains the same raw-SPY SMA50/SMA200 calculation and identical Bullish/Bearish/Neutral ordering. Current R2 production deliberately retains the legacy benchmark download/formula path. Therefore C09 has no legacy-current formula drift.

### Semantics

This is a coherent internal **SPY trend-regime classifier**. It measures the ordering of the current SPY price and two moving averages; it does not encode breadth, distribution days, follow-through days, macro state, volatility state, or a canonical O'Neil Market Direction model. Core therefore treats `market_regime` as a `VALID USSY DEFINITION` only under its explicit internal three-state semantics.

Raw SPY close is internally coherent here because the current price and both moving averages are computed from the same benchmark series. Core does not claim that this proves raw-price SMA is the only defensible benchmark basis; there is no corporate-action finding requiring a C09 correction from the evidence currently established.

### Temporal correctness and benchmark freshness boundary

The merge itself is causal: `direction='backward'` cannot use a future SPY regime row. If stock T0 is present while the benchmark downloader only has T-1, the stock receives T-1 regime rather than future information. That is stale-state risk, not look-ahead.

The architecture nevertheless has a distinct readiness/freshness boundary: stock facts come from governed R2 READY, while SPY/other benchmark facts are downloaded live through the legacy downloader. FSE-007 correctly records this as benchmark-ingestion evidence/hardening work. C09 does not collapse that architecture issue into a formula bug. The appropriate Full-Audit hardening is to keep proving/guarding benchmark date freshness and lineage relative to the common stock as-of date, or eventually govern benchmark state explicitly if approved.

### Consumer semantics

`hard_filter.compute_hard_filter()` maps Bullish -> PASS, Neutral -> NEAR_PASS, and Bearish/NaN -> FAIL, then includes `regime_status` among its five non-compensatory columns. Therefore regime can materially change `hard_filter_status`.

`decision_layer.compute_investability()`, however, intentionally uses only Trend, Liquidity, RS and Price. Its module contract explicitly states that Regime is a separate portfolio-level gate and `INVESTABILITY_COLS` excludes `regime_status`.

This is not accidental drift: it is the already-documented dual consumer architecture that C10 must verify end-to-end. C09's responsibility is to preserve the distinction rather than silently forcing regime into Investability or deleting it from hard filter.

### C09 disposition

- Legacy vs current formula: **`MATCH`**.
- Internal SPY price/SMA50/SMA200 three-state classifier: **`VALID USSY DEFINITION`**.
- Canonical/O'Neil market-direction interpretation: **not claimed / not established**.
- Temporal merge: **PASS / no future leakage**.
- Benchmark ingestion/readiness: **separate FSE-007 architectural hardening/evidence dependency**, not a C09 formula mismatch.
- Materiality: **YES** through `regime_status` in `hard_filter_status`; deliberately **NO direct membership in Investability**.
- Action: **`RETAIN + REDOCUMENT` the portfolio-level consumer boundary**. No formula or threshold tuning in Core.

**C09 CLOSED. Production remains unchanged.**

## Existing deep evidence retained

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- FSE-007: hybrid live benchmark vs governed R2-stock ingestion remains a Full-Audit evidence/hardening concern.
- FSE-009: Investability excludes regime while legacy hard filter includes it; C09 independently confirms this architecture.
- Evidence 10: effective-date lifecycle technical validation closed; production decision separate.
- Evidence 11: corporate-action semantics.
- Evidence 12: Sep-14 partial-volume incident closed/verified under incident scope.
- Evidence 13: FSE-014 split-normalized share-liquidity correction spec frozen; production adoption separate.

## Scope boundary

Core proves primitive/core components. Full Audit remains responsible for composition and actual end-to-end decision semantics. Remediation remains separate.

## Next execution sequence

1. C01-C04 independent review gate: PASS.
2. C05-C09: CLOSED under dispositions above.
3. Resume C10 Investability / Tradability aggregation from actual hard-filter, decision-layer, candidate/watchlist/actionability, and production-position consumers.
4. Compare legacy/current composition and explicitly verify the dual downstream contracts rather than assuming they are interchangeable.
5. Stop before production remediation requiring separate governed decision.
6. After C10, Core completion does not automatically close Full Audit; return to Full Audit composition/end-to-end objective.

Production remains untouched throughout this Core audit.