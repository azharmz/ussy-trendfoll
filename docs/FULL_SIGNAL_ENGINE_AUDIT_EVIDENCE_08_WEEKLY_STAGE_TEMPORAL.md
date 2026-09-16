# Full Signal Engine Audit — Evidence 08: Weekly Stage Temporal Semantics

Status: **EMPIRICAL TEST EVIDENCE / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

Branch: `research/exit-development-hypotheses`

## Scope

This evidence closes the temporal/calendar questions around the current weekly Stage implementation:

- `compute_weekly_stage_features()` resamples daily raw close with `W-FRI` and `.last()`;
- weekly Stage rows are merged back to daily rows with backward-as-of semantics;
- audit target is whether future Friday information can leak into Monday–Thursday and whether US holiday-shortened weeks create leakage or unintended lag.

## Test gate

Research-only test:

- `tests/test_weekly_stage_temporal.py`

Workflow:

- `.github/workflows/audit-weekly-stage-temporal.yml`
- workflow name: `Signal Engine Weekly Stage Temporal Audit`
- run ID: `35036545474`
- branch: `research/exit-development-hypotheses`
- head SHA: `ee0395858c553273b39442d3e5ea6886bddfdf92`
- job ID: `104606820914`
- conclusion: **SUCCESS**
- pytest result: **4 passed in 0.73s**

## Cases tested

1. **Normal Monday–Thursday behavior**
   - Daily rows before Friday may only receive the most recent completed Friday-labeled Stage state through backward-as-of merge.
   - The current week's Friday-labeled value is not available to Monday–Thursday rows.

2. **Friday availability**
   - Once the Friday daily bar exists, the W-FRI weekly bucket is knowable at that Friday close and may be used by the Friday daily row after close.

3. **Good Friday 2026**
   - Good Friday (2026-04-03) is a US market holiday.
   - The holiday-shortened week's last trading observation is Thursday, but pandas W-FRI labels the bucket Friday.
   - Because there is no Friday daily row, the Friday-labeled weekly state is not merged into Thursday; Thursday continues to use the prior completed Friday state.
   - The new holiday-week state becomes available to the next trading row after the Friday label, preventing future-Friday leakage at the cost of an intentional calendar-label lag across the holiday.

4. **Labor Day 2026**
   - Monday 2026-09-07 is a non-session.
   - The following Tuesday–Thursday rows continue to use the previous completed Friday state; the new week's state is not leaked before Friday.

## Classification

Current weekly Stage temporal mechanics: **MATCH / TEMPORALLY CAUSAL**.

No look-ahead defect was reproduced in the tested W-FRI/backward-as-of path.

The Good-Friday behavior is a documented semantic consequence of Friday-labeled weekly buckets, not future-data leakage: a holiday-shortened week whose final trading bar is Thursday is not exposed to Thursday itself because the weekly observation is labeled on the non-trading Friday. This creates a conservative lag until the next trading session.

This evidence does **not** validate the economic/methodological correctness of the Stage1–4 approximation. That remains separately classified `APPROXIMATION` and still requires authoritative Weinstein-methodology comparison.

## Checklist disposition

Closed by this evidence:

- D2.6 — weekly W-FRI labeling around market holidays.
- D2.7 — no weekly look-ahead through resample/as-of merge.
- G5 — no future-Friday information leaked into Monday–Thursday.
- G6 — holiday-shortened-week behavior explicitly tested and documented.
- K6 — holiday/calendar edge-case test exists and passes for the weekly Stage path.

No production correction is warranted from this temporal test evidence.