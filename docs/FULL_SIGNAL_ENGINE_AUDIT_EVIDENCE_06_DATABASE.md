# Full Signal Engine Audit — Evidence 06: Empirical Persistence Consistency

Status: **DIAGNOSTIC ONLY / READ-ONLY DATABASE AUDIT / NO PRODUCTION CHANGE**

Audit target: Supabase project `USSY Trendfoll`, current persisted `watchlist` and `positions` state.

## Watchlist

Read-only SQL result:

- 1,307 persisted watchlist rows
- 161 distinct historical symbols
- date range: 2026-07-31 through 2026-09-10
- duplicate `(symbol,date)` keys: **0**
- persisted rows with Investability below `NEAR_PASS` or null: **0**
- latest persisted snapshot (2026-09-10): 85 symbols

This empirically matches the code contract: watchlist persistence contains only Investability >= NEAR_PASS and retains historical daily snapshots rather than deleting candidates that later leave monitoring.

Notable continuity evidence: persisted dates are not every US market session. The table contains Sep-1, Sep-4, then Sep-10, consistent with the already documented workflow discontinuities. Lifecycle therefore represents **successful persisted observation days**, not a guaranteed uninterrupted daily state series.

Classification: **MATCH**, with continuity caveat.

## Positions

Current database state:

- total positions: **27**
- active: **6**
- closed: **21**
- missing `realistic_entry_price`: **0**
- nonpositive realistic entry: **0**
- invalid/missing trigger `entry_price`: **0**
- invalid/missing `atr14_at_entry`: **0**
- invalid/missing `stop_price`: **0**
- active positions with exit fields populated: **0**
- closed positions missing exit date/price: **0**
- closed positions with exit before entry date: **0**
- active stop mismatch against `realistic_entry_price - 2*ATR14(T0)`: **0 / 6**

There is one symbol (`ANF`) with two historical position rows, but only one is active. This is compatible with the one-active-position-per-symbol contract and the design that a symbol may generate a new position after a prior position closes.

Classification: **MATCH** for current persisted invariants.

## Audit consequences

1. The static downstream trace in Evidence 05 is supported by live persisted-state evidence.
2. No current database evidence indicates that watchlist rows below the monitoring threshold are being persisted.
3. No current database evidence indicates missing T+1 realistic-entry fills among the 27 recorded positions.
4. All six active stops are aligned to the realistic T+1 entry anchor under the current `2 * ATR14(T0)` contract.
5. Watchlist history must not be treated as a complete market-session time series because failed/missing production runs leave date gaps.

No mutation, repair, or production-rule change was performed.