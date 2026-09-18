# Feature Engine Reachability Audit

Status: **CLOSED / PRODUCTION-VERIFIED / CONSOLIDATED**

## Current production path

`.github/workflows/daily.yml` runs `main.py`.

```text
daily.yml
→ main.py
→ r2_integration.py
→ feature_engine.py
→ hard_filter.py / decision_layer.py
→ watchlist / alert / position tracking
```

There is one production orchestrator (`main.py`) and one feature calculation engine
(`feature_engine.py`). `r2_integration.py` is the R2 source/readiness boundary, not
a second feature engine. The former `r2_main.py` and `r2_feature_engine.py` were
retired after architecture regression and a full production-equivalence run.

## EMA ownership after FSE-005 remediation

The governed analytical EMA price basis is `adj_close`, matching the shared EMA
contract owned by `ussy-data`.

For the rolling READY timeline, production invokes `compute_canonical_ema_features()`
through the R2 integration boundary. These intermediate READY rows are an
**ADJ-CLOSE-BASIS LOCAL EMA / ROLLING-WINDOW DERIVATION**. READY is capped at about
300 bars and these intermediate EMA rows must not be described as full-history-seeded
canonical EMA.

The terminal production row is then replaced/validated by
`apply_shared_ema_terminal()` against the governed persisted shared EMA state from
`ussy-data`. That state is bootstrapped/rebuilt from canonical full history and
advanced recursively. Therefore terminal production EMA is
**CANONICAL GOVERNED FULL-HISTORY-SEEDED EMA**.

This does not change nominal raw-close price floor, pivot/breakout, Stage, ATR,
volume, 52-week-high, or other frozen raw-price semantics.

## Why no historical EMA dataset is persisted in R2

`ussy-data` owns canonical full OHLCV history and persisted terminal EMA state.
TrendFoll does not need a second full historical EMA object store. READY supplies
the rolling production feature window; terminal EMA correctness is governed by the
upstream persisted state and equivalence fence.

## Validation evidence

FSE-005 implementation commit:
`47eac431df7edc6c481619e5c8856aad8f086370`

Focused EMA CI:
`35236746582` — **SUCCESS**

Pre-consolidation terminal production verification:
Daily Watchlist run `35238539180` (#50) — **SUCCESS**

Pipeline consolidation architecture regression:
run `35283171630` — **SUCCESS**

Consolidated full production-equivalence verification:
Daily Watchlist run `35283636542` (#51), job `105410986767` — **SUCCESS**

Run #51 reproduced the material baseline #50 state:
- R2 READY: 1,227 securities / 367,544 rows
- Feature Store: 367,544 × 43
- exact SPY T0 readiness: PASS as-of 2026-09-16
- terminal shared EMA rows replaced: 1,227
- EMA equivalence verified: 50
- latest rows: 1,222 / 1,227
- candidates/watchlist: 106
- same five READY securities without a terminal-date bar: JFB, SITC, WILC, YYGH, ZTEK
- near-trigger shadow: 18 / 106
- database watchlist upsert: 106

## Classification

| Component | Classification |
|---|---|
| `main.py` | **SOLE PRODUCTION ORCHESTRATOR** |
| `feature_engine.py` | **SOLE FEATURE CALCULATION ENGINE / PRODUCTION-REACHABLE** |
| `r2_integration.py` | **R2 SOURCE + READINESS ADAPTER / NOT A FEATURE ENGINE** |
| `canonical_ema.py` | **ADJ-CLOSE READY-TIMELINE EMA DERIVATION** |
| `r2_ready.py` | **CANONICAL R2 READY LOADER/CONTRACT** |
| `r2_shared_ema.py` | **CANONICAL GOVERNED TERMINAL EMA VALIDATION/OVERRIDE** |
| `r2_main.py` | **RETIRED / ABSENT** |
| `r2_feature_engine.py` | **RETIRED / ABSENT** |

## Decision

**FSE-005 = CORRECTED / CI VALIDATED / PRODUCTION ADOPTED / TERMINAL VERIFIED / CLOSED.**

**PRODUCTION PIPELINE CONSOLIDATION = ADOPTED / PRODUCTION-EQUIVALENT / VERIFIED / CLOSED.**

Do not recreate a parallel R2 entrypoint or R2 feature engine. Any future architecture
change must preserve the production invariants above and be regression-validated
against the consolidated path.
