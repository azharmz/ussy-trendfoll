# PROB-017 — Ledger-aware canonical history and integrity preflight

Status: **IMPLEMENTED ON DIAGNOSTIC BRANCH / VALIDATION PENDING**

Branch: `diagnostic/prob017-canonical-preflight`  
Scope: software integrity only. No strategy, entry, exit, or production database rows are changed by this branch.

## Changes

- `positions._validate_position_identity_rows` validates every duplicate `(symbol, entry_date)` group against the reconciliation ledger.
- A duplicate group is accepted only when exactly one `resolved` decision names a canonical ID present in the group and the excluded-ID set exactly matches every other ID in that group.
- A stale or incomplete `resolved` ledger entry fails closed.
- `positions.get_canonical_position_history` returns a validated canonical history and omits only IDs explicitly excluded by a resolved ledger decision. Source rows remain untouched.
- `positions.assert_position_identity_integrity` reads both tables with pagination and performs the non-destructive preflight.
- `main.main` invokes the preflight immediately after creating the Supabase client, before loading data or performing daily writes.
- `tests/test_prob017_position_identity.py` covers the reconciled ANF case, unresolved duplicates, review-required decisions, invalid canonical/excluded IDs, and stale ledger mappings.

## Expected behavior for the known ANF identity

- IDs 18 and 19 remain present in `public.positions`.
- Ledger row 1 designates ID 19 canonical and ID 18 excluded from canonical outcomes.
- The integrity preflight accepts this group only while the ledger exactly matches the current source IDs.
- The canonical-history helper returns ID 19 and omits ID 18; it does not delete or update either row.

## Fail-closed cases

The preflight stops the daily pipeline if it finds a duplicate group without exactly one valid resolved ledger mapping, or if a resolved mapping no longer matches the source table. This is intentional: an ambiguous history must not silently flow into outcome analysis.

## Validation boundary

Unit tests and CI must pass before merge. This branch does not automatically modify external dashboards, exports, notebooks, or other applications that query `public.positions` directly. Those consumers must adopt `get_canonical_position_history` or an equivalently validated canonical interface before PROB-017 can be called fully resolved end-to-end.

No unique constraint on `(symbol, entry_date)` is proposed: later re-entry semantics remain distinct from immutable lifecycle identity `positions.id`.
