# DIAG-002 — Entry Quality Attribution Contract

Status: **DEVELOPMENT-FROZEN DIAGNOSTIC CONTRACT / OBSERVATIONAL ONLY**

## Question

Among independent entry-ready onsets under the governed research-history contract, which already-existing entry-state components are associated with different executable T+1 outcome distributions?

This diagnostic follows valid-history DIAG-001. It does not search for a new trading rule.

## Corpus and event unit

- Universe authority: current R2 readiness universe.
- Deterministic sample: same SHA256-ranked 100-security method used by PROB-019 and rebuilt DIAG-001.
- Stock history: governed R2 full-history contract via `research_history.py`.
- Pre-roll: frozen 500 bars.
- Canonical historical EMA: `adj_close`.
- Evaluation end: R2 readiness snapshot date.
- Event: independent `entry_ready` False -> True onset, detected on the full decision stream before restricting T0 to `research_eligible`.
- Execution anchor: T+1 open. T0 close is signal information, not an executable fill assumption.

## Pre-registered components

No additional indicators or thresholds may be introduced during this diagnostic.

Continuous components:
1. T-1 -> T0 raw-close return (`ret_tminus1_t0`).
2. T0 extension above prior pivot in ATR units (`pivot_extension_atr_t0`).
3. T0 close -> T+1 open gap (`gap_t0close_t1open`). Primary directional gap attribution uses signed values; positive-gap-only rows are also summarized separately.
4. Breakout volume percentile (`breakout_volume_percentile`).
5. VCP tightness (`vcp_tightness`).

Categorical/context components already present at T0:
6. Investability status.
7. Trend status.
8. Liquidity status.
9. RS status.
10. Price status.
11. Regime status / market regime.
12. Tight-structure boolean where available.

Some hard-filter components can be constant among entry-ready events by construction. Such components must be reported as non-identifiable in this corpus rather than interpreted as having no effect.

## Outcomes

Primary outcome:
- T+1 open -> T+5 close return.

Secondary outcomes:
- T+1 open -> T+1 close.
- T+1 open -> T+3 close.
- MFE through T+5 from T+1 open.
- MAE through T+5 from T+1 open.
- T+5 positive rate.

## Attribution views

For each continuous component, report:
- non-missing N;
- median and IQR of the component;
- Spearman rho versus T+5 return, MFE5 and MAE5;
- descriptive quartiles Q1-Q4 formed from the diagnostic corpus, with N, source median, T+5 median, T+5 positive rate, MFE5 median and MAE5 median.

Quartiles are descriptive only. Their boundaries are **not candidate thresholds** and must not be promoted into production or a development rule from this run.

For each categorical component, report each observed level with N and the same outcome summaries. If only one meaningful level is present, mark the component `NON_IDENTIFIABLE_BY_CONSTRUCTION_OR_CORPUS`.

## Interpretation discipline

This diagnostic may classify a component as:
- `DESCRIPTIVE_SEPARATION_PRESENT` — materially different descriptive paths appear across pre-registered views;
- `WEAK_OR_MIXED` — differences are small, inconsistent across outcomes, or non-monotonic;
- `NO_CLEAR_SEPARATION` — little descriptive differentiation;
- `NON_IDENTIFIABLE_BY_CONSTRUCTION_OR_CORPUS` — insufficient variation.

These labels are diagnostic summaries, not statistical proof of causality and not production authorization.

No multivariate coefficient is to be interpreted causally. No stepwise selection, brute-force subset search, threshold optimization, p-value fishing, parameter tuning, or best-bucket trading rule is permitted.

## Governance boundary

DIAG-002 can update the Root Cause Map and prioritize a later development hypothesis. It cannot itself change:
- entry timing;
- momentum or gap limits;
- pivot-extension limits;
- volume/tightness thresholds;
- Investability/Tradability definitions;
- regime gates;
- stop or exit rules;
- production alerts.

Any proposed strategy change must enter a separate evidence-backed development cycle, be frozen before validation, and receive untouched validation with no post-validation tuning.

## Survivorship boundary

The universe is current R2 readiness, not reconstructed historical point-in-time membership. Results must not be described as survivorship-bias-free.
