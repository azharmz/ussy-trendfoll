# Feature Engine Reachability Audit

Status: **CLOSED / PRODUCTION-REACHABLE / HISTORICAL EMA MIGRATION CI-VALIDATED / PRODUCTION ADOPTION PENDING TERMINAL RUN**

## Current production path

`.github/workflows/daily.yml` runs `r2_main.py`, which calls `r2_feature_engine.build_feature_store_from_r2()`. The R2 adapter still delegates the bulk of feature formulas to `feature_engine.build_feature_store()`; therefore `feature_engine.py` remains production-reachable and must not be deleted as legacy code.

## EMA ownership after FSE-005 remediation

The governed analytical EMA price basis is `adj_close`, matching the shared EMA contract owned by `ussy-data`.

The R2 production adapter now applies `compute_canonical_ema_features()` to each symbol's full READY timeline after the legacy feature store is built. This replaces only EMA20/50/150/200 and `ema_stack_aligned` across the historical READY rows. It does **not** alter nominal raw-close price floor, pivot/breakout, Stage, ATR, volume, 52-week-high, or other frozen raw-price semantics.

After that historical canonicalization, `apply_shared_ema_terminal()` still replaces/validates the terminal row against the governed persisted shared EMA state. Thus terminal source-of-truth and READY lineage remain unchanged.

## Why no historical EMA dataset is persisted in R2

`ussy-data` already owns canonical full OHLCV history and a persisted terminal EMA state. READY is a rolling window (maximum 300 bars per ticker), while the shared terminal EMA state is bootstrapped/rebuilt from canonical full history and advanced recursively. TrendFoll therefore does not need a second full historical EMA object store. Historical EMA rows are deterministically derived from the `adj_close` rows supplied to the feature engine; terminal production state remains governed upstream.

## Regression evidence

Implementation commit: `47eac431df7edc6c481619e5c8856aad8f086370`

CI commit: `afd4fd70d5cea8e1cfa01f638a2e5e4c6a437a14`

GitHub Actions run: `35236746582` — **SUCCESS**

The focused regression verifies EMA20/50/150/200 against pandas `ewm(span=period, adjust=False)` on `close_adj`, a synthetic split discontinuity cannot contaminate canonical EMA, stack alignment uses adjusted close, and missing/non-numeric adjusted close fails closed.

A prior observational migration audit had already shown that raw-vs-adjusted historical EMA differences are real but aggregate event overlap is high. That evidence was reused rather than repeating expensive research compute.

## Classification

| Component | Classification |
|---|---|
| `feature_engine.py` | **PRODUCTION_REACHABLE** |
| legacy `feature_engine.compute_ema_features()` | **INTERMEDIATE ONLY on R2 path; canonicalized before downstream use** |
| `r2_feature_engine.py` | **PRODUCTION R2 ORCHESTRATOR** |
| `canonical_ema.py` | **CANONICAL HISTORICAL READY-TIMELINE EMA (`adj_close`)** |
| `r2_shared_ema.py` | **CANONICAL GOVERNED TERMINAL EMA (`adj_close`)** |

## Decision

FSE-005 historical EMA price-basis consistency has passed focused CI and is ready for production adoption. It is not marked terminally CLOSED/VERIFIED until a normal `USSY TrendFoll — Daily Watchlist` production run succeeds on the adopted main commit (or a descendant containing the same remediation). The legacy feature engine remains because it owns other production-reachable formulas. Broader feature-engine refactoring is separate architecture work.
