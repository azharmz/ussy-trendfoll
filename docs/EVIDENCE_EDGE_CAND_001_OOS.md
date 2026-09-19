# EDGE-CAND-001 — Untouched Validation Evidence

Status: **OOS GATES PASSED / FURTHER RESEARCH SUPPORTED / NOT PRODUCTION-AUTHORIZED**

Frozen contract: docs/EDGE_CAND_001_VALIDATION_CONTRACT.md

Run: 35417801041  
Head commit: 9b0c3f686e8694c59c2ddc043bd70e0d0120ef49  
Artifact: edge-cand001-validation-1 (ID 10575914815)  
Artifact SHA256: bbcd8850145f14ec3d1434ea0b5f56ce70623f5f55e20c5334fc8c18595e97d2

## Untouched design

Development identities were deterministic ranks 1–100. This validation used ranks 101–200 with no overlap. Full canonical history, 500-bar pre-roll, adj_close historical EMA basis, and full-stream onset detection were retained.

This remains current-READY-membership research rather than a point-in-time universe backtest.

## Result

The untouched corpus produced 1,533 mature baseline T+10 events. The frozen accepted candidate produced 1,203 mature T+10 events across 51 symbols.

Baseline T+1 Open → T+10:
- median +0.059%
- mean +0.154%
- positive rate 50.36%

EDGE-CAND-001 accepted T+2 Open → T+10:
- median +0.152%
- mean +0.455%
- positive rate 52.04%

Candidate T+2 Open → T+5:
- median +0.111%
- mean +0.294%
- positive rate 51.04%

Risk-path comparison:
- baseline median MAE10: -3.374%
- candidate median MAE10: -3.104%
- candidate median MFE10: +3.088%

Concentration:
- 51 unique candidate symbols
- largest symbol share 5.07%

Year robustness:
- 23 calendar years had >=20 mature candidate events
- 65.22% of those years had non-negative median T+10

## Frozen gates

All pre-registered gates passed:
- mature T+10 >=200: PASS
- unique symbols >=25: PASS
- median T+10 >0: PASS
- positive T+10 rate >50%: PASS
- median MAE10 less adverse than baseline: PASS
- >=60% eligible years non-negative median T+10: PASS
- top symbol share <=10%: PASS

## Interpretation

The untouched security holdout reproduces the direction of the development hypothesis: waiting until T+1 acceptance is observable and anchoring causally at T+2 Open leaves a modest positive short-horizon path and somewhat improves adverse excursion versus the unconditional T+1 baseline.

The magnitude is small. This is evidence for further research, not evidence that production should switch entries. It does not include transaction costs/slippage, current exit rules, portfolio constraints, point-in-time universe membership, or a forward live cohort.

Recent years are not uniformly positive; for example 2024, 2025 and 2026 have negative median T+10 in this holdout. That limits any claim of temporal stability even though the frozen >=60% year gate passed.

## Governance decision

EDGE-CAND-001 is **OOS-SUPPORTED FOR FURTHER RESEARCH**, not production-authorized.

Do not tune a pivot margin, gap cutoff, momentum cutoff, retest requirement, or other threshold from this result.

Before any production proposal, the candidate needs:
1. economic conversion using a frozen exit/risk implementation and realistic costs;
2. explicit recent-period robustness;
3. preferably point-in-time universe or a documented survivorship sensitivity;
4. forward/shadow evidence if it survives those checks.

Current production T+1 Open semantics remain unchanged.
