# Full Signal Engine Audit — Evidence 12: Latest Volume Completeness

Status: **ROOT CAUSE IDENTIFIED / NEW-SESSION PREVENTION EMPIRICALLY VALIDATED / HISTORICAL RECONCILIATION STILL OPEN / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Scope

Investigate the anomalous terminal `breakout_volume_percentile` population observed in R2 READY and determine whether it is caused by the TrendFoll percentile formula or by upstream OHLCV completeness.

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

- 933 / 1,223 (76.29%) have terminal volume below **every** one of their prior 50 observations;
- median terminal-volume / previous-session-volume ratio = 0.1629;
- median cross-sectional terminal-volume / prior-50 median-volume ratio = 0.1520;
- 875 securities have terminal volume <25% of their prior-50 median;
- 1,025 securities have terminal volume <50% of their prior-50 median.

This independently explains the earlier mass concentration of terminal volume percentile at the theoretical 2% minimum for a 50-observation percentile window. The percentile formula is responding to the supplied volume facts; the terminal volume facts themselves were anomalously incomplete.

## Upstream code trace

The upstream `azharmz/ussy-data` updater has an append-only date rule:

```python
additions = downloaded[downloaded["date"] > last_date].copy()
```

Therefore a partial same-date daily candle that has already entered historical storage is not replaced by a later download of the same date.

The upstream repository also contains a finalization wrapper that excludes the current New York trading-day candle before 18:00 America/New_York. Its module documentation explicitly identifies the historical risk: accepting a current daily Yahoo candle while the session is unfinished can permanently freeze a partial OHLCV/volume bar because production updating is append-only by date.

These facts are mechanically consistent with the Sep-14 R2 terminal-volume anomaly:

`partial same-date candle accepted historically -> append-only rule preserves it -> READY exports it -> TrendFoll volume percentile ranks it near the bottom`.

## Post-refresh validation — finalized new session

After upstream production published a refreshed READY containing the next finalized market session, the exact same frozen diagnostic was rerun without changing TrendFoll volume thresholds or percentile semantics.

Workflow: `Signal Engine Latest Volume Completeness Audit`

- run: `35056685958`
- job: `104668244734`
- head: `ecd1c9c080f2e3b5f2a1271766fd9b6553b376fb`
- conclusion: `SUCCESS`
- artifact: `latest-volume-completeness-3`
- artifact id: `10431260053`
- artifact SHA-256: `a45707a1a7154eeb010c3f7edf316549263820776ff7546254ddb453a7772804`

Observed refreshed R2 READY terminal date: `2026-09-15`.

Among 1,220 securities analyzed on that common latest date:

- 19 / 1,220 (1.56%) have terminal volume below every one of their prior 50 observations;
- median terminal-volume / previous-session-volume ratio = 0.9939;
- median cross-sectional terminal-volume / prior-50 median-volume ratio = 1.0771;
- 32 securities have terminal volume <25% of their prior-50 median;
- 92 securities have terminal volume <50% of their prior-50 median.

The mass anomaly therefore disappears on the newly finalized session: 76.29% -> 1.56% for the below-all-prior-50 population, while the median volume/prior-50-median ratio normalizes from 0.1520 -> 1.0771.

This is strong empirical evidence that the TrendFoll percentile formula was not the root cause and that upstream finalization prevents the same terminal-volume failure mode for the newly published session.

It does **not** prove that the historically persisted Sep-14 partial bars were repaired. Because the traced updater is append-only for dates at or before `last_date`, historical same-date reconciliation remains a distinct open remediation requirement.

## Classification

### TrendFoll volume-percentile formula

**MATCH / FORMULA BEHAVES AS IMPLEMENTED.**

The extreme Sep-14 terminal percentile population is not evidence that the percentile ranking formula itself is defective. The same formula produces a non-anomalous population when supplied the refreshed finalized Sep-15 volume facts.

### New-session terminal volume finalization

**MATCH / EMPIRICALLY VALIDATED FOR THE REFRESHED SEP-15 SESSION.**

The post-refresh diagnostic no longer shows a mass partial-volume signature. This closes the immediate new-session prevention question for the observed Sep-15 publication, subject to normal ongoing pipeline governance.

### Historical same-date completeness

**MISMATCH / RECONCILIATION REQUIREMENT REMAINS OPEN.**

The existing append-only rule does not itself repair a partial bar already stored for an earlier date. Sep-14 historical reconciliation has not yet been empirically demonstrated.

### Remediation boundary

The remaining correction belongs upstream in `ussy-data`, not in TrendFoll threshold tuning.

Required upstream behavior before governed production acceptance of historical reconciliation:

1. unfinished current-session candles remain excluded;
2. previously stored partial same-date candles must be repairable/reconcilable after the session is finalized;
3. READY publication must not silently promote materially incomplete terminal volume as finalized data;
4. correction must preserve historical identity/security mapping and avoid rewriting unrelated valid history;
5. TrendFoll volume threshold/percentile semantics must not be tuned to compensate for bad upstream facts.

No upstream production correction is authorized by this evidence document. This audit freezes the root cause, validates the observed new-session prevention behavior, and keeps historical reconciliation explicitly open.

## Follow-up validation

The next governed validation target is historical reconciliation, specifically the affected Sep-14 population. A valid upstream repair must demonstrate that previously persisted partial same-date observations can be corrected without altering unrelated valid history. After such a mechanism is implemented, rerun a date-specific comparison against Sep-14 rather than relying only on the newest terminal date.
