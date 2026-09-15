# CAND-003 Production Shadow — Append-only Session Ledger

Status: IMPLEMENTATION SPEC / NO PRODUCTION EXIT CHANGE

## Purpose

Close the operational-evidence gap in the frozen CAND-003 production-shadow plan by recording one immutable evidence row per observed production position, market session, and shadow contract version.

This ledger is evidence only. It must not drive or mutate the authoritative production exit decision.

## Contract

Shadow contract version remains `exit-cand-003-shadow-v1`.

Identity/invariant key:

`(position_id, session_date, contract_version)`

A repeated evaluation of the same position/session/version must be idempotent: it may confirm the identical evidence row, but must never create a second row or silently replace different evidence.

## Required session evidence

Each row must preserve, at minimum:

- position identity and symbol
- session date and contract version
- entry date and entry price
- days observed
- session OHLC used by the shadow evaluator
- operative stop entering the session
- stop source/state entering the session
- HH22, Wilder ATR22, and Chandelier value computed after surviving the session
- next-session ratcheted stop
- hypothetical shadow exit reason and price, if any
- authoritative production position status / production exit reason / production exit price available at evaluation time
- invariant flags needed to establish gap-before-touch ordering and no same-day Chandelier look-ahead
- creation timestamp

## Frozen CAND-003 ordering

For an operative stop known before session t:

1. `open_raw_t <= operative_stop_t` => hypothetical fill at Open, `risk_stop_gap`.
2. Else `low_raw_t <= operative_stop_t` => hypothetical fill at exact operative stop, `risk_stop_touch`.
3. Otherwise the position survives the stop check.
4. Boundary / EMA20 logic follows the frozen shadow representation.
5. HH22 / ATR22 / Chandelier calculated from session t may only arm/ratchet the stop for t+1; it cannot stop session t.

## Persistence rule

The existing mutable `exit_candidate003_shadow` row remains current shadow state. The new session ledger is append-only evidence and must be persisted independently.

Recommended table: `exit_candidate003_shadow_sessions`.

The application must use conflict-safe insert semantics on the invariant key. A conflict is acceptable only when the existing row is evidence-equivalent. Divergent evidence for the same invariant key is an operational defect and must surface loudly.

## Required database constraints

- primary key or unique constraint on `(position_id, session_date, contract_version)`
- non-null identity/session/contract fields
- service-role write access
- read policy/grant consistent with existing shadow evidence governance
- no update/delete path in normal application operation

## Tests required before claiming completion

1. Same position/session/version evaluated twice produces one ledger identity.
2. Gap-through has priority over touch and records Open fill.
3. Intraday touch without gap records exact operative-stop fill.
4. Chandelier computed from session t is recorded as next-session state and never used as session-t operative stop.
5. No-stop survivor records both operative and next stop evidence.
6. Production comparison fields do not alter the shadow decision.
7. Divergent duplicate evidence is rejected/surfaced.
8. Tests are actually discovered by the repository CI runner (not bare pytest functions under unittest discovery).

## Governance

This implementation must not:

- change the production exit contract;
- change CAND-003 parameters;
- tune ATR/EMA/holding-period values;
- use shadow outcomes to alter production behavior;
- modify Investability or Tradability semantics.

Completion requires code + schema + discovered tests + a terminal successful CI run + operational evidence verification.