# PROB-017 — Ledger-aware canonical history and integrity preflight

Status: **CANONICAL CONSUMER IDENTIFIED / RPC + DASHBOARD PATCH ADDED / DEPLOYMENT VALIDATION PENDING**

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
- `.github/workflows/prob017-tests.yml` runs the focused test suite automatically on relevant pull-request changes and remains manually dispatchable. It has read-only repository permissions and does not access production secrets or the database.

## Validation evidence

- GitHub Actions run **PROB-017 Identity Tests #2** completed successfully on 2026-10-14.
- Result: **5 passed in 0.21s**.
- The FSE-007/FSE-013 production regression and gap-aware stop execution regression workflows associated with the same PR commit also completed successfully.
- These results validate the focused unit-test contract and those regression suites; they do **not** prove all external readers of `public.positions` use canonical history.

## Expected behavior for the known ANF identity

- IDs 18 and 19 remain present in `public.positions`.
- Ledger row 1 designates ID 19 canonical and ID 18 excluded from canonical outcomes.
- The integrity preflight accepts this group only while the ledger exactly matches the current source IDs.
- The canonical-history helper returns ID 19 and omits ID 18; it does not delete or update either row.

## Fail-closed cases

The preflight stops the daily pipeline if it finds a duplicate group without exactly one valid resolved ledger mapping, or if a resolved mapping no longer matches the source table. This is intentional: an ambiguous history must not silently flow into outcome analysis.

## Remaining validation boundary

The TrendFoll web dashboard was one confirmed direct reader and has now been switched in code to the canonical RPC. Before it can work in production, apply `sql/migrate_prob017_canonical_reader_rpc.sql` after the reconciliation-ledger migration so PostgREST can expose the function. The RPC has not yet been executed against the live database, and other exports/notebooks/external applications still need an inventory. Therefore end-to-end closure remains pending.

No unique constraint on `(symbol, entry_date)` is proposed: later re-entry semantics remain distinct from immutable lifecycle identity `positions.id`.
