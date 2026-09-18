# PROB-003 + PROB-004 — persistent alert event/delivery integrity

Status: **CLOSED / EVIDENCE LOCKED**

## Old pipeline and reproduced failure modes
Production computed transitions in memory from current `latest` versus the previous persisted watchlist date, then upserted today's watchlist and, if any transition existed, immediately called Telegram with a daily summary. No transition/event/delivery identity was persisted. An identical rerun therefore recomputed the same transition against the same prior-day snapshot and could resend. Telegram failures were swallowed by `notify._send`, so the pipeline could not distinguish delivered from failed. A crash after Telegram acceptance had no durable success marker.

## Frozen event identity
Event identity is transport-independent:
`contract_version + symbol + effective_date + transition_type + from_state + to_state`.
The canonical key is deterministic SHA-256 over those fields. Random attempt UUIDs, process/run IDs, timestamps and Telegram message IDs are metadata, never semantic event identity.

This preserves distinct legitimate transitions for the same symbol/date while making identical recomputation resolve to one event.

## State machine
`event recorded -> pending -> sending(leased) -> delivered`, with `sending/failed -> retry`.
`alert_events.event_key` is UNIQUE. `alert_deliveries(event_id,transport)` is UNIQUE. Attempts are append-only in `alert_delivery_attempts`. Database uniqueness arbitrates concurrent event creation; conditional status/claim-token updates arbitrate the send lease.

A failed transport remains the same event and becomes retryable. A delivered event is skipped on replay. A crashed `sending` lease becomes reclaimable after 15 minutes.

## Telegram boundary
The production integration uses HTTP Bot API `sendMessage`. Its documented parameters do not expose an application idempotency key. Therefore the system guarantees exactly-once semantic event persistence and suppresses normal rerun/concurrent duplicate sends, but cannot guarantee exactly-once external delivery across the crash window: Telegram may accept a message and the process may die before the database records success. That residual can produce a retry duplicate. This is explicitly not represented as exactly-once Telegram delivery.

## Historical boundary
No historical events were manufactured. Ledger history begins at deployment. Existing watchlist/candidate evidence remains unchanged.

## Security
All three ledger tables have RLS enabled. `anon` and `authenticated` privileges are revoked; production service_role is the writer. Telegram credentials/payload secrets are not stored. Delivery errors are truncated/sanitized to exception type/message.

## Production semantics
Alert-state computation, Investability/Tradability, breakout, T0/T+1, entry/exit, position lifecycle, Near-Trigger and CAND-003 are unchanged. Only persistence, rendering/orchestration, retry and delivery bookkeeping changed.
