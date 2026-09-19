# EVIDENCE — EXIT-CAND-003 E1 First Real Operational Session

**Status:** PASS / EVIDENCE LOCKED  
**Contract:** `exit-cand-003-shadow-v1`  
**Production signal cohort:** 2026-09-17  
**Genuine T+1 session:** 2026-09-18  
**Observed production run:** GitHub Actions run `35409588002`, attempt 3, job `105872358482`

## Scope

This document locks the first admissible post-bootstrap-fix operational evidence for EXIT-CAND-003. It does not authorize a production exit change and does not alter frozen candidate parameters.

## Source and lineage confirmation

The production run verified exact SPY T0 and canonical production data at `as_of=2026-09-18`. The upstream READY snapshot was `production/ready/runs/2026-09-18.parquet`; shared EMA had passed its equivalence gate at READY cutoff 2026-09-18.

The run filled seven production positions registered on 2026-09-17 from the genuine next market session open on 2026-09-18, then registered seven CAND-003 shadows and advanced all seven once.

Admissible cohort:

| position_id | symbol | T+1 open / shadow entry | ATR14(T0) | initial operative stop |
|---:|---|---:|---:|---:|
| 28 | ATRC | 58.5099983215332 | 2.0018417032513494 | 54.5063149150305 |
| 29 | CRWD | 246.97999572753906 | 12.872018407419796 | 221.23595891269946 |
| 30 | ILMN | 249.1300048828125 | 10.099256394987817 | 228.93149209283686 |
| 31 | IOVA | 10.119999885559082 | 0.559465325594614 | 9.001069234369854 |
| 32 | NTRA | 365.7799987792969 | 12.120329533943819 | 341.53933971140924 |
| 33 | SMTC | 182.3300018310547 | 12.01359107715161 | 158.30281967675148 |
| 34 | TMO | 656.6099853515625 | 15.821037444905862 | 624.9679104617508 |

For every row, independent arithmetic confirms:

`initial_stop = T+1_open - 2 * ATR14(T0)`.

## Ledger integrity

Live database inspection after the run found exactly **7** session-ledger rows for 2026-09-18 and exactly **7** distinct `(position_id, session_date, contract_version)` keys.

The historical pre-fix quarantine remains exactly **27** rows. None of the seven 2026-09-18 rows belongs to that quarantine.

All seven rows link to real production positions 28–34. Their production `entry_date` is 2026-09-17 and their persisted `realistic_entry_price` equals the corresponding 2026-09-18 `open_raw`.

## Independent frozen-semantic recomputation

All seven session rows were checked against their persisted OHLC and frozen contract.

For every position:

1. `operative_stop_before == initial_stop`; therefore the session-t operative stop existed before evaluation of session t.
2. `open_raw > operative_stop_before`; no gap-through stop occurred.
3. `low_raw > operative_stop_before`; no intraday stop touch occurred.
4. `close_raw > ema20`; no EMA20 trend exit occurred.
5. This is observation day 1, so the 45-session boundary did not apply.
6. Persisted hypothetical exit reason and price are null, matching independent recomputation.
7. `gap_checked_first=true` and `chandelier_arms_next_session=true`.

IOVA is the useful no-lookahead boundary case. Its session-t Chandelier was 9.394418793166894, above the pre-session operative stop 9.001069234369854. The session was evaluated against **9.001069234369854**, while **9.394418793166894** was persisted only as `next_operative_stop`. Thus the session-t Chandelier did not retroactively arm on the same session.

For the other six positions, the session-t Chandelier did not exceed the existing operative stop, so the next operative stop remained unchanged.

No touch fill was generated, so there is no fill outside observed OHLC. Gap-before-touch ordering is consistent with the actual OHLC for all seven rows.

## Comparator non-feedback / production state

At evidence inspection time all seven linked production positions remained `active` with null production exit date and price. The shadow ledger stored production comparison fields observationally; the CAND-003 module contract does not update the production `positions` table.

The production run log reported:

- `[shadow003] registered 7 genuine T+1 shadow position(s).`
- `[shadow003] advanced 7 active shadow(s); hypothetical exits=0.`

No evidence in this E1 cycle indicates shadow feedback into production state.

## E1 verdict

All frozen E1 checks pass:

- genuine production T+1 session: **PASS**
- real production position + real market session: **PASS**
- live invariant-key uniqueness: **PASS**
- quarantine/synthetic exclusion: **PASS**
- independent recomputation: **PASS**
- pre-existing operative stop: **PASS**
- Chandelier next-session arming: **PASS**
- gap-before-touch ordering: **PASS**
- production comparator non-feedback: **PASS**

**E1 = COMPLETE / PASS / EVIDENCE LOCKED.**

This closes only the first-real-session gate. E2–E4 remain observational and must accumulate naturally. Current authorization remains **NO PRODUCTION EXIT CHANGE**.
