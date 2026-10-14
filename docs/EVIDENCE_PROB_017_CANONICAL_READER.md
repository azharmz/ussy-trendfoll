# PROB-017 — Ledger-aware canonical history and integrity preflight

Status: **RPC APPLIED + DATABASE SMOKE TEST PASS / DASHBOARD PATCH IN DRAFT PR / EXTERNAL CONSUMER AUDIT PENDING**

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

- GitHub Actions run **PROB-017 Identity Tests #11** completed successfully on 2026-10-14: **7 passed in 0.34s**. This includes five identity-validator tests and two dashboard/RPC source-contract tests.
- The FSE-007/FSE-013 production regression and gap-aware stop execution regression workflows associated with the earlier PR commit also completed successfully.
- Production migration `20261014030257_prob017_canonical_position_history_rpc` was applied to Supabase project `USSY Trendfoll` on 2026-10-14.
- Live SQL smoke checks passed: source table remains at 66 rows; canonical RPC returns 65 rows; ANF `2026-08-26` returns only canonical ID 19; canonical output contains no duplicate `(symbol, entry_date)` groups; `anon` and `authenticated` can execute the RPC.
- The Supabase security advisor flags the public `SECURITY DEFINER` RPC as a warning because it is callable by `anon` and `authenticated`. This is currently intentional for the public dashboard, and the RPC is read-only with a fixed `search_path`; the existing `positions` table already has public SELECT access. This warning must be reviewed before treating the security review as complete.
- These checks validate database execution and the Python/source contracts; they do **not** prove the live dashboard is already using the RPC. The dashboard change remains in draft PR #16.

## Expected behavior for the known ANF identity

- IDs 18 and 19 remain present in `public.positions`.
- Ledger row 1 designates ID 19 canonical and ID 18 excluded from canonical outcomes.
- The integrity preflight accepts this group only while the ledger exactly matches the current source IDs.
- The canonical-history helper returns ID 19 and omits ID 18; it does not delete or update either row.

## Fail-closed cases

The preflight stops the daily pipeline if it finds a duplicate group without exactly one valid resolved ledger mapping, or if a resolved mapping no longer matches the source table. This is intentional: an ambiguous history must not silently flow into outcome analysis.

## External consumer inventory (2026-10-14)

A targeted read-only audit checked the accessible sibling repositories most likely to contain portfolio/position consumers: `ussy-data`, `ussy-signal`, `ussy-swing-actions`, `ussy-signal-actions`, `ussy-cross`, `ussy-pattbreak`, `ussy-oneil-patterns`, `ussy-canslim-core`, `ussy-fundamentals`, `ussy-swing-backtest`, and `ussy-governance`.

- `ussy-signal` syncs its own journal/state to Supabase project `owipcazgkxeplimbsnxs`.
- `ussy-swing-actions` uses project `pklhkbcglltayrdqeeph` and its own `daily_features` / `strategy_results` tables; its open positions are simulated from that project's trade data.
- `ussy-cross` uses project `wwhdcjbnnrtjwptkajci` and its own `positions` schema keyed by ticker/combo, not the TrendFoll `public.positions` schema.
- `ussy-pattbreak` builds open-position checkpoints from its own immutable T1 execution artifacts rather than reading TrendFoll's Supabase table.
- No references to the TrendFoll Supabase project ID were found in the targeted sibling-repository searches. GitHub code search is not a complete proof of absence, and unlisted repos, private external clients, notebooks, exports, and manual downloads cannot be ruled out.

The TrendFoll web dashboard remains the only confirmed direct consumer of this exact project/table in the inspected code. Its branch patch in draft PR #16 uses the canonical RPC, but has not been merged/deployed. Treat the cross-repository audit as **targeted, not exhaustive**. End-to-end closure remains pending dashboard deployment and a final production-consumer check.

No unique constraint on `(symbol, entry_date)` is proposed: later re-entry semantics remain distinct from immutable lifecycle identity `positions.id`.
