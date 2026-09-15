# CAND-003 Shadow Session Ledger — Promotion Boundary

Promotion of this branch into the authoritative execution branch is an engineering/evidence change only.

It does not authorize any production exit-policy change and does not change the frozen CAND-003 representation.

After promotion, the next scheduled production pipeline session should be allowed to populate real rows in `exit_candidate003_shadow_sessions`. The first operational review must verify:

1. one row per `(position_id, session_date, contract_version)`;
2. no duplicate invariant keys;
3. operative stop matches pre-session mutable shadow state;
4. any Chandelier ratchet appears only as next-session stop;
5. hypothetical gap/touch fills are feasible against observed OHLC;
6. production comparison fields are observational and do not alter production state;
7. rerunning the same session is idempotent or fails closed on divergence.

No synthetic live row should be inserted to satisfy this milestone.
