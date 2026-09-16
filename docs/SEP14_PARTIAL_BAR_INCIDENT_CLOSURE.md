# Sep 14 Partial Daily-Bar Incident — Closure Record

Status: **CLOSED / REMEDIATED / VERIFIED**

Date closed: 2026-09-16

## Incident

A production update was triggered during the US trading session on 2026-09-14. Yahoo daily OHLCV could therefore expose the still-forming 2026-09-14 daily candle. The upstream updater accepted that current-session row into R2. The most visible downstream symptom was a systemic collapse of `breakout_volume_percentile` to its 50-session minimum grid value (2%).

## Root cause

The defect was not the frozen percentile formula. The data boundary allowed a current US-market daily bar to be promoted before the session was finalized.

The updater can reconcile overlapping dates when a later finalized session arrives, so most affected per-security histories subsequently self-healed. A finalized-date audit of 1,300 eligible histories found only two residual mismatches and zero processing errors.

## Remediation

Upstream `azharmz/ussy-data` now runs the production updater through a finalization wrapper that, while the US market day is not finalized, excludes the current New York calendar date while still allowing previously closed dates to update. This avoids blocking unrelated CI/workflow execution during market hours.

Residual finalized-bar repair was limited to:

- HUBB (`US4435106079`): Sep14 volume 61,875 -> 457,222, with low/close also corrected.
- SITC (`US82981J8514`): Sep14 volume 74,352 -> 831,377, with high/close also corrected.

Post-write verification for those two histories returned `changed=0, missing=0, errors=0` against finalized Yahoo data.

## Derived-state verification

After repair, the upstream production pipeline was rebuilt. READY remained 1,227 securities / 367,522 rows with latest finalized market date 2026-09-15. Adjusted-EMA equivalence validation completed with zero numeric failures, zero classification mismatches, and max error 0.0; the production EMA pointer was promoted normally.

## Downstream verification

`ussy-trendfoll` volume-percentile diagnostic was rerun against rebuilt R2 READY data.

Before remediation:

- 935 / 1,223 latest rows (76.5%) had percentile exactly 2%.

After remediation:

- 19 / 1,220 latest rows had percentile exactly 2%.
- median percentile = 58%.
- 329 latest rows had percentile >= 80%.
- target names: BBY 58%, CHRD 8%, COKE 76%, OKTA 84%, OXY 90%, PR 78%, SU 62%.

This removes the systemic minimum-percentile cluster and supports the partial-current-session OHLCV diagnosis.

## Governance decision

- Incident remediation is closed.
- The frozen volume-percentile formula is unchanged.
- Historical Supabase/watchlist observations are not retroactively rewritten; contaminated historical observations remain as audit evidence.
- Further work returns to the signal-engine execution audit rather than tuning Tradability to this incident.

## Evidence

- Sep14 finalized-history audit run: `azharmz/ussy-data` Actions run `35063409654`.
- Targeted repair verification run: `azharmz/ussy-data` Actions run `35065793106`.
- Derived-state rebuild: `azharmz/ussy-data` Production Daily run `35066010307`.
- Downstream volume-percentile verification: `azharmz/ussy-trendfoll` run `35067332157`.
