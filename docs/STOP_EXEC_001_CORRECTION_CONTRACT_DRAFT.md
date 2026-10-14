# STOP-EXEC-001 — CURRENT Gap-Through Correction Contract and Implementation Audit

**Updated:** 2026-10-14  
**Status:** **REPOSITORY IMPLEMENTATION VERIFIED / HISTORICAL DIAGNOSTIC EVIDENCE LOCKED / LIVE DEPLOYMENT NOT INDEPENDENTLY VERIFIED**  
**Diagnostic evidence:** [`EVIDENCE_STOP_EXEC_001.md`](EVIDENCE_STOP_EXEC_001.md)  
**Original protocol:** [`STOP_EXEC_001_AUDIT_PROTOCOL.md`](STOP_EXEC_001_AUDIT_PROTOCOL.md)

## 1. Historical diagnostic

The locked STOP-EXEC-001 diagnostic compared a historical `CURRENT_EXACT_STOP` representation with a gap-aware diagnostic. In the governed 1,524-event paired sample, 93 events opened at or below the operative stop. An exact stop-price fill is infeasible for those events.

This remains valid evidence about the historical execution representation and the size of the affected event class. It does **not** mean the current repository still implements that defective fill assumption.

## 2. Read-only current repository audit — result

The current `main` branch already contains the gap-aware execution correction from commit [d213fd491975f8d9aaeb6116fef7eef837fd7cb5](https://github.com/azharmz/ussy-trendfoll/commit/d213fd491975f8d9aaeb6116fef7eef837fd7cb5), titled “Fix gap-through stop-loss execution”.

Audited behavior in `positions.py`:
- If `low_raw > stop_price`, no stop exit.
- If the stop is triggered but `open_raw` is missing, fail closed with an error instead of inventing an exact-stop fill.
- If `open_raw <= stop_price`, fill at observed Open and return `stop_fill_type="gap_open"`.
- Otherwise, if Low reaches the stop, fill at the stop and return `stop_fill_type="stop_touch"`.
- Both fill types preserve canonical persisted status/reason `stop_loss`, avoiding a new database status or migration.

Compatibility audit:
- `sql/schema_positions.sql` uses a free-text `status` field and does not declare a CHECK constraint enumerating exit statuses.
- The exit update stores the selected `exit_price`; realized `pnl_pct` in the alert payload is calculated from that actual fill.
- `notify.py` already labels `gap_open` as “STOP LOSS — GAP THROUGH (fill di Open)”.
- Dashboard history/performance uses persisted `status` for grouping and actual `exit_price` for realized return. Preserving `status="stop_loss"` keeps gap-through exits in the existing stop-loss group; no schema migration is indicated by this audit.
- Historical `max_holding` status styling/labels remain as compatibility for old rows; they do not establish an active age-based exit rule.

## 3. Test evidence

`tests/test_gap_aware_stop_execution.py` covers gap-open fills, ordinary stop touches, untouched stops, missing Open fail-closed behavior, persistence of the gap-open price with stable `stop_loss` status, and PnL calculation. The same workflow passed on 2026-10-14 in run `38552916021` (Gap-aware stop execution regression #21), including the new >45-session and trend-break regression cases.

## 4. Decision and remaining boundary

**No additional production code or schema migration is indicated by this read-only audit.** The gap-aware behavior is already present and regression-tested in repository `main`.

Still not established here:
- which commit the live daily pipeline is executing;
- whether the live dashboard and alert deployment have picked up the repository behavior;
- an independently observed real post-fix gap-through exit.

Therefore the historical diagnostic is closed as a discovery, the repository implementation audit is complete, but independent live deployment verification remains pending. Do not rewrite historical position rows or rerun/retune the frozen research corpus as part of this documentation update.

## 5. Guardrails

- Do not change the 2×ATR14 stop placement.
- Do not change EMA20 trend-break logic.
- Do not change the frozen CAND-003 contract or its 45-session shadow boundary.
- Do not introduce a new `stop_loss_gap` database status without a separate evidence-backed reason; current `stop_loss` status plus `stop_fill_type` alert metadata is the implemented compatibility contract.
- Do not claim a production deployment check unless a live run/position/alert is actually inspected.