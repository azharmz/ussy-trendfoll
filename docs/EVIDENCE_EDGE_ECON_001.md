# EDGE-ECON-001 — Economic Conversion Evidence

Status: **EVIDENCE-LOCKED / ECONOMIC CONVERSION NOT SUPPORTED / NO PRODUCTION CHANGE**

Run: 35418179364  
Job: 105830746488  
Head SHA: c858e417b559ee53344fa645e03c6c5b611e1d52  
Artifact: edge-econ001-1 (ID 10576865445)  
Artifact SHA256: 2c6a2950f77f1bcf05d8923c3328cc975aa62280e93370fb5d7c15aa87e8e357

Contract: docs/EDGE_ECON_001_CONTRACT.md

## Scope

This is a follow-up on already inspected ranks 101–200, not a second untouched validation. It combines frozen EDGE-CAND-001 acceptance (T+1 close >= T0 pivot, entry T+2 Open) with frozen EXIT-CAND-003 mechanics. No entry/exit threshold was tuned.

Paired mature events: 1,197 across 49 symbols.

## Economic result

### CURRENT-ACCEPTED comparator
Gross:
- median -3.0405%
- mean +0.6681%
- positive rate 32.25%

At 10 bps/side:
- median -3.2405%
- mean +0.4681%
- positive rate 31.75%

Median hold 16 sessions; median MFE +5.1697%; median MAE -4.1140%.

### EDGE+EXIT003
Gross:
- median -2.0533%
- mean -0.0056%
- positive rate 35.09%

At 5 bps/side:
- median -2.1533%
- mean -0.1056%
- positive rate 34.42%

At 10 bps/side:
- median -2.2533%
- mean -0.2056%
- positive rate 33.75%

At 20 bps/side:
- median -2.4533%
- mean -0.4056%
- positive rate 32.25%

Median hold 12 sessions; median MFE +4.4855%; median MAE -3.4427%.

Exit reasons:
- risk_stop_touch 900
- risk_stop_gap 137
- trend_exit 131
- observation_boundary 29

The candidate improves median outcome and adverse excursion relative to CURRENT-ACCEPTED, but the combined realized-return distribution remains economically weak: negative median at every cost sensitivity and negative mean once even modest costs are included.

## Recent period

At 10 bps/side, 2022–2026 aggregate:
- n=229
- median -2.7382%
- mean -0.5262%
- positive rate 31.88%

Individual recent years available in the artifact are also weak:
- 2023: median -2.0116%, positive 31.94% (n=72)
- 2024: median -3.1925%, positive 35.56% (n=90)
- 2025: median -4.8992%, positive 23.08% (n=39)
- 2026: median -2.5661%, positive 32.14% (n=28)

No 2022 candidate row appears in the yearly output, so no standalone 2022 statistic is asserted.

## Interpretation

EDGE-CAND-001 successfully identified a weaker T+1-rejected subset in event-path research, and its untouched accepted subset had a modest positive T+2→T+10 path. That does **not** convert into positive realized economics when paired with the already frozen EXIT-CAND-003 exit/risk representation.

This sharpens the diagnosis:
1. T+1 rejection is a real descriptive failure mode.
2. Waiting for acceptance modestly improves the forward path.
3. EXIT-CAND-003 improves risk/median relative to the current accepted comparator.
4. The combined entry+exit representation still does not produce a robust positive realized distribution, especially recently.

Therefore the evidence does not support a production entry change to EDGE-CAND-001 and does not support promoting EDGE+EXIT003 as a combined strategy.

## Governance

- Production T+1 Open entry remains unchanged.
- EXIT-CAND-003 production-shadow work remains a separate frozen workstream and is not invalidated by this combination test.
- Do not repair EDGE-CAND-001 with post-hoc pivot margins, gap filters, momentum filters, retest filters, or exit-parameter tuning.
- EDGE-CAND-001 is evidence-locked as a useful structural diagnostic but **closed for production promotion under the tested representation**.
- Further TrendFoll edge research, if opened, must begin from a new pre-registered hypothesis rather than optimizing this candidate.
