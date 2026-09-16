# Full Signal Engine Audit — Evidence 12: Latest Volume Completeness

Status: **ROOT CAUSE IDENTIFIED / UPSTREAM DATA-CONTRACT DEFECT / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Scope

Investigate the anomalous terminal `breakout_volume_percentile` population observed in the current R2 READY dataset and determine whether it is caused by the TrendFoll percentile formula or by upstream OHLCV completeness.

## Empirical run

Workflow: `Signal Engine Latest Volume Completeness Audit`

- run: `35052179872`
- job: `104654742433`
- head: `e17c875662907102f348e4a78a5379be149d0e3c`
- conclusion: `SUCCESS`
- artifact: `latest-volume-completeness-2`
- artifact id: `10429173250`
- artifact SHA-256: `20579e261afee9eee5355cc2bf9e880e01a47096109f776bfa46abd75d1e55a0`

Observed current R2 READY terminal date: `2026-09-14`.

Among 1,223 securities with a row on that common latest date:

- 933 / 1,223 (76.29%) have terminal volume below **every** one of their prior 50 observations;
- median terminal-volume / previous-session-volume ratio = 0.1629;
- median cross-sectional terminal-volume / prior-50 median-volume ratio = 0.1520;
- 875 securities have terminal volume <25% of their prior-50 median;
- 1,025 securities have terminal volume <50% of their prior-50 median.

This independently explains the earlier mass concentration of terminal volume percentile at the theoretical 2% minimum for a 50-observation percentile window. The percentile formula is responding to the supplied volume facts; the terminal volume facts themselves are anomalously incomplete.

## Upstream code trace

The upstream `azharmz/ussy-data` updater currently has an append-only date rule:

```python
additions = downloaded[downloaded["date"] > last_date].copy()
```

Therefore a partial same-date daily candle that has already entered historical storage is not replaced by a later download of the same date.

The upstream repository now also contains a finalization wrapper that excludes the current New York trading-day candle before 18:00 America/New_York. Its module documentation explicitly identifies the historical risk: accepting a current daily Yahoo candle while the session is unfinished can permanently freeze a partial OHLCV/volume bar because production updating is append-only by date.

These two facts are mechanically consistent with the observed R2 terminal-volume anomaly:

`partial same-date candle accepted historically -> append-only rule preserves it -> READY exports it -> TrendFoll volume percentile ranks it near the bottom`.

## Classification

### TrendFoll volume-percentile formula

**MATCH / FORMULA BEHAVES AS IMPLEMENTED.**

The extreme terminal percentile population is not evidence that the percentile ranking formula itself is defective.

### Current R2 terminal volume completeness

**MISMATCH / UPSTREAM DATA-CONTRACT DEFECT.**

A READY daily OHLCV contract used for T0-close signal evaluation must not expose a materially unfinished terminal session as if it were a finalized daily observation.

### Remediation boundary

The correction belongs upstream in `ussy-data`, not in TrendFoll threshold tuning.

Required upstream behavior before governed production acceptance:

1. unfinished current-session candles remain excluded;
2. previously stored partial same-date candles must be repairable/reconcilable after the session is finalized;
3. READY publication must not silently promote materially incomplete terminal volume as finalized data;
4. correction must preserve historical identity/security mapping and avoid rewriting unrelated valid history;
5. TrendFoll volume threshold/percentile semantics must not be tuned to compensate for bad upstream facts.

No upstream production correction is authorized by this evidence document. This audit freezes the root cause and remediation boundary only.

## Follow-up validation

After an upstream reconciliation mechanism is implemented and governed separately, rerun this exact diagnostic against the newly published READY pointer. Acceptance requires the mass terminal-volume anomaly to disappear or be specifically explained by genuine market observations rather than by partial-bar persistence.
