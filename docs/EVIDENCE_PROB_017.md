# PROB-017 — Position Identity / Lifecycle Integrity Evidence

Status: **CLOSED / EVIDENCE LOCKED**

## Production audit

Audit date: 2026-09-18. Production-linked Supabase contained **27 rows / 27 unique ids**. Exactly **1 duplicate (symbol, entry_date) group** affected **1 symbol** and was conflicting:

- ANF / 2026-08-26: ids 18 and 19.
- id 18: stop_loss, exit_date 2026-08-26, exit_price 132.35252353126424.
- id 19: active.
- Both share trigger 147.75, filled T+1 open 144.6999969482422, ATR14(T0) 7.69873823436788.
- Status distribution at audit: 13 stop_loss, 8 trend_exit, 6 active.

No other duplicate group existed.

## Reconstructed root cause

The 2026-08-27 scheduled pipeline run 33028409635 used the historical ordering:
check_exits -> fill_realistic_entry_prices -> register_new_positions.

The production row for ANF already represented the 2026-08-26 signal. A rerun whose latest/as-of bar still resolved to the same signal date could evaluate that active row against T0, close it, then registration saw no active ANF and inserted the same signal occurrence again. The active-symbol partial unique index could not prevent this because the first row had already become closed.

Taxonomy: **accidental replay/lifecycle-order/idempotency failure**, not legitimate multiple positions.

## Canonical identity contract

1. `positions.id` is the immutable canonical position/lifecycle identifier and the only key consumers may use to link a concrete position.
2. Under the current single-strategy production contract, `(symbol, entry_date)` identifies one signal occurrence and is an idempotency/replay invariant.
3. Repeated positions in the same symbol are valid only for a later signal date after the prior position is no longer active. Multiple positions for the same symbol and signal date are not valid.
4. T0 is signal registration only. Production exit evaluation begins no earlier than T+1; same-signal-date reruns cannot exit the row.
5. Retry/replay must reuse/skip the existing signal occurrence. It must never create another row.
6. Consumers linking lifecycle/shadow/outcomes must propagate `positions.id`. Ambiguous logical-key lookup fails closed; no first/latest/limit-one heuristic is canonical.
7. Historical conflicting rows are retained unchanged as audit evidence.

## Consumer impact

Production exit tracking already updates by `id`. CAND-003 shadow and its append-only session ledger already link by `position_id`; both historical ANF ids are retained and their pre-fix shadow rows are already classified `invalid_bootstrap`. Repository research diagnostics reconstruct market paths independently and do not use the production `positions` table as their historical event corpus. No frozen research evidence is rewritten by this remediation.

## Remediation

- registration checks the full signal-occurrence key before insert, not only active symbol;
- ambiguous pre-existing signal identity fails closed;
- T0 exit evaluation is prohibited as a lifecycle guard;
- DB trigger rejects any new duplicate `(symbol, entry_date)` while preserving the historical ANF conflict;
- supporting non-unique lookup index added;
- no destructive historical deduplication and no trading parameter/entry/exit-rule change.

The database trigger is intentionally used instead of a UNIQUE constraint because the historical conflicting rows are preserved. A future explicit archival migration could enable a conventional UNIQUE constraint, but is not required to close the live write-path defect.
