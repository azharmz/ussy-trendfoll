# Canonical Shared EMA Production Migration Evidence

Status: **PASS / PRODUCTION SOURCE MIGRATION AUTHORIZED**

Scope: latest-day TrendFoll production scanner only. This evidence does not close `PROB-019`, which separately governs historical research/pre-roll initialization.

## Contract

TrendFoll production migrates from terminal EMA values recomputed from the rolling ready window using raw `close` to the governed shared EMA state published by `ussy-data`:

- pointer: `production/indicators/ema/current.json`
- price basis: `adj_close`
- periods: 20 / 50 / 150 / 200
- state initialization: long-history bootstrap, then recursive persisted updates
- promotion: candidate -> equivalence -> immutable run -> current pointer last

Only terminal EMA20/50/150/200 and `ema_stack_aligned` are replaced. Stage2, RS, liquidity, market regime, breakout, volume, structure, ATR, tradability, exit rules, and thresholds remain unchanged.

## Upstream methodology evidence

TrendFoll PR #5 froze the price-basis audit. On a deterministic 100-symbol long-history sample with 500-bar warm-up, changing only EMA price basis from raw `close` to `adj_close` produced 98.82% entry-ready event Jaccard overlap, with essentially unchanged T+1/T+3/T+5 outcome characteristics. No evidence supported maintaining raw-close EMA as a permanent strategy-specific exception.

## Production shadow gate

Workflow: `Canonical EMA migration shadow`

Run: `34903826440` (run #3)

Head: `b7c832ca4f4d25a8895e8883be387b976230baac`

Result: **SUCCESS**

Repository tests: **8 / 8 PASS**

Ready universe: **1,226 securities**

Shared EMA lineage matched the current ready dataset.

### Latest stack impact

16 securities changed terminal `ema_stack_aligned` between legacy finite `EMA(close)` and governed recursive canonical `EMA(adj_close)`:

`ACFN, CHT, CRCT, CTAS, ICLR, III, MXC, NEPH, NRP, NTNX, PC, PVL, SD, SLP, SWKS, UG`

Only these 16 securities required downstream recomputation; all other securities were invariant under an EMA-only migration.

| Layer | Changes |
|---|---:|
| EMA stack | 16 |
| Trend status | 15 |
| Hard-filter status | 5 |
| Investability status | 5 |
| Candidate membership | 5 |
| Tradability status | **0** |
| Actionable membership | **0** |

The shared EMA state used by the run carried upstream equivalence evidence with `verified=50` and zero governed equivalence failures, and pointed to immutable run `production/indicators/ema/runs/run-34896707408-1.parquet`.

## Verdict

Migration is authorized as an architecture/data-contract correction, not strategy tuning.

The observed qualification changes are expected consequences of removing rolling-window EMA reinitialization and adopting the canonical adjusted analytical price basis already supported by the frozen price-basis audit. No execution/tradability rule changed, and the shadow gate observed zero Tradability and zero Actionable membership changes.

Full production pipeline rerun is intentionally not required as a migration gate because same-day reruns can recompute/resend alert transitions while persistent alert-event idempotency is still open engineering debt. The next normal scheduled production run should consume the canonical EMA state through the standard pipeline.
