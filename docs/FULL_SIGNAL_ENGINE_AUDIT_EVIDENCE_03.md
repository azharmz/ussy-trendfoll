# Full Signal Engine Audit — Evidence 03

Status: **DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Benchmark / external-data boundary

Current production stock OHLCV comes from the R2 READY dataset. Benchmark/context series remain externally fetched through yfinance.

Observed benchmark inventory in the feature engine:

- `SPY`: decision-relevant. Used for 63-session relative strength and market-regime construction.
- `QQQ`: fetched but no current production Investability/Tradability dependency was identified in the traced decision path.
- `^VIX`: auxiliary/context feature; no current Investability/Tradability dependency identified.
- sector ETFs: auxiliary relative-strength/context features; no current Investability/Tradability dependency identified.

This is a split-ingestion architecture: stock rows and benchmark rows do not inherit one common R2 readiness/checksum/freshness contract.

## Temporal alignment semantics

### RS63

The stock's 63-session adjusted-close return is compared with SPY using date-aligned benchmark data. The calculation therefore depends on exact-date benchmark availability/alignment for the relevant observation.

### Market regime

Regime alignment uses backward/as-of semantics. A stock observation may therefore inherit the most recent prior benchmark regime observation rather than requiring an exact same-date benchmark row.

These are not intrinsically look-ahead operations, but they have different stale-data behavior and must not be treated as one temporal contract.

## Audit classification

### Benchmark ingestion

`NEEDS_EVIDENCE` remains appropriate until empirical freshness/calendar behavior is measured. Code inspection establishes the split boundary but cannot prove that live benchmark rows are always current when R2 READY is current.

### Temporal semantics

- shifted pivot (`pivot_high.shift(1)`) prevents same-bar pivot self-reference: **MATCH** for Donchian-like prior-high breakout semantics.
- breakout is only known after T0 close; execution evaluation must remain T+1 Open where an executable trade is studied.
- current-bar volume percentile includes current T0 volume. This is available at T0 close and therefore is not look-ahead, but it differs semantically from a percentile threshold frozen strictly on T-1 information.
- regime backward-as-of alignment is causal if benchmark data are timestamp-current, but can silently tolerate stale benchmark state. Freshness therefore remains an empirical/data-contract question.

## Decision-layer architecture confirmed

`hard_filter_status` and `investability_status` are not synonyms:

- hard filter includes trend, liquidity, RS, price **and market regime**;
- Investability uses trend, liquidity, RS and price, excluding market regime;
- Tradability is separately derived from breakout + volume confirmation + tightness.

This distinction is intentional in current code structure but requires downstream-consumer audit so that no component accidentally treats `hard_filter_status` as Investability or vice versa.

No production change is authorized from this evidence alone.