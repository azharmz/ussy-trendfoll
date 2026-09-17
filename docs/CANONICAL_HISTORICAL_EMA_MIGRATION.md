# Canonical historical EMA migration

Status: IMPLEMENTED ON VALIDATION BRANCH; PRODUCTION ADOPTION PENDING REGRESSION.

## Contract

`ussy-data` owns the canonical analytical EMA contract: `adj_close`, EMA20/50/150/200, pandas `ewm(adjust=False)` recursion. READY is a rolling dataset (maximum 300 bars per ticker); governed terminal EMA state is persisted separately and bootstrapped/rebuilt from canonical full history.

TrendFoll must not publish another full-history EMA dataset. For the R2 production feature timeline it computes EMA locally from READY `adj_close`, then keeps the governed shared EMA terminal replacement as the production source-of-truth/lineage fence.

## Scope

This migration changes only EMA20/50/150/200 and `ema_stack_aligned` inside the R2 feature path. It does not change nominal raw-close price floor, pivot/breakout, 52-week-high distance, Stage, ATR, volume, RS, thresholds, entry timing, exits, fees, or the shared terminal EMA contract.

The standalone historical `feature_engine.py` formula remains untouched in this patch. The R2 adapter injects the canonical EMA function while building the READY-backed feature store. This avoids silently changing older standalone research/backtest entrypoints before their own consumers are explicitly migrated.

## Existing materiality evidence

The prior Shared EMA Migration Audit compared raw-close versus adj-close EMA while holding non-EMA logic constant. On the deterministic 100-symbol long-history sample it found non-zero historical state changes but high signal-event overlap. That evidence authorizes regression testing, not blind production adoption.

## Adoption gate

Before merge/adoption:

1. unit tests for canonical EMA must pass;
2. R2 feature build must still pass READY and exact-SPY-T0 guards;
3. terminal locally computed EMA must agree with governed shared EMA within the existing shared-state equivalence contract;
4. downstream hard-filter/investability/tradability/candidate/actionable changes must be measured and reviewed;
5. production daily behavior must not be changed until regression evidence is recorded.

No new full-history R2 EMA storage is required.
