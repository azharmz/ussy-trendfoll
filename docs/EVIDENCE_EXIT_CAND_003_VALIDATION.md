# EVIDENCE — EXIT-CAND-003 UNTOUCHED VALIDATION

Status: **EVIDENCE-LOCKED / UNTOUCHED VALIDATION PASS / NOT PRODUCTION**

Protocol was frozen before outcomes in `docs/EXIT_CAND_003_VALIDATION_PROTOCOL.md`. Candidate representation remained exactly `docs/EXIT_CANDIDATE_REPRESENTATION_003.md`; no parameter or semantic tuning was performed.

## Workflow evidence
- Workflow: `EXIT-CAND-003 Untouched Validation`
- Run: `34952211596`
- Job: `104325601461`
- Head SHA: `643a3d723ad086fc41bd69b5877796f59865375b`
- Artifact: `exit-candidate003-validation-1`
- Artifact ID: `10389703236`
- Artifact SHA256: `d848c5901d284608621307b3e2f64b79b4c11e1ec953d5ba402f84259d5d9a3c`
- Workflow/job conclusion: SUCCESS
- Repository tests: PASS

## Corpus integrity
- snapshot/evaluation end: 2026-08-28
- development ranks: 1–100
- validation ranks: 101–200
- rank method: SHA256(`security_id|ticker`), ascending hash then security_id
- development securities: 100
- validation securities: 100
- development-validation security overlap: **0**
- history requested/loaded securities: 100/100
- research-eligible securities: 87
- 500-bar pre-roll
- eligible onsets: 1,533
- exact paired comparable events: **1,526**
- current-universe historical limitation remains: not survivorship-bias-free / not PIT universe membership

Corpus integrity: **PASS**.

## Validation results

CURRENT comparator (frozen historical EXIT-ISO-001 semantics):
- n: 1,526
- median return: **-3.0652%**
- positive rate: **33.2896%**
- median MAE: **-4.3138%**
- median MFE: +4.8722%
- median holding: 16 days
- stop_loss: 780
- trend_exit: 444
- max_holding: 302

EXIT-CAND-003:
- n: 1,526
- median return: **-2.0973%**
- positive rate: **35.0590%**
- median MAE: **-3.6255%**
- median MFE: +4.3341%
- median holding: 12 days
- risk_stop_gap: 169
- risk_stop_touch: 1,147
- trend_exit: 162
- observation_boundary: 48

Median-return improvement versus CURRENT: **+0.9679 percentage points**.

## Frozen validation gate
- corpus integrity / zero overlap: PASS
- exact paired comparator counts: PASS
- feasibility invariants: PASS
- candidate median return > CURRENT: PASS
- candidate positive rate >= CURRENT: PASS
- candidate median MAE >= CURRENT: PASS

Terminal verdict:

**EXIT-CAND-003 = DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION**

The validation result does not authorize immediate production changes. It authorizes only a separate productionization/shadow design phase.

## Reporting-only quirk retained
The inherited `stop_touch_timing` helper still reports zero candidate stop events because it expects the obsolete `risk_stop` label. The authoritative exit-reason counts above show 169 `risk_stop_gap` and 1,147 `risk_stop_touch`. This is reporting-only; candidate semantics and frozen validation outcomes are unchanged.

## Comparator boundary retained
CURRENT remains intentionally frozen to the historical exact-stop comparator convention for this validation. The independent realistic gap-through audit of CURRENT remains separate engineering/research debt (`STOP-EXEC-001`).