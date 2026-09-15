# EVIDENCE — STOP-EXEC-001 CURRENT Gap-Through Audit

Status: **EVIDENCE LOCKED / EXECUTION-FEASIBILITY DEFECT OBSERVED / NO PRODUCTION CHANGE**

## Authoritative run

- workflow: `STOP-EXEC-001 Gap-Through Audit`
- run: `34967551005`
- job: `104375527910`
- head SHA: `890218c3d80bc3c9e7cbc4f991e6f08a50766c60`
- conclusion: `SUCCESS`
- artifact: `stop-exec001-1`
- artifact ID: `10395628680`
- artifact SHA256: `f8a5abce518acd87793fec510b8ec668ac6e3fdf495ba1db409007fea99fee56`
- artifact expires: `2026-12-14`

Repository tests passed before the audit step.

## Frozen corpus

- READY snapshot / evaluation end: `2026-08-28`
- deterministic development sample: first 100 securities
- history requested / loaded: `100 / 100`
- research-eligible securities: `87`
- history rows: `519,288`
- eligible rows: `470,890`
- pre-roll: `500` bars
- eligible onsets: `1,545`
- exact paired comparable events: `1,524`
- EMA basis: `adj_close`
- history: `R2 backtest/ohlcv/{security_id}.parquet`
- universe authority: `R2 production/ready/current.json`

## Frozen comparison

Only execution representation changed.

`CURRENT_EXACT_STOP`:

- T+1 Open entry
- fixed stop = entry − 2×ATR14(T0)
- if daily Low touches/breaches stop, fill exactly at stop
- EMA20 and max-45 behavior unchanged

`GAP_AWARE_DIAGNOSTIC`:

- identical entry, stop, EMA20 and max-holding contract
- if Open <= stop, fill at observed Open
- otherwise Low <= stop fills exactly at stop

No parameters were tuned and this diagnostic does not mutate production.

## Results

### Gap-through incidence

- CURRENT stop events: `839`
- gap-through events: `93`
- ordinary stop-touch events: `746`
- gap-through fraction of CURRENT stop events: `11.0846%`
- gap-through fraction of all paired events: `6.1024%`

Therefore the exact-stop assumption is infeasible on 93 governed events: the session was already below the operative stop at Open.

### Gap slippage relative to stop

For the 93 gap-through events, `(Open / Stop - 1)`:

- median: `-1.1347%`
- Q25: `-2.9748%`
- Q75: `-0.5554%`
- worst: `-17.0903%`

### Aggregate realized outcome

CURRENT exact-stop:

- median realized return: `-3.4648%`
- positive rate: `33.0052%`

Gap-aware diagnostic:

- median realized return: `-3.5616%`
- positive rate: `33.0052%`

Paired gap-aware minus CURRENT:

- median delta: `0.0000 pp`
- mean delta: `-0.1291 pp`
- changed events: `93 / 1,524` (`6.1024%`)
- worst paired delta: `-16.4767 pp`

The unchanged paired median is expected because most events do not gap through the stop; it does not remove the execution-feasibility defect on affected events.

## Terminal interpretation

**CURRENT EXACT-STOP EXECUTION FEASIBILITY DEFECT OBSERVED.**

The frozen CURRENT representation overstates attainable stop fills when a session opens below the stop. This is an engineering/execution-contract defect, not evidence for changing the 2×ATR parameter or for tuning EXIT-CAND-003.

STOP-EXEC-001 is complete as a diagnostic. Any correction to authoritative production exit execution requires its own explicit implementation/migration governance. EXIT-CAND-003 remains frozen and shadow-only.
