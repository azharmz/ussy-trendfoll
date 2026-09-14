# TrendFoll Problem Map

Status: **ACTIVE GOVERNANCE**

This document is the problem register for TrendFoll. `PROB-*` identifies a problem or unresolved question; it is not a roadmap item and does not imply a production change.

## Governance chain

`Architecture Map -> Problem Map (PROB) -> Diagnostic Plan (DIAG) -> Evidence -> Root Cause -> Roadmap -> Development Plan -> Validation -> Production`

Rules:
- Diagnose before tuning.
- Separate software/operational defects from trading-model hypotheses.
- A bad outcome is not automatically a bad signal: selection, execution, regime, risk, and exit must be decomposed.
- Diagnostic work is observational unless a separate governed development cycle explicitly authorizes a strategy change.
- Existing frozen validation contracts remain frozen.

## Classification

- **CONFIRMED** — directly established from current code/data/production behavior.
- **OPEN DIAGNOSIS** — plausible or observed concern whose cause/effect is not yet isolated.
- **GOVERNED VALIDATION** — development candidate exists but is not production-validated.
- **ENGINEERING DEBT** — reliability, integrity, auditability, or operational issue rather than trading edge.

## Problem register

| ID | Class | Priority | Problem / question | Next evidence |
|---|---|---:|---|---|
| PROB-001 | CONFIRMED | High | Production alert semantics call monitored non-actionable candidates `NEAR_TRIGGER`, while the <=0.60 ATR proximity definition is still shadow-only. | Complete frozen forward validation before any semantic promotion. |
| PROB-002 | CONFIRMED | Medium | Watchlist latest view can make historical candidates appear to disappear. | Candidate Lifecycle is the current mitigation; continue auditability checks. |
| PROB-003 | ENGINEERING DEBT | High | Telegram does not yet deliver exact transition labels/events. | Design persistent transition delivery after diagnostic foundation. |
| PROB-004 | ENGINEERING DEBT | High | Same-day reruns can recompute transitions because alert delivery has no persistent idempotency/event ledger. | Persistent alert-event identity and delivery status. |
| PROB-005 | ENGINEERING DEBT | Medium | R2 loader validates duplicate `(security_id,date)` but mapped `(symbol,date)` collision still needs explicit contract validation. | Add loader guard + tests. |
| PROB-006 | CONFIRMED | Medium | Stock OHLCV is R2-backed, but auxiliary benchmark/sector inputs remain outside that stock-data contract. | Document dependency boundary; do not change signal gates without evidence. |
| PROB-007 | CONFIRMED | Medium | Position tracking is forward paper tracking, not a realistic portfolio/capital simulation. | Keep outcome interpretation separate from portfolio performance claims. |
| PROB-008 | CONFIRMED | High | T0 signal close differs from executable T+1 open; current tracking stores both, so trigger performance and executable performance must not be conflated. | DIAG-001 signal-path analysis. |
| PROB-009 | OPEN DIAGNOSIS | Highest | Does strong T-1 -> T0 momentum/extension make the signal overextended before an executable T+1 entry? | DIAG-001: T-1/T0 extension and subsequent path. |
| PROB-010 | OPEN DIAGNOSIS | Highest | Does edge decay between T0 breakout and T+1 executable entry through overnight gap or early fade? | DIAG-001: T0 -> T+1 open/close -> T+2/T+3/T+5. |
| PROB-011 | OPEN DIAGNOSIS | Highest | When outcomes disappoint, is the dominant failure in selection, breakout quality, execution timing, regime, risk, or exit? | DIAG-001 end-to-end funnel and later attribution diagnostics. |
| PROB-012 | OPEN DIAGNOSIS | High | Which entry components provide separation: breakout onset/repeat, volume confirmation, tightness, Investability components, or regime? | Follow-up attribution diagnostic after DIAG-001. |
| PROB-013 | OPEN DIAGNOSIS | High | Is the current exit contract (2 ATR stop anchored to filled T+1 entry, EMA20 trend exit, 45 trading-day maximum) aligned with the intended short-to-medium swing objective? | Exit reason, MFE/MAE, give-back, recovery and time-to-MFE analysis. |
| PROB-014 | OPEN DIAGNOSIS | Medium-High | How regime-dependent are signal and executable-entry outcomes? | Segment DIAG-001 outcomes by frozen regime labels. |
| PROB-015 | OPEN DIAGNOSIS | Medium | Which Investability components actually contribute outcome separation? | Component-level descriptive attribution; no threshold tuning. |
| PROB-016 | GOVERNED VALIDATION | High | <=0.60 ATR proximity has development evidence for near-term breakout onset, but not untouched production validation and not profitability evidence. | Continue frozen Cycle 1 forward validation independently. |
| PROB-017 | ENGINEERING DEBT | High | Supabase position history contains a duplicate `(symbol, entry_date)` key (`ANF`, `2026-08-26`) with conflicting state/outcome rows, which can contaminate forward attribution. | Audit position lifecycle history and enforce/verify canonical uniqueness semantics. |

## Diagnostic work order

1. **DIAG-001 — Signal-to-Outcome Funnel**: PROB-008/009/010/011.
2. Entry attribution: PROB-012.
3. Exit behavior: PROB-013.
4. Regime and Investability segmentation: PROB-014/015.
5. Continue PROB-016 frozen validation in parallel; it must not be tuned from DIAG-001.
6. Engineering debt PROB-003/004/005/017 can be hardened without changing trading semantics.

## Decision discipline

A diagnostic result may establish a root-cause hypothesis, but it does not itself authorize a strategy change. Any proposed threshold, entry rule, exit rule, or alert semantic change must be linked back to its `PROB-*` and evidence, then enter a separate development/validation cycle.
