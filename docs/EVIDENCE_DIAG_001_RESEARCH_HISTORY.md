# EVIDENCE — DIAG-001 Rebuild on Governed Research History

Status: **OBSERVATIONAL EVIDENCE / VALID-HISTORY REBUILD / NO PRODUCTION CHANGE AUTHORIZED**

Source run: GitHub Actions `DIAG-001 research-history rebuild` run #2, run id `34908204710`, job `104189609137`.
R2 ready snapshot / evaluation end: `2026-08-28`.
Research-history contract: `docs/RESEARCH_HISTORY_CONTRACT.md`.

This rebuild supersedes the original finite-window DIAG-001 for historical causal interpretation. The original evidence remains retained for provenance.

## Contract and coverage

- Universe authority: current R2 readiness snapshot.
- Deterministic sample: 100 `security_id|ticker` pairs, SHA256-ranked using the same sampling method as PROB-019.
- Full stock history source: `backtest/ohlcv/{security_id}.parquet`.
- Canonical historical EMA basis: `adj_close`.
- Engineering pre-roll: first 500 daily bars per security, not evaluated.
- Independent entry-ready onset is detected on the **full decision stream first**, then T0 is restricted to `research_eligible` rows. This prevents a false onset at the warm-up boundary.
- Full-history rows loaded: 519,288.
- Eligible decision rows: 470,890 across 87 securities.
- Full-stream entry-ready onsets: 1,610.
- Eligible onsets: 1,545.
- Mature through T+1: 1,545.
- Mature through T+3: 1,545.
- Mature through T+5: 1,544.
- Production/Supabase positions are intentionally not linked in this rebuild.

Boundary: the universe is the current R2 readiness universe, not point-in-time historical membership. These results are therefore **not survivorship-bias-free**.

## Whole-sample medians

| Metric | Median |
|---|---:|
| T-1 -> T0 return | +3.07% |
| T0 pivot extension | +0.54 ATR |
| T0 close -> T+1 open gap | 0.00% |
| T+1 open -> T+1 close | +0.05% |
| T+1 open -> T+3 close | +0.22% |
| T+1 open -> T+5 close | +0.15% |
| T+1-open anchored MFE through T+5 | +2.57% |
| T+1-open anchored MAE through T+5 | -2.50% |

This valid-history corpus does **not** show the median T+3/T+5 deterioration seen in the original rolling-window DIAG-001.

## T-1 -> T0 momentum

Spearman rank relationships on mature T+5 observations:

- momentum vs T+5 close return: **+0.011** — effectively no monotonic relationship;
- momentum vs MFE5: **+0.232** — stronger signal-day moves are associated with larger upside excursion;
- momentum vs MAE5: **-0.210** — stronger signal-day moves are also associated with worse downside excursion.

Descriptive quartiles:

| Momentum quartile | Median T-1->T0 | Median T+5 | T+5 positive | MFE5 | MAE5 |
|---|---:|---:|---:|---:|---:|
| Q1 | +1.23% | +0.32% | 54.9% | +2.08% | -1.84% |
| Q2 | +2.41% | -0.13% | 48.2% | +2.24% | -2.39% |
| Q3 | +3.97% | +0.25% | 52.1% | +2.95% | -2.57% |
| Q4 | +7.73% | +0.06% | 50.3% | +3.66% | -3.54% |

Interpretation: the robust part of the previous overextension finding is **dispersion/risk expansion**, not a monotonic loss of T+5 return. Higher momentum increases both favorable and adverse excursion. The previous claim that upper momentum buckets systematically produce negative T+5 returns is not reproduced.

## T0 -> T+1 opening gap

Descriptive quartiles:

| Gap quartile | Median gap | Median T+5 | T+5 positive | MFE5 | MAE5 |
|---|---:|---:|---:|---:|---:|
| Q1 | -0.95% | +0.37% | 52.6% | +3.28% | -2.56% |
| Q2 | -0.14% | +0.16% | 51.7% | +2.41% | -2.32% |
| Q3 | +0.19% | +0.25% | 52.5% | +2.21% | -2.19% |
| Q4 | +0.96% | -0.10% | 48.7% | +2.71% | -3.09% |

Interpretation: the old symmetric “both gap extremes are weak” result is not reproduced. The largest positive-gap quartile is somewhat weaker and has worse MAE, but this remains descriptive and does not authorize a cutoff.

## Comparison with original DIAG-001

The original rolling-300-window run reported median T+5 = -0.27% and Spearman momentum-vs-T+5 = -0.105, with negative T+5 medians in the upper momentum half. Under the governed full-history/pre-roll contract, median T+5 is +0.15% and momentum-vs-T+5 rho is +0.011.

Therefore the earlier directional return-decay interpretation is **not robust to the corrected research-history architecture**. It must not be used as justification for a momentum ceiling, delayed entry, or other production change.

What does survive:
- signal-day momentum is associated with wider subsequent excursion;
- strongest momentum has materially larger MFE and worse MAE;
- large positive overnight gaps remain a plausible execution-quality dimension worth decomposing in DIAG-002;
- exit/risk conversion remains open for DIAG-003, but is not established by this rebuild.

## Artifact

- Artifact: `diag001-research-history-2`
- Artifact ID: `10373158420`
- Artifact ZIP SHA256: `ec1ab3e3225d123c20ddeb71fb14381e0a2b464a8edaf7c05dc6f949662baca2`
- Repository tests: 12/12 PASS.

## Governance conclusion

This evidence is observational. It authorizes **revision of diagnostic hypotheses**, not a trading-rule change. No momentum threshold, gap threshold, entry delay, stop, exit, or alert rule is authorized here.
