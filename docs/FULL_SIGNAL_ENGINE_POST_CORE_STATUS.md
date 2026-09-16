# Full Signal Engine Audit — Post-Core Status

Status: **ACTIVE / CORE 10/10 FROZEN / PRODUCTION UNCHANGED**

Date: 2026-09-17

Branch: `research/exit-development-hypotheses`

## Purpose

This document synchronizes the Full Signal Engine Audit after `CORE_INDICATOR_AUDIT.md` reached 10/10 closure. The 269-item engineering checklist remains useful evidence and hardening inventory, but Core findings now control primitive semantics. Open checklist items must not mechanically reopen a Core component unless new contradictory evidence appears.

Terminal objective:

`R2 READY -> FEATURES/INDICATORS -> HARD FILTER -> INVESTABILITY -> TRADABILITY -> CANDIDATE/WATCHLIST -> ALERT/ACTIONABLE -> PRODUCTION ENTRY/EXIT`

## Frozen Core dispositions consumed by Full Audit

1. C01 terminal canonical EMA: retain governed adj-close terminal state; historical/local consistency separate.
2. C02 Stage: retain as Weinstein-inspired approximation.
3. C03 RS vs SPY: retain 63-session adjusted-return excess-return definition; optimization separate.
4. C04 Liquidity: split-sensitive raw share-volume mismatch; FSE-014 governance applies.
5. C05 nominal price floor: retain raw current-price rule.
6. C06 ATR: ordinary formula valid, but split-sensitive raw ATR state needs separate correction governance; `vcp_tightness` is a volatility-tightness proxy, not literal VCP.
7. C07: retain prior-60-session trailing-high breakout; not O'Neil/base pivot.
8. C08: retain inclusive rolling-volume-rank confirmation; inherits normalized-volume dependency.
9. C09: retain internal SPY SMA50/SMA200 regime; benchmark readiness remains Full-Audit boundary.
10. C10: preserve explicit dual contracts; watchlist/actionability and production entry are not interchangeable.

## Reconciliation of stale Full-Audit statements

The detailed checklist statement that FSE-014 still requires a correction specification is stale. The correction contract is frozen. Research implementation: `5e0e91046c30165abeef02857435d5f553ee0c63`. Contract tests: `785c513f442a27971616af2122b5ecdbd5eb5a80`. CI research gate head: `593e8f699494e7e155e95e1835eaf4e98f754056`; run `35080840497` succeeded.

The FSE-014 contract retains window=50, min_periods=20 and existing PASS/NEAR thresholds. At T0, historical share volume is expressed on T0 share basis using only split factors effective in `(t,T0]`; future events cannot alter historical state; unknown required factors fail closed.

FSE-013 is technically past correction/validation: refined contract, regression, and untouched validation V2 are complete. Remaining step is explicit production adoption/defer/reject governance.

FSE-015 Sep-14 partial-volume incident is CLOSED/VERIFIED under its incident scope after upstream finalization protection and residual HUBB/SITC repair. It is not a blocking TrendFoll remediation without new contradictory evidence.

## FSE-014 upstream contract verification — BLOCKER CONFIRMED

Full Audit inspected current `azharmz/ussy-data` production source contract.

`src/bootstrap_ohlcv.py` defines persisted `OHLCV_COLUMNS` as only:

`date, security_id, ticker, open, high, low, close, adj_close, volume`.

The Yahoo bootstrap call explicitly uses `actions=False`. `normalize_history()` maps only OHLCV/Adj Close/Volume and emits exactly the OHLCV schema above. Therefore current upstream persisted OHLCV/READY does **not** carry authoritative split-event ratios.

`READY_DATA.md` also documents the consumer dataset as rolling price data (max 300 bars/ticker) and does not define a corporate-action/split-factor lineage contract.

Current TrendFoll `r2_ready.to_feature_contract()` synthesizes `stock_splits=0.0`; that is a compatibility placeholder, not evidence that no split occurred. It cannot satisfy FSE-014's fail-closed authoritative-factor requirement.

### FSE-014 production disposition at this gate

**BLOCKED_ON_UPSTREAM_CONTRACT.**

This is not a rejection of the correction. The research correction and tests are valid for their frozen input contract, but production adoption is unsafe until upstream provides authoritative split factors with date/security lineage and as-of semantics. TrendFoll must not infer/fabricate split factors merely to make the correction executable.

The proper dependency is:

`ussy-data corporate-action fact contract -> R2 READY/sidecar lineage -> TrendFoll causal normalization -> regression -> untouched validation -> production decision`.

No production code was changed.

## Remaining production-relevant work after Core

### P1 — Production-decision queue

**FSE-013 effective-date lifecycle state** — technically validated; explicit production decision remains.

**FSE-014 split-normalized share-volume state** — research contract validated, but **BLOCKED_ON_UPSTREAM_CONTRACT** because current `ussy-data` does not persist split factors.

### P2 — ATR split-sensitive state

C06 establishes a production-relevant corporate-action basis defect because raw OHLC true range can interpret a split discontinuity as volatility and recursive ATR state affects production stop distance. It requires a separate correction contract. It must not be silently folded into FSE-014.

The same upstream corporate-action fact gap is likely relevant to an explicit split-aware ATR correction, but the ATR contract must be frozen independently because price-basis/risk semantics differ from share-volume normalization.

### P3 — Benchmark readiness governance

C09 confirms the regime formula is causal, but stock state is governed by R2 READY while SPY/other benchmark state is downloaded live. FSE-007 remains ingestion/readiness governance: explicit benchmark as-of/freshness guard or governed benchmark snapshot contract. This is architecture hardening, not formula tuning.

### P4 — Historical EMA consistency

Terminal production EMA is canonical. Historical rows retain legacy finite-window/raw-close state. This belongs to the separate legacy feature-engine standardization workstream unless Full Audit identifies a current production consumer materially affected by historical mixed-basis state.

## Non-blocking methodology research

The following are not blockers under frozen USSY definitions: optimization of RS horizon/thresholds, liquidity/price thresholds, fuller Weinstein Stage morphology, O'Neil base-pivot replacement, O'Neil average-volume expansion, ATR-percentile threshold tuning, and frequency studies whose purpose is strategy optimization rather than correctness.

## Immediate Full-Audit execution order

1. FSE-014 upstream split-factor availability: **DONE — BLOCKER CONFIRMED**.
2. Freeze separate C06/ATR corporate-action correction contract and build research-only tests/implementation; no production change.
3. Close FSE-007 benchmark freshness governance with an explicit detectable contract.
4. Reconcile findings/checklist against Core 10/10 so stale methodology items are non-blocking.
5. Produce correction decision matrix: FSE-013, FSE-014, ATR, benchmark readiness, and any truly production-relevant historical EMA dependency.
6. Only after those gates, proceed to explicit production adoption/defer/reject decisions and full regression/untouched validation as applicable.

## Current terminal state

- Core Indicator Audit: **CLOSED 10/10**.
- Full Signal Engine Audit: **ACTIVE**.
- FSE-014: **BLOCKED_ON_UPSTREAM_CONTRACT**, not failed.
- Production code: **UNCHANGED**.
- Next executable work: **C06/ATR split-sensitive correction contract on research branch**, while upstream split-factor support is handled in `ussy-data` governance.
