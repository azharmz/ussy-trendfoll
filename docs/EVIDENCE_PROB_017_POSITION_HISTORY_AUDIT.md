# PROB-017 — Position Identity / History Integrity Audit

Status: **AUDIT COMPLETED / CANONICAL MAPPING RECORDED / ORIGINAL POSITION ROWS PRESERVED**

Audit date: 2026-10-13
Project: Supabase project `USSY Trendfoll`
Scope: `public.positions` identity and exit chronology.

## Aggregate result

- 66 position rows.
- 65 distinct `(symbol, entry_date)` identities.
- One duplicate excess row: `ANF / 2026-08-26`.
- 21 active rows across 21 distinct active symbols.
- One active row currently lacks `realistic_entry_price`: `SHOP / 2026-10-12`, created 2026-10-13 03:54 UTC. This is consistent with an entry awaiting the next available trading bar; it is not treated as an anomaly from this snapshot alone.

## Conflicting ANF records

| ID | Status | Entry date | Realistic entry | Exit date | Exit price | Days held |
|---:|---|---|---:|---|---:|---:|
| 18 | stop_loss | 2026-08-26 | 144.70 | 2026-08-26 | 132.35 | 0 |
| 19 | trend_exit | 2026-08-26 | 144.70 | 2026-09-23 | 132.25 | 19 |

Both rows share the same trigger entry price (147.75), realistic entry price, and ATR14 at entry (7.6987), but carry conflicting exits and stop prices. Row 18's exit date equals its signal/entry date and `days_held=0`, despite the contract that realistic execution starts at T+1 open. That record is chronologically inconsistent with the intended executable-entry model. Row 19's 19-bar holding duration is chronologically plausible. The stop anchor also matches the executable-entry contract: 144.70 − 2 × 7.6987 ≈ 129.3025, unlike row 18's trigger-price anchor of 147.75 − 2 × 7.6987 ≈ 132.3525.

## Schema and code boundary

- The database has a partial unique index on `symbol` only for `status='active'`; this prevents simultaneous active positions per symbol but does not prevent duplicate historical `(symbol, entry_date)` rows after a row closes.
- `idx_positions_symbol_entry_date` is a non-unique index.
- Current `positions.py` on the production default branch includes a same-signal-date exit guard and a duplicate-identity check before registering a new position for the same `symbol/entry_date`.
- A global `assert_position_identity_integrity` helper exists, but the current `main.py` pipeline does not invoke it at startup. Therefore the historical duplicate remains in the database and is not globally surfaced by that helper during every run.
- The current safeguards reduce repeat creation and same-day T0 exit risk going forward; they did not reconcile the existing rows automatically.

## Reconciliation decision — recorded 2026-10-13

The approved decision is recorded in Supabase table `public.position_identity_reconciliations`, ledger row ID **1**:

- Logical identity: `ANF / 2026-08-26`.
- Canonical position: **ID 19** (`trend_exit`, 2026-09-23, 19 days held).
- Retained anomaly: **ID 18** (`stop_loss`, signal-day exit, `days_held=0`).
- Resolution status: `resolved`.
- The ledger stores the rationale, verification booleans, and JSON snapshots of both original rows.

Post-write verification confirmed that both original `public.positions` rows remain unchanged and the table still contains 66 rows / 65 distinct identities. No position row was updated or deleted. The reconciliation is logical and auditable, not a physical deduplication.

## Remaining operational work

**The ANF identity is reconciled in the ledger, but PROB-017 is not fully closed for every consumer.** Any query, dashboard, export, or analysis that reads `public.positions` directly and ignores `public.position_identity_reconciliations` can still double-count this identity. Before calling the whole integrity problem resolved:

1. Make canonical-outcome readers consult the ledger or a governed canonical view.
2. Add a non-destructive identity-integrity preflight to operations.
3. Design uniqueness enforcement compatible with legitimate later re-entries; do not impose a naive unique `(symbol, entry_date)` constraint without validating lifecycle semantics.
