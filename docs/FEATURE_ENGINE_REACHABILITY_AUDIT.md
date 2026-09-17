# Feature Engine Reachability Audit

Status: **CLOSED / PRODUCTION-REACHABLE / DO NOT DELETE**

## Question

Why do both `feature_engine.py` and `r2_feature_engine.py` exist, and is the former removable legacy code?

## Current production path

`.github/workflows/daily.yml` runs `python r2_main.py`. `r2_main.py` loads R2 READY and calls `r2_feature_engine.build_feature_store_from_r2()`.

`r2_feature_engine.py` is **not an independent replacement feature engine**. It currently imports `feature_engine as fe`, substitutes R2 READY for the stock-universe download, normalizes benchmark datetimes, and calls `fe.build_feature_store(universe, sector_map=...)`.

Therefore `feature_engine.py` remains **PRODUCTION_REACHABLE** and owns the bulk of feature formulas executed by the R2 production path.

Historical evidence agrees: commit `97ea8f03a9edd4c145e53857fb83a117bab350f7` introduced `r2_feature_engine.py` explicitly as an R2 adapter while retaining formula ownership in `feature_engine.py`.

## EMA ownership and price basis

`feature_engine.compute_ema_features()` calculates EMA20/50/150/200 from `close_raw` and derives `ema_stack_aligned` from raw close versus those EMAs.

After the full feature store is built, `r2_feature_engine.py` calls `apply_shared_ema_terminal()` from `r2_shared_ema.py`.

The shared EMA contract is governed R2 state with:

- price basis: `adj_close`
- periods: 20/50/150/200
- READY lineage validation
- equivalence gate
- terminal-row replacement

`apply_shared_ema_terminal()` replaces EMA20/50/150/200 and `ema_stack_aligned` **only on each symbol's terminal feature row**. It does not rewrite historical rows.

So the current state is intentionally asymmetric:

- historical feature-store EMA rows: legacy `close_raw` calculation from `feature_engine.py`
- terminal production EMA row: governed R2 shared `adj_close` EMA

The terminal production trend decision therefore uses canonical shared `adj_close` EMA, while historical/local feature-store EMA remains a consistency debt.

## Reachability classification

| Component | Classification | Evidence / role |
|---|---|---|
| `feature_engine.py` | **PRODUCTION_REACHABLE** | Called by `r2_feature_engine.build_feature_store_from_r2()` |
| `feature_engine.build_feature_store()` | **PRODUCTION_REACHABLE** | Builds the bulk of the feature store used downstream |
| `feature_engine.compute_ema_features()` | **PRODUCTION_REACHABLE, HISTORICAL EMA NON-CANONICAL** | Produces raw-close EMA before terminal override |
| `r2_feature_engine.py` | **PRODUCTION_REACHABLE ADAPTER/ORCHESTRATOR** | R2 READY adapter, benchmark readiness, shared EMA application |
| `r2_shared_ema.py` | **PRODUCTION-REACHABLE CANONICAL TERMINAL EMA** | Replaces terminal EMA state with governed `adj_close` state |
| auxiliary feature outputs previously classified by Full Signal Engine audit | **UNUSED AS AUTHORITATIVE DECISION INPUTS unless separate consumer exists** | Existing audit classification remains unchanged |

## Decision

1. **Do not delete or deprecate `feature_engine.py`.** It is not dead code.
2. **Do not blindly change its EMA from raw close to adjusted close.** That would alter historical feature semantics and may affect research/backtests/diagnostics beyond the already-frozen terminal production contract.
3. Preserve the audited terminal production contract: canonical shared R2 EMA on `adj_close`.
4. Treat historical raw-close EMA standardization as a separate migration workstream with explicit consumer-impact analysis and regression/equivalence evidence.
5. Longer-term architecture may split formula ownership from ingestion/orchestration so the misleading two-engine naming disappears, but that is refactoring, not a correctness emergency.

## Closure

The apparent "two feature engines" are not two competing independent production engines. The architecture is currently:

`R2 READY -> r2_feature_engine adapter/orchestration -> feature_engine formula core -> shared R2 terminal EMA override -> downstream production decisions`

This reachability question is closed. Any future EMA historical-basis migration must start from this contract rather than assuming `feature_engine.py` is legacy/dead.
