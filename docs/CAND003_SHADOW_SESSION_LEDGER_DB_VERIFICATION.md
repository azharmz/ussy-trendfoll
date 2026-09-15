# CAND-003 Shadow Ledger DB Verification

Supabase project: USSY Trendfoll (`rggtylvlrzzesrtumqzj`).

Verified on 2026-09-16 Asia/Makassar:

- `exit_candidate003_shadow_sessions` exists.
- RLS is enabled.
- SELECT policy exists for `anon, authenticated`.
- Effective grants: anon=SELECT; authenticated=SELECT; service_role=SELECT,INSERT.
- Security advisor returned zero findings.
- Performance advisor no longer reports an unindexed foreign key after adding the `shadow_id` index.
- Ledger currently contains zero rows and zero duplicate invariant keys; first real row is intentionally pending promotion and a real production-shadow session.
