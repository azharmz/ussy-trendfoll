# Evidence — CURRENT Maximum-Holding Rule and Live OKTA State

**Checked:** 2026-10-14  
**Status:** REPOSITORY EXIT BEHAVIOR VERIFIED / LIVE DATABASE ROW OBSERVED / POST-MERGE PRODUCTION RUN PENDING

## Repository evidence

- Decision: [`DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md`](DECISION_CURRENT_EXIT_NO_MAX_HOLDING_PERIOD.md).
- CURRENT `positions.py::check_exits` has no age-only exit condition. Existing stop-loss and `close_raw < ema20` trend-break remain.
- Regression CI run `38552916021` passed; PR #17 merged as `d5c04e884958befb5c7ab550c4720282a7e354f5`.

## Read-only live database check

Queried Supabase project `USSY Trendfoll` (`rggtylvlrzzesrtumqzj`) without writing data.

Latest OKTA position row:
- `id`: 22
- `entry_date`: 2026-08-27
- `status`: `active`
- `exit_date`: null
- `stop_price`: 153.5911
- `mark_price`: 226.53
- `days_held`: null (this field is persisted on exit; the dashboard's active-row calendar-age display is separate)
- `updated_at`: 2026-10-14 03:48:45 UTC

Production status counts at the time of query: 21 active, 25 stop_loss, 22 trend_exit; no current `max_holding` rows in the grouped result.

## Deployment boundary

The latest successful daily pipeline run available at this check was run #83, ID `38507633128`, on branch `main`, head SHA `6a29253831474e61e36e2a018965aa276a6fca26`, started 2026-10-14 03:42:26 UTC and completed 03:49:27 UTC. The maximum-holding removal commit was created after that run, so this run does **not** verify execution of the post-removal code.

Therefore:
- The live database shows OKTA still active; its age alone has not closed it in the persisted row as of this check.
- Repository code and tests show no age-only exit.
- **A successful production daily run after PR #17's merge is still required** to verify that the live pipeline has executed the post-removal code. No production workflow was triggered manually as part of this read-only check.
- The deployed dashboard's HTML/browser version has not been independently inspected in this check.

## Next verification

After the next normal production daily run on the updated `main`, record its run ID/head SHA and re-query OKTA. Verify it remains active if neither stop-loss nor trend-break has fired. Do not manually close, update, or otherwise mutate the position for this verification.