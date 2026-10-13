# PROB-017 — Position Identity / History Integrity Audit

Status: **READ-ONLY AUDIT COMPLETED / AMBIGUITY CONFIRMED / NO DATABASE MUTATION**

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

Both rows share the same trigger entry price (147.75), realistic entry price, and ATR14 at entry (7.6987), but carry conflicting exits and stop prices. Row 18's exit date equals its signal/entry date and `days_held=0`, despite the contract that realistic execution starts at T+1 open. That record is chronologically inconsistent with the intended executable-entry model. Row 19's 19-bar holding duration is chronologically plausible, but the audit does not silently declare it canonical or delete the other record.

## Schema and code boundary

- The database has a partial unique index on `symbol` only for `status='active'`; this prevents simultaneous active positions per symbol but does not prevent duplicate historical `(symbol, entry_date)` rows after a row closes.
- `idx_positions_symbol_entry_date` is a non-unique index.
- Current `positions.py` on the production default branch includes a same-signal-date exit guard and a duplicate-identity check before registering a new position for the same `symbol/entry_date`.
- A global `assert_position_identity_integrity` helper exists, but the current `main.py` pipeline does not invoke it at startup. Therefore the historical duplicate remains in the database and is not globally surfaced by that helper during every run.
- The current safeguards reduce repeat creation and same-day T0 exit risk going forward; they do not reconcile the existing rows.

## Decision

**PROB-017 remains confirmed and unresolved at the data-reconciliation layer.** Do not use the ANF pair as canonical forward-exit evidence or choose one row heuristically. No database rows were updated or deleted during this audit.

Recommended next action is a separately approved, auditable reconciliation that preserves both original row IDs and the reason for the chosen canonical treatment. After reconciliation, add/verify a database-level uniqueness strategy for logical signal identity that is compatible with legitimate later re-entries, and wire a non-destructive integrity preflight into operations once historical data is clean.
