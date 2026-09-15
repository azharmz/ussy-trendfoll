# EXIT-CAND-003 — UNTOUCHED VALIDATION PROTOCOL

Status: **FROZEN PRE-OUTCOME VALIDATION CONTRACT / OUTCOMES NOT YET ACCESSED / NOT PRODUCTION**

This protocol is frozen after EXIT-CAND-003 development PASS and before any validation outcome is accessed. No validation outcome may be used to alter this protocol, candidate parameters, comparator semantics, corpus selection, or gate.

## Candidate representation
Use `docs/EXIT_CANDIDATE_REPRESENTATION_003.md` exactly:
- entry = T+1 Open;
- initial stop = entry − 2 × ATR14(T0);
- Chandelier = HH22 − 3 × Wilder ATR22;
- EMA20 trend exit retained;
- 45 trading-day observation boundary;
- Chandelier ratchets upward only and day-t value can arm for t+1 only;
- gap stop: if open <= operative stop, fill at Open (`risk_stop_gap`);
- touch stop: otherwise if low <= operative stop, fill at operative stop (`risk_stop_touch`).

No parameter grid, threshold search, profit target, entry change, subgroup rule, or post-outcome patch is permitted.

## Untouched corpus
The security ranking procedure is frozen to the same deterministic SHA256 rule used in development:

`sha256(f"{security_id}|{ticker}")`

Sort ascending by `(hash, security_id)`.

- development = deterministic ranks 1–100;
- validation = deterministic ranks **101–200**;
- required development-validation security overlap = **0**.

Use the same R2 ready snapshot/evaluation boundary as governed by the repository dataset, the same full-history research contract, 500-bar pre-roll, feature construction, research eligibility, signal-onset construction, and T+1 Open execution. Current-universe historical research remains not survivorship-bias-free / not PIT universe membership.

Validation must fail closed if fewer than 200 unique ranked securities are available, if rank membership is non-deterministic, or if development-validation overlap is nonzero.

## Comparator
CURRENT must retain the comparator semantics frozen in EXIT-CAND-003 development. Do not retrofit realistic gap-through fills into CURRENT inside this validation. The independent CURRENT execution audit remains separate debt (`STOP-EXEC-001`).

Comparator and candidate must be evaluated on an exact paired event corpus. Any event not evaluable for both is excluded from both. Variant event counts must match.

## Frozen validation gate
EXIT-CAND-003 passes untouched validation only if all are true:
1. corpus integrity PASS, including explicit zero security overlap with development;
2. exact paired comparator/candidate event counts PASS;
3. feasibility invariants PASS;
4. candidate median realized return > CURRENT median realized return;
5. candidate positive-return fraction >= CURRENT;
6. candidate median MAE-to-exit >= CURRENT (less negative or equal).

No tolerance band or rescue criterion may be introduced after outcomes are seen.

## Required evidence output
Record at minimum:
- snapshot/evaluation boundary;
- development and validation rank ranges and security counts;
- development-validation security overlap count;
- eligible onset count;
- exact paired comparable event count;
- CURRENT and EXIT-CAND-003 median return, positive rate, median MAE, median MFE, median holding, and exit-reason counts;
- feasibility/corpus/comparator invariant results;
- each frozen gate criterion and terminal PASS/FAIL.

## Terminal rule
If any frozen criterion fails:

`EXIT-CAND-003 = VALIDATION FAILED / EVIDENCE-LOCKED / DO NOT TUNE`

If all frozen criteria pass:

`EXIT-CAND-003 = DEVELOPMENT + UNTOUCHED VALIDATION SUPPORTED / NOT YET PRODUCTION`

A PASS authorizes only a separate productionization/shadow design phase. It does not authorize immediate production exit changes.