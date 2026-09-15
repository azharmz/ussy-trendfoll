# EVIDENCE — EXIT-CAND-003 DEVELOPMENT

Status: **EVIDENCE-LOCKED / DEVELOPMENT PASS / NOT VALIDATION / NOT PRODUCTION**

## Frozen candidate
Representation: `docs/EXIT_CANDIDATE_REPRESENTATION_003.md`

Development workflow: `EXIT-CAND-003 Development`

- Run: `34949786428`
- Job: `104317742856`
- Head SHA: `745046c626444b68a8791c502142a8626a62c5ba`
- Artifact: `exit-candidate003-development-1`
- Artifact ID: `10388569364`
- Artifact SHA256: `2f5c906843d017571aeee2f76bd390816b132b9147aead7b11005931057cdf30`
- Repository tests: `12/12 PASS`

## Corpus
- deterministic SHA256 security ranks: 1–100
- snapshot: 2026-08-28
- 500-bar pre-roll
- eligible onsets: 1,545
- exact comparable events: 1,524
- T+1 Open entry

## Results

CURRENT:
- median return: -3.4648%
- positive rate: 33.005%
- median MAE: -4.7341%
- median MFE: +5.5153%
- median holding: 16 days

EXIT-CAND-003:
- median return: -2.2974%
- positive rate: 34.6457%
- median MAE: -3.8254%
- median MFE: +4.7497%
- median holding: 12 days
- risk_stop_gap: 160
- risk_stop_touch: 1,241
- trend_exit: 78

Aggregate median-return improvement: **+1.1673 percentage points**.

## Development gate
- CURRENT baseline exact: PASS
- feasibility invariants: PASS
- candidate median return > CURRENT: PASS
- candidate positive rate >= CURRENT: PASS
- candidate median MAE >= CURRENT: PASS

Verdict: **EXIT-CAND-003 DEVELOPMENT GATE = PASS**.

This does not authorize production use. Median return remains negative. The next governed step is untouched validation on a separately frozen deterministic corpus.

## Reporting-only defect
The development summary's inherited `stop_touch_timing` helper expects the old `risk_stop` label, so it reports zero stop events despite `risk_stop_gap` and `risk_stop_touch` exit-reason counts. This is reporting-only and does not alter simulation, returns, MAE, feasibility, or the gate. Candidate semantics are not changed.

## Comparator boundary
CURRENT deliberately retains the historical EXIT-ISO-001 exact-stop convention for this candidate's development and validation comparator. A realistic gap-through audit of CURRENT is separate debt (`STOP-EXEC-001`) and must not be mixed into EXIT-CAND-003 untouched validation.