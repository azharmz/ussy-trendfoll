# Full Signal Engine Audit — Evidence 12: Latest Volume Completeness

Status: **ROOT CAUSE IDENTIFIED / NEW-SESSION PREVENTION VALIDATED / RESIDUAL SEP-14 CORRUPTION DETERMINISTICALLY REPAIRED + VERIFIED / HISTORICAL MAJORITY SELF-HEAL PROVEN EMPIRICALLY BUT FORENSIC PROVENANCE OPTIONAL-OPEN / NO TRENDFOLL PRODUCTION CHANGE**

## Scope

Investigate the anomalous terminal `breakout_volume_percentile` population observed in R2 READY and distinguish:

1. TrendFoll formula correctness;
2. prevention of unfinished new-session bars;
3. deterministic remediation of residual corrupted Sep-14 history;
4. forensic provenance of the earlier majority self-healing event.

These are separate questions and must not be collapsed into one unresolved upstream-provenance finding.

## Baseline empirical run — anomalous READY

Workflow: `Signal Engine Latest Volume Completeness Audit`

- run: `35052179872`
- job: `104654742433`
- head: `e17c875662907102f348e4a78a5379be149d0e3c`
- conclusion: `SUCCESS`
- artifact: `latest-volume-completeness-2`
- artifact id: `10429173250`
- artifact SHA-256: `20579e261afee9eee5355cc2bf9e880e01a47096109f776bfa46abd75d1e55a0`

Observed R2 READY terminal date: `2026-09-14`.

Among 1,223 securities with a row on that common latest date:

- 933 / 1,223 (76.29%) had terminal volume below every prior-50 observation;
- median terminal / previous-session volume = 0.1629;
- median terminal / prior-50 median volume = 0.1520;
- 875 securities were <25% of prior-50 median;
- 1,025 securities were <50% of prior-50 median.

This explained the mass concentration of `breakout_volume_percentile` at its theoretical 2% minimum. The TrendFoll percentile formula was ranking supplied volume facts; the supplied Sep-14 volume facts were anomalously incomplete.

## Upstream prevention trace

The incremental updater contains an append-only trigger:

```python
additions = downloaded[downloaded["date"] > last_date].copy()
```

A separate finalization wrapper, introduced by upstream commit `f805a59c217e0056cbbe80b2728fbd0877b87135`, excludes the current New York trading-day candle before 18:00 America/New_York. This prevents the observed failure mode from accepting an unfinished current-session Yahoo daily candle through that production path.

## Post-refresh validation — finalized new session

The same TrendFoll diagnostic was rerun after refreshed READY publication without changing TrendFoll thresholds or percentile semantics.

- run: `35056685958`
- job: `104668244734`
- head: `ecd1c9c080f2e3b5f2a1271766fd9b6553b376fb`
- conclusion: `SUCCESS`

Observed terminal date: `2026-09-15`.

Among 1,220 securities:

- below every prior-50 observation: 19 / 1,220 = 1.56%;
- median terminal / previous-session volume = 0.9939;
- median terminal / prior-50 median volume = 1.0771;
- <25% prior-50 median = 32;
- <50% prior-50 median = 92.

The mass terminal anomaly disappeared on the finalized new session.

## Incident workstream — final residual audit before targeted repair

The upstream incident workstream created `src/repair_partial_daily_bar.py`. The utility compares one historical R2 daily OHLCV row against a fresh finalized Yahoo row for the same date. In `--apply` mode it replaces only the targeted date in the affected security history, preserving other dates and the standard OHLCV schema.

Final no-write audit before targeted repair:

- run: `35063409654`
- job: `104688391199`
- checkout/head: `4fbb8caff9ebd653141c7f44b4b7ddd5c6d0fa15`
- conclusion: `SUCCESS`
- target: `2026-09-14`
- eligible histories: 1,300
- changed: **2**
- missing fresh source rows: **19**
- processing errors: **0**

The two residual mismatches were:

- `HUBB` / `US4435106079`: Sep-14 volume `61,875 -> 457,222`, with associated finalized OHLC corrections;
- `SITC` / `US82981J8514`: Sep-14 volume `74,352 -> 831,377`, with associated finalized OHLC corrections.

This audit is important for interpretation: by this point the original mass Sep-14 corruption had already reduced to only two detectable residual mismatches among histories for which a fresh comparison could be made. Therefore the majority had self-healed earlier; that earlier self-healing is distinct from the targeted repair below.

## Deterministic targeted write repair

Repair run:

- run: `35065793106`
- job: `104695656869`
- conclusion: `SUCCESS`
- workflow steps explicitly executed `Apply targeted Sep14 finalized bar repair` followed by `Verify targeted Sep14 bars are clean`.

Repair result:

- changed: **2**
- missing: **0**
- errors: **0**

Immediate post-write verification:

- changed: **0**
- missing: **0**
- errors: **0**

Therefore the residual HUBB/SITC corruption has explicit, deterministic, repeatable remediation provenance through `repair_partial_daily_bar.py`; it is not an unexplained side effect of generic republication.

## Full derived-state rebuild after repair

After the targeted historical write, the full upstream derived state was rebuilt.

- rebuild commit: `bca86d829f70cc1871143e345d5b8ebee4d63ec1`
- Production Daily run: `35066010307`
- job: `104696335029`
- conclusion: `SUCCESS`

The successful workflow executed finalized OHLCV update, READY export, adjusted EMA candidate build, and adjusted EMA validation/promotion. Incident evidence records:

- READY: 1,227 securities / 367,522 rows;
- latest finalized date: `2026-09-15`;
- unfinished Sep-16 excluded;
- EMA affected securities rebuilt: 2;
- EMA equivalence numeric failures: 0;
- classification mismatches: 0;
- max absolute error: 0.0;
- production EMA pointer promoted.

## Downstream TrendFoll verification

After repair + derived-state rebuild, TrendFoll volume-percentile audit was rerun:

- run: `35067332157`
- job: `104700496198`
- conclusion: `SUCCESS`
- diagnostic step: `Run diagnostic audit` = SUCCESS.

Incident evidence records the exact 2% population falling from `935 / 1,223` to `19`, with the distribution returning to normal. This closes the downstream consequence chain for the targeted remediation without any TrendFoll threshold tuning.

## Later date-specific historical confirmation

A separate TrendFoll research-only diagnostic subsequently re-read current READY and targeted historical `2026-09-14` directly:

- run: `35078341639`
- job: `104735984047`
- conclusion: `SUCCESS`

For 1,223 Sep-14 rows in current READY:

- below every prior-50 observation: 13 / 1,223 = 1.06%, versus original 76.29%;
- median Sep-14 / previous-session volume = 1.1159, versus original 0.1629;
- median Sep-14 / prior-50 median volume = 1.0617, versus original 0.1520;
- <25% prior-50 median = 39, versus original 875;
- <50% prior-50 median = 76, versus original 1,025.

This independently confirms that current READY no longer exposes the original Sep-14 partial-volume population.

## Classification

### TrendFoll volume-percentile formula

**MATCH / FORMULA BEHAVES AS IMPLEMENTED.**

No TrendFoll threshold/formula correction is supported by this incident.

### New-session terminal finalization

**MATCH / EMPIRICALLY VALIDATED FOR THE OBSERVED POST-FIX PUBLICATION.**

The unfinished-current-session prevention path exists and the next finalized session did not reproduce the mass-low-volume signature.

### Residual Sep-14 remediation correctness

**PASS / DETERMINISTIC REPAIR + IMMEDIATE VERIFICATION + DERIVED-STATE REBUILD + DOWNSTREAM VERIFICATION.**

The remaining HUBB/SITC mismatches were explicitly identified, written through the one-date repair utility, immediately re-audited clean, propagated through the full derived-state rebuild, and verified downstream in TrendFoll.

### Historical majority self-healing provenance

**FORENSIC QUESTION OPEN / NOT A BLOCKER TO THE PROVEN RESIDUAL REMEDIATION CHAIN.**

The no-write audit immediately before targeted repair found only two residual mismatches, so most of the original Sep-14 population had already self-healed. The exact earlier workflow/run responsible for every self-healed historical row has not been isolated here. That is a separate forensic-provenance question and must not be used to describe the residual repair itself as unexplained.

## FSE-015 disposition

FSE-015 must distinguish remediation correctness from optional historical forensics:

- **A. Are the residual corrupted Sep-14 observations known at final audit deterministically repaired and verified? YES.**
- **B. Is the exact earlier workflow/run that self-healed the majority of Sep-14 rows fully isolated? NOT YET in this evidence; forensic follow-up may remain open.**

For the TrendFoll signal-engine audit, the observed volume-completeness incident no longer justifies a TrendFoll correction. The upstream incident has a demonstrated prevention path, an explicit one-date residual repair mechanism, immediate verification, a successful derived-state rebuild, and successful downstream verification.

Any remaining work should be scoped as upstream durability/forensic governance (for example, continuous completeness guards or reconstructing the earlier majority self-heal provenance), not as an unresolved TrendFoll formula defect.
