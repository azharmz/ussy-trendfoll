# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / C01-C04 REVIEW GATE PASS / C05 CLOSED / NO PRODUCTION CHANGE**

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
- [ ] C06 ATR / volatility tightness
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 5 / 10. C01-C04 independent review gate: PASS. C05 closed independently.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `VALID USSY DEFINITION` for the current production terminal contract. Historical/local raw-close finite-window EMA is a separate consistency/debt issue. | T0 causal; READY-lineage/as-of governed. | **CLOSED / CHANGED.** Legacy finite `EMA(close_raw)` -> current canonical recursive `EMA(adj_close)`. | **RETAIN.** Migration evidence supports the current production terminal contract. |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope; compact Stage1–4 mapping. | `APPROXIMATION` | **PASS / causal**, with a conservative holiday-week visibility lag when Friday is not a session. | **CLOSED / MATCH.** Same formula exists in original repository implementation and current path. | **RETAIN + REDOCUMENT** as Weinstein-inspired approximation. |
| C03 | RS vs SPY | 63-session adjusted-close stock return minus same-basis SPY return; PASS >=0, NEAR >=-0.02. | `MATCH` legacy-current / `VALID USSY DEFINITION` as 63-session excess return vs SPY. | **PASS / causal.** | **CLOSED / MATCH.** Same formula and thresholds in original repository state. | **RETAIN.** Horizon/threshold rationale remains separate research question. |
| C04 | Liquidity | Current production still uses `rolling_mean(volume_raw, 50, min_periods=20)`; PASS >=300k, NEAR_PASS >=240k. | `MISMATCH` in split-sensitive windows for intended average-share-liquidity semantics. | Raw rolling calculation is T0-causal; frozen correction is explicitly as-of causal. | **CLOSED / MATCH legacy-current.** The defect is inherited, not a new regression. | **CORRECT under FSE-014 governance.** Finding/action is supported; research prototype/test success does not itself authorize production adoption. |
| C05 | Price floor | Current hard filter classifies the same-day nominal `close_raw`: PASS >= $10, NEAR_PASS >= $8, otherwise FAIL. R2 READY `close` maps directly to `close_raw`; no downstream price-floor override exists. | `VALID USSY DEFINITION` as a nominal share-price eligibility rule. The exact $10/$8 cutoffs remain `NEEDS_EVIDENCE` as methodology/threshold choices, not implementation defects. | **PASS / T0 causal.** Uses only T0 nominal close; no future data or rolling lookahead. | **CLOSED / MATCH.** Original repository hard filter uses the identical `close_raw` input and $10/$8 thresholds. | **RETAIN.** Raw/unadjusted close is intentional for a nominal-dollar price floor; do not convert this rule to adjusted close. Threshold optimization, if desired, is separate research. |
| C06 | ATR / volatility tightness | ATR14 plus `vcp_tightness = 100 - ATR percentile(63)` | ATR: `MATCH`; VCP label: `MISMATCH` with literal VCP morphology | T0 causal | **OPEN** | Strong candidate for rename/re-document as volatility-tightness proxy |
| C07 | Pivot / breakout | Pivot proxy = rolling raw high 60, min20; Tradability compares T0 close with shifted prior-row pivot | Pivot-as-O'Neil semantics: `MISMATCH`; rolling-high breakout: `VALID USSY DEFINITION` | Breakout T0 causal | **OPEN** | Decide intended label; avoid silently claiming O'Neil pivot |
| C08 | Breakout volume | Raw volume percentile in rolling 50 including current; confirmation >=80 | `APPROXIMATION` | T0 causal | **OPEN** | Sep-14 incident was upstream incomplete volume, not percentile-formula failure |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime; excluded from Investability but included in hard-filter contract | `MATCH` architecture / `VALID USSY DEFINITION` | Backward-as-of; empirical freshness audit passed | **OPEN** | Preserve consumer distinction |
| C10 | Investability / Tradability | Investability = Trend + Liquidity + RS + Price non-compensatory; Tradability = breakout + volume confirmation + tightness; position entry intentionally retains separate backtest-parity contract | Dual downstream contract currently documented as `VALID USSY DEFINITION` | T0 decision / T+1 realistic execution traced | **OPEN** | Compare legacy aggregation/entry contract directly |

## C01 evidence note — canonical adjusted EMA migration

Production workflow runs `r2_main.py`, which obtains features through `build_feature_store_from_r2()`. The R2 adapter first executes the legacy feature formulas and then unconditionally calls `apply_shared_ema_terminal()` before returning the feature frame. The migration validates READY lineage, terminal date, security/ticker mapping, adjusted last price, and governed shared-state equivalence before replacing terminal EMA20/50/150/200 and `ema_stack_aligned`.

Migration commit `f35c3fb0376b7342e73efe7a55419a1fb30a07f9` records a 1,226-security shadow: 16 stack changes, 15 Trend changes, 5 Hard Filter changes, 5 Investability changes, 5 candidate changes, 0 Tradability changes, and 0 Actionable changes. Production position registration and current-day exit checks consume `latest` after this terminal override, so no material current-day production decision path identified in the review bypasses canonical terminal EMA.

Review clarification: because legacy and current EMA are deliberately different, `MATCH` is not used as the legacy-current comparison verdict for C01. The supported semantic conclusion is `VALID USSY DEFINITION`, action `RETAIN`. Historical/local EMA consistency remains outside the primitive current-terminal verdict.

**C01 review verdict: SUPPORTED, with documentation wording revised to remove ambiguous `MATCH` usage.**

## C02 evidence note — Stage Analysis

Original and current `feature_engine.py` use the same W-FRI / SMA30w / three-observation slope / Stage1–4 mapping. No Stage overlay analogous to shared EMA was found; the R2 adapter explicitly leaves all non-EMA formulas to `feature_engine.build_feature_store()`.

`tests/test_weekly_stage_temporal.py` checks W-FRI semantics, Monday-Thursday non-visibility of the future Friday bucket, Good-Friday behavior, and Monday-holiday behavior. The review notes a test-quality limitation: most temporal assertions reconstruct the resample/as-of mechanism rather than calling the full production function end-to-end. This does not overturn the conclusion because the production implementation itself uses the same W-FRI weekly table and backward `merge_asof`, but future test hardening could exercise the function output directly. A Friday market holiday causes the Thursday close to become visible only after the Friday-labelled bucket is in the past; this is conservative lag, not future leakage.

**C02 review verdict: SUPPORTED.** Action remains `RETAIN + REDOCUMENT`.

## C03 evidence note — Relative Strength vs SPY

The original and current feature contracts use `RS_LOOKBACK_DAYS = 63` and adjusted-close returns. Current R2 maps READY `adj_close` to `close_adj` and reuses the feature engine for RS; there is no RS terminal override. Hard-filter thresholds remain PASS >=0 and NEAR_PASS >=-0.02. The benchmark merge is date-based and causal; no future benchmark value is used to fill T0.

Corporate-action evidence supports adjusted return as the analytical basis, but does not prove that 63 sessions or the -2pp near band is optimal. Therefore implementation correctness and methodology optimization remain separated.

**C03 review verdict: SUPPORTED.** Action remains `RETAIN`, with the precise name `63-session excess return versus SPY`.

## C04 evidence note — Liquidity

Original and current TrendFoll both calculate `avg_volume_50d` from the raw `volume_raw` series with window 50/min20 and unchanged 300k/240k thresholds. Current R2 maps READY `volume` directly to `volume_raw`; `to_feature_contract()` deliberately sets `stock_splits=0.0`, so TrendFoll production has no split-factor information and no split-normalization overlay.

Independent upstream trace confirms the historical `ussy-data` bootstrap obtained Yahoo data with `auto_adjust=False` and copied `Volume` directly into the governed OHLCV `volume` field. Thus the TrendFoll READY adapter is not secretly receiving an FSE-014-style normalized share-volume series.

The dimensional finding is sound: a split changes the share unit, so an arithmetic mean spanning pre/post split raw share counts can mechanically change even with continuous underlying activity. The frozen correction preserves share-liquidity semantics while converting prior observations to each T0 share basis using explicit share-changing factors. It is as-of causal and rejects future-event back-propagation.

The research prototype has direct contract tests for no-split identity, 2-for-1, reverse split, multiple splits, outside-window split, min-period behavior, future-event non-leakage, unknown-factor fail-closed behavior, unaffected-status invariance, and a threshold-discontinuity example. The CI research gate passed. Review boundary: this validates the correction mechanics in research; it is not untouched-population validation and not production authorization.

**C04 review verdict: SUPPORTED.** Action remains `CORRECT` under FSE-014 governance; production remains unchanged.

## Independent C01-C04 review gate

Review performed against actual repository execution path, original repository state/history, tests, migration evidence, and upstream data semantics rather than accepting the prior Core document as authority.

| Component | Review verdict | Key independent result | Issue / caveat |
|---|---|---|---|
| C01 EMA | **SUPPORTED** | Daily production -> `r2_main.py` -> R2 feature adapter -> unconditional terminal canonical shared EMA override; downstream latest-day decisions consume the overridden state. | Prior wording `MATCH / VALID` was ambiguous because legacy and current are different. Revised to `VALID USSY DEFINITION`; historical/local EMA remains debt/consistency work. |
| C02 Stage | **SUPPORTED** | Legacy=current W-FRI/SMA30w/3-point-slope mapping; no Stage overlay found; backward-as-of prevents future-Friday leakage. | Temporal tests mostly reconstruct semantics instead of full-function output; holiday Friday creates conservative lag. Neither invalidates current verdict. |
| C03 RS vs SPY | **SUPPORTED** | Legacy=current adjusted-close 63-session excess return vs SPY with unchanged 0/-0.02 thresholds; R2 changes stock source, not formula. | Horizon and near-band are not independently optimized/validated; keep as separate methodology research. |
| C04 Liquidity | **SUPPORTED** | Legacy=current raw share-volume rolling mean; upstream READY volume is copied from unadjusted Yahoo Volume; no production split normalization exists. Split-unit defect and frozen causal correction are technically coherent. | Research contract tests pass, but this is not production adoption or untouched-population authorization. |

### Gate decision

**C01-C04 REVIEW GATE = PASS.**

No dependent Core conclusion was invalidated. One audit-record clarification was required and has been applied to C01: current EMA is not `MATCH` to legacy; it is a changed, validated current production definition. C02 test hardening is optional engineering work, not a blocker. C04 remediation remains governed separately and must not be silently promoted during Core Audit.

## C05 evidence note — nominal price floor

The original repository hard filter and current branch are byte-identical for the relevant contract: `THRESHOLDS['price'] = {'pass': 10.0, 'near_pass': 8.0}` and `price_status` is computed from the same row's `close_raw`. Current R2 ingestion maps governed READY `close` to `close_raw`, and the R2 adapter only overlays terminal EMA state; it does not replace nominal close or price status.

This rule is dimensionally different from analytical return/EMA features. It asks whether one share's observed market price at T0 is at least a nominal-dollar eligibility cutoff. Using adjusted close here would rewrite historical nominal prices after splits/dividends and would no longer represent the actual per-share quote that the rule claims to filter. Therefore raw close is the correct basis for the stated rule.

The consumer is material: `price_status` is one of the four non-compensatory Investability inputs and is also included in the five-factor hard filter used by the production position-entry contract. A FAIL can therefore block candidate eligibility/entry even when other criteria pass. That materiality does not imply the numerical cutoff is optimal.

No evidence in the Core audit establishes that $10 PASS or $8 NEAR_PASS is an empirically optimal threshold for this universe/horizon. That is a methodology/research question rather than an implementation correctness defect. Core therefore does not tune either cutoff.

Temporal verdict is straightforward: classification uses only same-row T0 `close_raw`, with no rolling window, future event, or T+1 value. It is causal at signal close; actual realistic execution remains governed separately at T+1 Open.

**C05 final verdict: `MATCH` legacy-current + `VALID USSY DEFINITION`; action `RETAIN`.** Threshold rationale remains `NEEDS_EVIDENCE / RESEARCH SEPARATELY` if optimization is ever desired. No production change.

## Existing deep evidence retained

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: FSE-013 effective-date lifecycle correction passed research contract/regression and untouched validation V2; production decision remains separate.
- Evidence 11: corporate-action semantics for RS, liquidity, and nominal price.
- Evidence 12: Sep-14 partial-volume incident; residual upstream repair handled separately and incident closed/verified.
- Evidence 13: FSE-014 split-normalized share-liquidity correction specification is frozen; research contract gate passed; production adoption remains separate.

## Scope boundary

Core proves primitive/core components. Full Audit remains responsible for composition and actual end-to-end decision semantics. Remediation remains a separate governed track.

## Next execution sequence

1. C01-C04 independent review gate: **PASS**.
2. C05 Price Floor: **CLOSED / RETAIN**.
3. Resume C06 ATR / volatility tightness from actual legacy/current execution path.
4. Continue C07-C10 sequentially.
5. For each: implementation -> actual consumer path -> legacy/current -> data semantics -> T0 causality -> implementation vs methodology -> materiality -> verdict/action -> evidence.
6. Stop before any production remediation/change that requires a separate governed decision.
7. After C10, Core completion does not automatically close Full Signal Engine Audit; return to the Full Audit terminal objective for composition/end-to-end correctness.

Production remains untouched throughout this Core audit.