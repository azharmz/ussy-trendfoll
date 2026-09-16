# CAND-003 Operational Evidence Sufficiency Gate

**Status:** FROZEN BEFORE CLEAN OPERATIONAL OUTCOMES

**Date frozen:** 2026-09-16

**Scope:** `exit-cand-003-shadow-v1` operational shadow only.

## Purpose

Define the evidence required before CAND-003 operational shadow observation may advance to final governance review. This gate is defined before any admissible post-bootstrap operational session exists, so it cannot be tuned to observed candidate outcomes.

This document does **not** authorize a production exit change and does not alter the frozen CAND-003 mathematical representation.

## Admissibility boundary

Operational evidence is admissible only when all of the following hold:

1. The shadow belongs to a real production position created after the bootstrap fix.
2. Shadow registration occurs on the first genuinely observable T+1 market session available to the production pipeline.
3. Sessions are accumulated sequentially; no retrospective state reconstruction or skipped-session bootstrap is allowed.
4. The persisted session row uses the frozen `exit-cand-003-shadow-v1` contract.
5. The row is produced by the normal production pipeline, not by a synthetic/test insertion.
6. The append-only uniqueness invariant `(position_id, session_date, contract_version)` holds.

The 27 rows produced by the 2026-09-16 bootstrap-defect smoke run are permanently excluded from admissible operational evidence. Their associated shadow states are quarantined as `invalid_bootstrap`; rows remain preserved for auditability.

## E1 prerequisite

Before aggregate operational sufficiency can be evaluated, the first admissible session must pass the complete E1 first-real-session verification in `docs/EXIT_WORKSTREAM_PROGRESS_CHECKLIST.md`, including independent recomputation of persisted stop/Chandelier semantics and confirmation that shadow computation did not mutate production state.

If E1 fails, observation does not advance. Diagnose the engineering defect, preserve evidence, fix under engineering governance, regression-test, and restart admissible observation only where sequential state remains valid.

## Operational sufficiency criteria

Final governance review may begin only after **all** criteria below are satisfied.

### 1. Sequential lifecycle coverage

The admissible dataset must contain complete sequential shadow evidence from genuine T+1 registration through a terminal shadow outcome for each position used in terminal-outcome comparisons. Positions still active may contribute execution/invariant evidence but may not be treated as completed outcome observations.

### 2. Execution-path representation

The admissible completed dataset must contain real operational representation of every exit path that actually occurs during the observation period. Absence of a path is reported as an observed zero; no synthetic event may be manufactured merely to satisfy path diversity.

A production-governance decision must explicitly acknowledge any frozen exit path that remains unobserved operationally.

### 3. Data-quality completeness

For admissible expected position-sessions:

- every missing ledger session must be enumerated and assigned a reason;
- duplicate invariant keys must be zero;
- divergent replay conflicts must be zero;
- stop-decrease invariant failures must be zero;
- same-day Chandelier look-ahead failures must be zero;
- impossible touch fills outside observed OHLC must be zero;
- shadow mutation of authoritative production exit/position state must be zero.

Any non-zero semantic/invariant failure blocks final governance until diagnosed. Missing upstream market data may be documented separately but cannot be silently counted as valid coverage.

### 4. Production comparison integrity

Production status/exit fields are observational comparators only. Evidence must demonstrate that they are attached after the CAND-003 session decision and do not feed back into shadow state or hypothetical exit selection.

### 5. Outcome maturity

Operational reporting must distinguish active/censored shadows from terminal shadows. Return, exit-timing, and production-versus-shadow terminal comparisons may use only observations for which the required endpoints are genuinely observable.

### 6. Stability across calendar time

Evidence must span multiple independent production-entry cohorts rather than a single same-day cohort. This requirement is structural, not performance-based: it prevents one market session or one batch of entries from being treated as operational validation of the pipeline.

No minimum return, win rate, median performance, or candidate-vs-production superiority threshold is part of this sufficiency gate.

## Required locked report before Section H

The operational evidence report must contain at minimum:

- observation start/end dates;
- eligible production positions and represented shadow positions;
- expected versus persisted admissible sessions and coverage;
- missing-data counts and reasons;
- active versus terminal shadows;
- exit-reason mix;
- gap-through count/frequency and gap slippage;
- production-versus-shadow exit timing where observable;
- production-versus-shadow realized-return differences where observable;
- MAE/MFE where available;
- invariant-failure counts;
- duplicate/replay-conflict counts;
- explicit list of frozen exit paths not observed operationally;
- immutable evidence snapshot identifier/hash where practical.

## Governance boundary

These criteria measure operational representativeness, completeness, chronology, and execution correctness. They intentionally do not specify a favorable performance outcome.

After the criteria are reached, Section H may review the evidence and choose a terminal governance path. Reaching operational sufficiency does **not** itself promote CAND-003 to production.

**Frozen marker:**

`PRE-OUTCOME SUFFICIENCY GATE LOCKED → WAIT FOR FIRST ADMISSIBLE GENUINE T+1 → E1 → SEQUENTIAL OBSERVATION → LOCK OPERATIONAL SNAPSHOT → FINAL GOVERNANCE REVIEW`
