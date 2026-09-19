# TrendFoll Problem Map

Status: **ACTIVE GOVERNANCE — DIAG-001/002/003 COMPLETE**

This document is the problem register for TrendFoll. `PROB-*` identifies a problem or unresolved question; it is not a roadmap item and does not imply a production change.

## Governance chain

`Architecture Map -> Problem Map (PROB) -> Diagnostic Plan (DIAG) -> Evidence -> Root Cause -> Roadmap -> Development Plan -> Validation -> Production`

Rules:
- Diagnose before tuning.
- Separate software/operational defects from trading-model hypotheses.
- A bad outcome is not automatically a bad signal: selection, execution, regime, risk, and exit must be decomposed.
- Diagnostic work is observational unless a separate governed development cycle explicitly authorizes a strategy change.
- Existing frozen validation contracts remain frozen.

## Current problem register

| ID | Class | Priority | Problem / question | Next evidence |
|---|---|---:|---|---|
| PROB-001 | CONFIRMED | High | Production alert semantics call monitored non-actionable candidates `NEAR_TRIGGER`, while <=0.60 ATR proximity remains shadow-only. | Complete frozen forward validation before semantic promotion. |
| PROB-003 | **RESOLVED / EVIDENCE LOCKED** | — | Alert transitions now have transport-independent persistent semantic identity plus durable delivery state/history. | Maintain ledger contract and observe scheduled production. |
| PROB-004 | **RESOLVED / EVIDENCE LOCKED** | — | Same-event replay resolves to one canonical event; delivered events are skipped and failed/stale deliveries remain retryable under a leased claim. | Maintain replay/concurrency tests and operational evidence. |
| PROB-005 | **RESOLVED / EVIDENCE LOCKED** | — | TrendFoll now validates the security_id→ticker→(symbol,date) identity boundary and fails closed before feature computation on any many-to-one or duplicate market-observation mapping. | Maintain loader identity guard; upstream audit evidence recorded separately. |
| PROB-007 | CONFIRMED | Medium | Position tracking is forward paper tracking, not realistic portfolio/capital simulation. | Keep research-path claims separate from portfolio performance. |
| PROB-008 | CONFIRMED | High | T0 signal close differs from executable T+1 open. | Preserve T+1-open execution anchor in all governed research. |
| PROB-009 | RESOLVED DIAGNOSIS | — | Strong T0 momentum expands MFE/MAE dispersion but does not show monotonic T+5 decay. | Evidence locked by DIAG-001/002; no momentum cutoff authorized. |
| PROB-010 | PARTIALLY RESOLVED | Medium | Positive overnight gap has weak descriptive deterioration, not a validated cutoff. | Reopen only through separately frozen hypothesis/validation evidence. |
| PROB-011 | RESOLVED TO ROOT CAUSE | Highest | Broad early signal decay is not supported; exit/risk conversion is materially implicated. | RC-004 development-hypothesis cycle; no direct production tuning. |
| PROB-012 | **PARTIALLY RESOLVED / EDGE FOLLOW-UP CLOSED** | Medium | Entry components do not provide a simple monotonic quality rule. EDGE-DECOMP-001 found T+1 pivot rejection to be a weaker structural subset; frozen EDGE-CAND-001 passed security-holdout path gates, but EDGE-ECON-001 failed to convert the combined accepted-entry + EXIT-CAND-003 representation into positive realized economics, especially recently. | Do not tune EDGE-CAND-001; reopen only with a new pre-registered independent hypothesis. |
| PROB-013 | **RESOLVED DIAGNOSIS / CAND-003 VALIDATED + SHADOW ACTIVE** | **Highest** | Exit/risk conversion is materially implicated; component isolation identified the fixed 2 ATR stop as primary implicated mechanism. Frozen EXIT-CAND-003 passed development and untouched validation and is now awaiting genuine production shadow evidence. | Preserve frozen CAND-003 shadow protocol; do not tune while operational evidence accumulates. |
| PROB-014 | OPEN DIAGNOSIS | Medium-High | Regime dependence remains insufficiently identified because governed entry-ready corpus is constrained by the current hard filter. | Separate pre-registered regime study if still decision-relevant. |
| PROB-015 | OPEN DIAGNOSIS | Medium | Investability components are largely non-identifiable inside entry-ready events because PASS is required by construction. | Use a separately governed broader candidate corpus if component attribution is pursued. |
| PROB-016 | GOVERNED VALIDATION | High | <=0.60 ATR proximity remains in frozen forward validation; not profitability evidence. | Continue frozen Cycle 1 independently. |
| PROB-017 | **RESOLVED / EVIDENCE LOCKED** | — | Historical Supabase position history had one conflicting duplicate `(symbol, entry_date)` group; canonical lifecycle identity is immutable `positions.id`, while `(symbol, entry_date)` is the idempotency key for the current single-strategy signal occurrence. | Preserve historical conflict; enforce fail-closed/idempotent future writes. |
| PROB-018 | RESOLVED VALIDITY GATE | — | Rolling ~300-bar ready history is not a valid full historical feature/backtest window. | Evidence locked; use research-history contract. |
| PROB-019 | RESOLVED ARCHITECTURE | — | Governed full-history + 500-bar pre-roll research architecture is implemented/audited. | Maintain contract. |

## Diagnostic work order — status

0. **PROB-018 complete** — `docs/EVIDENCE_PROB_018.md`.
1. **PROB-019 complete** — `docs/EVIDENCE_PROB_019.md` and `docs/RESEARCH_HISTORY_CONTRACT.md`.
2. **DIAG-001 complete** — valid-history signal-path evidence locked.
3. **DIAG-002 complete** — entry attribution evidence locked; no production threshold authorized.
4. **DIAG-003 complete** — exit/risk conversion evidence locked in `docs/EVIDENCE_DIAG_003_EXIT_RISK.md`; RC-004 supported as material, mechanism unresolved.
5. **NEXT strategy-research gate** — evidence-backed exit-development hypothesis formulation. Do not grid-search ATR multipliers, EMA periods, holding days, or profit targets.
6. Continue **PROB-016** frozen forward validation in parallel.
7. Engineering debt **PROB-003/004/005/017** may be hardened independently without changing trading semantics.

## DIAG-003 diagnostic closure

DIAG-003 used 1,545 governed independent entry-ready paths; 1,524 were mature through 45 forward bars. On that identical mature subset, current-rule realized return had median **-3.46%** and positive rate **33.01%**, while the pre-registered day-45 endpoint counterfactual had median **+1.70%** and positive rate **56.43%**. Stop loss was the dominant exit reason, and median time-to-45-bar-MFE was 27 bars versus a 16-bar median current holding time.

This establishes exit/risk conversion as a material root cause in the governed corpus. It does **not** identify the correct alternative rule and does not authorize removing/changing the stop, EMA20, 45-day maximum, or adding a target. See `docs/EVIDENCE_DIAG_003_EXIT_RISK.md`.

## Decision discipline

A diagnostic result may establish or reject a root-cause hypothesis, but it does not itself authorize a strategy change. Any proposed threshold, entry rule, exit rule, or alert semantic change must be linked back to its `PROB-*` and evidence, then enter a separate development/validation cycle.

## Edge decomposition closure — 2026-09-19

EDGE-DECOMP-001 identified T+1 close back below the existing rolling-60D breakout reference as a materially weaker structural subset. EDGE-CAND-001 froze a causal acceptance representation (observe T+1, qualify iff close >= T0 pivot, earliest entry T+2 Open) and passed all pre-registered security-holdout path gates on ranks 101–200.

Economic conversion was then evaluated without tuning by combining that frozen entry with frozen EXIT-CAND-003. EDGE-ECON-001 produced 1,197 paired events. EDGE+EXIT003 gross median realized return was -2.05%; at 10 bps/side median was -2.25%, mean -0.21%, positive rate 33.75%. The 2022–2026 aggregate at 10 bps/side had median -2.74%, mean -0.53%, positive rate 31.88% (n=229).

Governance conclusion: the acceptance observation is retained as useful structural evidence, but EDGE-CAND-001 is closed for production promotion under the tested representation. No post-hoc pivot/gap/momentum/retest or exit-parameter tuning is authorized. Production T+1 Open remains unchanged.
