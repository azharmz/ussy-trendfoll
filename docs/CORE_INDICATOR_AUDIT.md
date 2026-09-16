# Core Indicator Audit — Legacy vs Current

Status: **ACTIVE PRIMARY AUDIT / C01-C04 REVIEW GATE PASS / C01-C06 CLOSED / NO PRODUCTION CHANGE**

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
- [ ] C07 Pivot / breakout
- [ ] C08 Breakout volume confirmation
- [ ] C09 Market regime
- [ ] C10 Investability / Tradability aggregation

**Core completion: 6 / 10. C01-C04 independent review gate: PASS.**

## Working matrix

| ID | Component | Current implementation established by audit | Current semantic verdict | Temporal status | Legacy comparison | Materiality / action |
|---|---|---|---|---|---|---|
| C01 | Trend / EMA | Current production terminal state is governed long-history recursive EMA20/50/150/200 on `adj_close`, consumed from shared `ussy-data` EMA state. | `VALID USSY DEFINITION` for the current production terminal contract. Historical/local raw-close finite-window EMA is a separate consistency/debt issue. | T0 causal; READY-lineage/as-of governed. | **CLOSED / CHANGED.** Legacy finite `EMA(close_raw)` -> current canonical recursive `EMA(adj_close)`. | **RETAIN.** Migration evidence supports the current production terminal contract. |
| C02 | Stage Analysis | W-FRI weekly `close_raw`; SMA30w; three-observation monotonic MA slope; compact Stage1–4 mapping. | `APPROXIMATION` | **PASS / causal**, with a conservative holiday-week visibility lag when Friday is not a session. | **CLOSED / MATCH.** Same formula exists in original repository implementation and current path. | **RETAIN + REDOCUMENT** as Weinstein-inspired approximation. |
| C03 | RS vs SPY | 63-session adjusted-close stock return minus same-basis SPY return; PASS >=0, NEAR >=-0.02. | `MATCH` legacy-current / `VALID USSY DEFINITION` as 63-session excess return vs SPY. | **PASS / causal.** | **CLOSED / MATCH.** Same formula and thresholds in original repository state. | **RETAIN.** Horizon/threshold rationale remains separate research question. |
| C04 | Liquidity | Current production still uses `rolling_mean(volume_raw, 50, min_periods=20)`; PASS >=300k, NEAR_PASS >=240k. | `MISMATCH` in split-sensitive windows for intended average-share-liquidity semantics. | Raw rolling calculation is T0-causal; frozen correction is explicitly as-of causal. | **CLOSED / MATCH legacy-current.** The defect is inherited, not a new regression. | **CORRECT under FSE-014 governance.** Finding/action is supported; research prototype/test success does not itself authorize production adoption. |
| C05 | Price floor | Current hard filter classifies same-day nominal `close_raw`: PASS >=$10, NEAR_PASS >=$8, otherwise FAIL. | `VALID USSY DEFINITION` as nominal share-price eligibility rule; exact cutoffs `NEEDS_EVIDENCE`. | **PASS / T0 causal.** | **CLOSED / MATCH.** Original and current contract identical. | **RETAIN.** Raw close is intentional for nominal-price rule. |
| C06 | ATR / volatility tightness | `ATR14` = Wilder-style EWM (`alpha=1/14`) of raw-price true range; `atr_pct = atr14/close_raw*100`; `atr_percentile_63d` ranks raw ATR level within rolling 63 incl. T0; `vcp_tightness = 100 - atr_percentile_63d`; Tradability calls tight when >=60. | **ATR formula: MATCH / valid ATR mechanics in ordinary no-action windows, but `MISMATCH` as an invariant volatility/risk measure across split-sensitive windows because raw OHLC discontinuities and the EWM state are not split-normalized. `vcp_tightness`: `MISMATCH` as literal VCP semantics; it is an inverse recent ATR-level percentile / low-volatility proxy, not a contraction-sequence detector.** | **PASS / causal.** All inputs are T0 or prior; rolling percentile includes T0 but no future observation. Corporate-action correction, if developed, must preserve as-of causality and must not back-propagate future splits. | **CLOSED / MATCH legacy-current.** Original repository contains the same ATR, percentile, VCP proxy, and Tradability >=60 contract. No R2 override analogous to EMA exists. | **CORRECT + RENAME/REDOCUMENT, governed separately.** Correct the corporate-action-sensitive ATR basis/state before claiming robust risk volatility across split windows; rename/re-document `vcp_tightness` as a volatility-tightness proxy unless a real VCP morphology detector is separately developed. Do not tune 60 in Core. |
| C07 | Pivot / breakout | Pivot proxy = rolling raw high 60, min20; Tradability compares T0 close with shifted prior-row pivot | Pivot-as-O'Neil semantics: `MISMATCH`; rolling-high breakout: `VALID USSY DEFINITION` | Breakout T0 causal | **OPEN** | Decide intended label; avoid silently claiming O'Neil pivot |
| C08 | Breakout volume | Raw volume percentile in rolling 50 including current; confirmation >=80 | `APPROXIMATION` | T0 causal | **OPEN** | Sep-14 incident was upstream incomplete volume, not percentile-formula failure |
| C09 | Market regime | SPY-based Bullish/Neutral/Bearish regime; excluded from Investability but included in hard-filter contract | `MATCH` architecture / `VALID USSY DEFINITION` | Backward-as-of; empirical freshness audit passed | **OPEN** | Preserve consumer distinction |
| C10 | Investability / Tradability | Investability = Trend + Liquidity + RS + Price non-compensatory; Tradability = breakout + volume confirmation + tightness; position entry intentionally retains separate backtest-parity contract | Dual downstream contract currently documented as `VALID USSY DEFINITION` | T0 decision / T+1 realistic execution traced | **OPEN** | Compare legacy aggregation/entry contract directly |

## C01-C04 independent review gate

**PASS.** See repository history for the detailed independent review record. C04 remediation remains governed separately.

## C05 evidence note — nominal price floor

Original and current hard filters use identical `close_raw` and $10/$8 thresholds. Current R2 maps READY `close` to `close_raw`; no price-floor overlay exists. This is intentionally a nominal-dollar rule, not an analytical return series. It is T0 causal and material through Investability and hard-filter position entry.

**C05 final verdict: `MATCH` legacy-current + `VALID USSY DEFINITION`; action `RETAIN`.** Threshold rationale remains `NEEDS_EVIDENCE / RESEARCH SEPARATELY` if optimization is ever desired. No production change.

## C06 evidence note — ATR14 and volatility tightness

### Legacy vs current execution

The original repository state and current branch are identical for the relevant formulas. `ATR_PERIOD=14`. True range is the row-wise maximum of `high_raw-low_raw`, `abs(high_raw-prev_close_raw)`, and `abs(low_raw-prev_close_raw)`. ATR uses pandas EWM with `alpha=1/period`, `adjust=False`, `min_periods=period`. `atr_pct` divides that ATR by same-row `close_raw`. `atr_percentile_63d` is the percentile rank of the current raw ATR level inside a rolling 63-session window with min20. `vcp_tightness` is exactly `100 - atr_percentile_63d`.

Current R2 production injects READY raw OHLCV into `feature_engine.build_feature_store()` and overlays terminal EMA only. Therefore ATR/tightness has no current migration or canonical adjusted-state override. Legacy=current mechanically.

Tradability uses `vcp_tightness >= 60` as `has_tight_structure`. This exact contract is also present in the original `decision_layer.py`, so neither the formula nor its consumer threshold drifted from legacy.

### ATR formula semantics

The true-range/Wilder-style smoothing mechanics are a valid ATR implementation for a continuous raw-price series, and the calculation is causal. However, Core review exposed an important basis issue not previously promoted by Evidence 11: the current input is **raw OHLC**, while Evidence 11 empirically established that raw and adjusted price bases are materially non-interchangeable around the corporate-action-sensitive population (30/31 event rows had >5pp one-session raw-vs-adjusted return gaps).

For a split-sensitive boundary, raw `prev_close` and post-action raw high/low can be in different per-share units. The true-range gap terms can therefore interpret the mechanical split discontinuity as market volatility. Even after the event row, recursive ATR state retains the artificial shock until it decays. `atr_pct` does not fully repair this because its numerator contains the mixed-basis recursive state. The 63-session percentile can also remain contaminated while the distorted ATR observation/state remains in its comparison window.

This is not a look-ahead problem and not evidence that the ATR equation itself is wrong. It is a **corporate-action basis/state mismatch** in the current raw-price implementation. Unlike C04, no frozen correction contract is adopted here by Core. The appropriate next remediation stage is to specify and validate an as-of-causal corporate-action-safe ATR price/state basis without changing risk parameters merely to hide the discontinuity.

This finding is material beyond presentation: production position registration reads T0 `atr14` and uses it to derive the provisional stop, later preserving T0 ATR when the realistic T+1 Open fill is installed. Thus a mechanically inflated split-boundary ATR can change stop distance. ATR is therefore not safely classifiable as merely informational.

### `vcp_tightness` semantics

The source code itself calls this field a **starting point** and **placeholder sederhana**. Its exact formula asks only where today's ATR level ranks within its recent 63-session ATR distribution. A high score means relatively low current ATR; it does not establish multiple successive volatility contractions, decreasing contraction amplitudes, base morphology, or Minervini VCP sequence structure.

Therefore FSE-002 remains supported: `vcp_tightness` is a low-volatility / ATR-tightness proxy, not literal VCP morphology. Calling it `vcp_tightness` overstates what is measured.

The >=60 Tradability cutoff is mechanically well-defined but not proven optimal by Core. No threshold tuning is justified here.

### C06 disposition

- Legacy vs current formula/consumer: **`MATCH`**.
- ATR mechanics on ordinary continuous raw-price windows: **valid ATR mechanics**.
- ATR robustness across split-sensitive windows: **`MISMATCH` / corporate-action-sensitive basis-state defect**.
- `vcp_tightness` as literal VCP semantics: **`MISMATCH`**.
- `vcp_tightness` as inverse recent ATR-level percentile / volatility-tightness proxy: **`VALID USSY DEFINITION` if renamed/re-documented accordingly**.
- Temporal causality: **PASS**.
- Materiality: **YES** — tightness affects Tradability tier, while ATR14 directly affects production stop distance for registered positions.
- Core action: **`CORRECT` ATR corporate-action basis under separate governed remediation + `RENAME / REDOCUMENT` the VCP field.** Do not silently redesign VCP and do not tune the >=60 threshold during Core Audit.

**C06 CLOSED. Production remains unchanged.**

## Existing deep evidence retained

- FSE-001 through FSE-015 findings in `FULL_SIGNAL_ENGINE_AUDIT.md`.
- Evidence 10: FSE-013 effective-date lifecycle correction passed research contract/regression and untouched validation V2; production decision remains separate.
- Evidence 11: corporate-action semantics for RS, liquidity, and nominal price. C06 additionally identifies ATR as another raw-price state requiring corporate-action-safe remediation analysis; this is a Core finding, not a retroactive claim that Evidence 11 tested ATR.
- Evidence 12: Sep-14 partial-volume incident; residual upstream repair handled separately and incident closed/verified.
- Evidence 13: FSE-014 split-normalized share-liquidity correction specification is frozen; research contract gate passed; production adoption remains separate.

## Scope boundary

Core proves primitive/core components. Full Audit remains responsible for composition and actual end-to-end decision semantics. Remediation remains a separate governed track.

## Next execution sequence

1. C01-C04 independent review gate: **PASS**.
2. C05 Price Floor: **CLOSED / RETAIN**.
3. C06 ATR / volatility tightness: **CLOSED / CORRECT ATR split-sensitive basis + RENAME/REDOCUMENT VCP proxy**.
4. Resume C07 Pivot / breakout from actual legacy/current execution path.
5. Continue C08-C10 sequentially.
6. Stop before any production remediation/change that requires a separate governed decision.
7. After C10, Core completion does not automatically close Full Signal Engine Audit; return to Full Audit composition/end-to-end correctness.

Production remains untouched throughout this Core audit.