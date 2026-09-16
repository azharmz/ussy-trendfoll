# Full Signal Engine Audit — Evidence 12: Latest Volume Completeness

Status: **ROOT CAUSE IDENTIFIED / NEW-SESSION PREVENTION VALIDATED / SEP-14 HISTORICAL FACTS NOW NORMALIZED IN CURRENT READY / RECONCILIATION MECHANISM GOVERNANCE STILL OPEN / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

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

- 933 / 1,223 (76.29%) have terminal volume below every one of their prior 50 observations;
- median terminal-volume / previous-session-volume ratio = 0.1629;
- median cross-sectional terminal-volume / prior-50 median-volume ratio = 0.1520;
- 875 securities have terminal volume <25% of their prior-50 median;
- 1,025 securities have terminal volume <50% of their prior-50 median.

This independently explains the earlier mass concentration of terminal volume percentile at the theoretical 2% minimum for a 50-observation percentile window. The percentile formula was responding to supplied volume facts; the terminal volume facts themselves were anomalously incomplete.

## Upstream code trace

The traced `azharmz/ussy-data` updater contained an append-only date rule:

```python
additions = downloaded[downloaded["date"] > last_date].copy()
```

The upstream repository also contains a finalization wrapper that excludes the current New York trading-day candle before 18:00 America/New_York and explicitly documents the risk of accepting an unfinished daily Yahoo candle.

This trace established a plausible mechanism for the original Sep-14 anomaly, but code inspection alone did not prove whether some later upstream path/rebuild could replace the affected historical facts. That question is resolved empirically below.

## Post-refresh validation — finalized new session

After upstream production published a refreshed READY containing the next finalized market session, the exact same frozen latest-session diagnostic was rerun without changing TrendFoll volume thresholds or percentile semantics.

- run: `35056685958`
- job: `104668244734`
- head: `ecd1c9c080f2e3b5f2a1271766fd9b6553b376fb`
- conclusion: `SUCCESS`
- artifact: `latest-volume-completeness-3`
- artifact id: `10431260053`
- artifact SHA-256: `a45707a1a7154eeb010c3f7edf316549263820776ff7546254ddb453a7772804`

Observed refreshed R2 READY terminal date: `2026-09-15`.

Among 1,220 securities analyzed on that common latest date:

- 19 / 1,220 (1.56%) have terminal volume below every prior-50 observation;
- median terminal / previous-session volume = 0.9939;
- median terminal / prior-50 median volume = 1.0771;
- 32 securities are <25% of prior-50 median;
- 92 securities are <50% of prior-50 median.

The mass terminal anomaly disappeared on the newly finalized session.

## Date-specific historical reconciliation audit — Sep-14

A new research-only diagnostic then re-read the current READY but targeted the historical `2026-09-14` rows directly rather than the terminal date.

Workflow: `Signal Engine Sep14 Volume Reconciliation Audit`

- diagnostic script commit: `7be9d8f9e6e570429eb7a0a76d12823247be3283`
- workflow/head commit: `bfc2194c85adfd577da797458e372b099cef8144`
- run: `35078341639`
- job: `104735984047`
- conclusion: `SUCCESS`
- artifact: `sep14-volume-reconciliation-1`
- artifact id: `10438488703`
- artifact SHA-256: `4a370e50753f7ae94670fc8102c47e5dfc5a96f169f83fd100bb29b9f4151f49`

Current READY latest date remained `2026-09-15`, while the audit evaluated 1,223 historical rows dated `2026-09-14`.

Observed current Sep-14 distribution:

- below every prior-50 observation: **13 / 1,223 = 1.06%**, versus original **933 / 1,223 = 76.29%**;
- median Sep-14 / previous-session volume: **1.1159**, versus original **0.1629**;
- median Sep-14 / prior-50 median volume: **1.0617**, versus original **0.1520**;
- Sep-14 volume <25% prior-50 median: **39**, versus original **875**;
- Sep-14 volume <50% prior-50 median: **76**, versus original **1,025**.

This is decisive empirical evidence that the Sep-14 historical volume facts exposed through current READY are no longer the partial-volume population observed in the baseline run. The affected date has been normalized/reconciled somewhere in the upstream publication/rebuild path.

The result also corrects an earlier over-strong inference from the append-only incremental updater: although that individual code path cannot replace `date == last_date`, the complete upstream system evidently has another path capable of rebuilding or republishing historical facts. The exact mechanism and its invariant guarantees still require upstream governance before declaring the data-contract defect permanently remediated.

## Classification

### TrendFoll volume-percentile formula

**MATCH / FORMULA BEHAVES AS IMPLEMENTED.**

No TrendFoll threshold/formula correction is supported by this anomaly.

### New-session terminal volume finalization

**MATCH / EMPIRICALLY VALIDATED FOR SEP-15 REFRESH.**

The terminal mass-low-volume signature disappeared on the next finalized session.

### Sep-14 historical facts in current READY

**MATCH / EMPIRICALLY RECONCILED IN CURRENT READY.**

The original Sep-14 partial-volume population has disappeared when the exact historical date is re-read from current READY.

### Upstream reconciliation contract

**NEEDS GOVERNANCE / MECHANISM NOT YET FROZEN AS A GUARANTEE.**

The empirical repair is established, but the audit has not yet proven which upstream rebuild/reconciliation path performed it or that future same-date partial bars are guaranteed to be repaired under all relevant paths.

## Remediation boundary

Remaining governance belongs upstream in `ussy-data`, not in TrendFoll threshold tuning. A durable contract should establish:

1. unfinished current-session candles remain excluded;
2. previously stored partial same-date candles are reconcilable after finalization;
3. READY publication does not silently promote materially incomplete terminal volume as finalized data;
4. reconciliation preserves identity/security mapping and unrelated valid history;
5. a regression/health check demonstrates the behavior continuously.

No production mutation is authorized by this evidence document.

## Audit disposition

FSE-015 is no longer blocked on proving whether Sep-14 remained historically corrupted: **it does not in current READY**. The remaining question is narrower and upstream-governance-oriented: identify/freeze the mechanism that produced the repair and decide whether an explicit READY completeness guard is required.
