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
| PROB-012 | OPEN DIAGNOSIS | High | Which entry components provide separation: breakout onset/repeat, volume confirmation, tightness, Investability components, or regime? | Follow-up attribution diagnostic after valid research-history contract is available. |
| PROB-013 | OPEN DIAGNOSIS | **High** | Is the current exit contract (2 ATR stop anchored to filled T+1 entry, EMA20 trend exit, 45 trading-day maximum) aligned with a short-to-medium swing system adapted from the CAN SLIM/O'Neil family? The 45-day hard maximum is formally challenged. | Use `docs/CANSLIM_EXIT_AUDIT.md` as methodology baseline. DIAG-003 must measure early failure, current 2 ATR behavior, time-to-MFE, MFE/MAE, give-back, EMA20-loss timing, and a day-45 counterfactual. |
| PROB-014 | OPEN DIAGNOSIS | Medium-High | How regime-dependent are signal and executable-entry outcomes? | Segment outcomes by frozen regime labels once valid research history exists. |
| PROB-015 | OPEN DIAGNOSIS | Medium | Which Investability components actually contribute outcome separation? | Component-level descriptive attribution; no threshold tuning. |
| PROB-016 | GOVERNED VALIDATION | High | <=0.60 ATR proximity has development evidence for near-term breakout onset, but not untouched production validation and not profitability evidence. | Continue frozen Cycle 1 forward validation independently. |
| PROB-017 | ENGINEERING DEBT | High | Supabase position history contains a duplicate `(symbol, entry_date)` key (`ANF`, `2026-08-26`) with conflicting state/outcome rows, which can contaminate forward attribution. | Audit position lifecycle history and enforce/verify canonical uniqueness semantics. |
| PROB-018 | **CONFIRMED / RESOLVED DIAGNOSIS** | **Highest / VALIDITY GATE** | The ~300-bar R2 window is adequate for the current-end trend classification in the audited deterministic 100-symbol sample, but is **not** valid as a full historical feature/backtest window. Run #1 found 0% latest EMA-stack/Stage/trend-status disagreement, while historical trend-status disagreement was 15.64–21.76% in bars 1–150, 5.68% in 151–200, 2.14% in 201–250, and 0.96% at 251+. | Evidence locked in `docs/EVIDENCE_PROB_018.md`. Do not retune MAs. Introduce a research-history/pre-roll contract before further historical attribution/backtesting. |
| PROB-019 | CONFIRMED | **Highest / ARCHITECTURE GATE** | Research/backtest jobs need historical OHLCV before the evaluated window so EMA150/EMA200 and 30-week Stage are initialized from pre-roll rather than from the first evaluated R2 bar. A conservative warm-up inside a 300-bar dataset would consume most of the usable sample. | Define and implement a **feature pre-roll / research history contract**: preserve R2 readiness as the universe, obtain sufficiently long prior OHLCV for feature initialization, exclude pre-roll from evaluation, enforce no look-ahead, record source/provenance, and verify same-date feature agreement before DIAG-002/DIAG-003/backtests. |

## Diagnostic work order

0. **PROB-018 completed** — audit evidence is in `docs/EVIDENCE_PROB_018.md`. Current-end scanning is supported by the sample; full-window historical research is not.
1. **PROB-019 — RESEARCH HISTORY / PRE-ROLL ARCHITECTURE GATE**: implement valid feature initialization history while keeping R2 readiness as the universe. This now blocks new historical attribution and development backtests.
2. Rebuild/verify DIAG-001 where relevant under the valid history contract.
3. DIAG-002 Entry Attribution: PROB-012.
4. DIAG-003 Exit Conversion / Give-back: PROB-013, including the 45-day counterfactual.
5. Regime and Investability segmentation: PROB-014/015.
6. Continue PROB-016 frozen validation in parallel; it must not be tuned from these diagnostics.
7. Engineering debt PROB-003/004/005/017 can be hardened without changing trading semantics.

## PROB-018 evidence boundary

The audit used the current EMA20/50/150/200 and weekly Stage formulas, a deterministic 100-symbol R2 sample, and a 5-year yfinance reference. Of 29,901 overlapping observations, 29,900 passed the raw-close compatibility guard. The latest observation for all 100 sampled symbols had 0% disagreement for EMA-stack, Stage, and `trend_status`.

However, early historical bars were materially contaminated by finite-history initialization. In particular, the weekly 30-week Stage could not be equivalent to a long-history reference during much of the first ~150 bars, and EMA150/EMA200 convergence remained materially slower than EMA20/EMA50. See `docs/EVIDENCE_PROB_018.md` for the full table and provenance.

This evidence supports continuing the current latest-day scanner; it does **not** authorize using all 300 R2 bars as a historical backtest window.

## PROB-019 contract principles

The preferred architecture is not to shrink the model merely to fit the available history. Research should use:

`R2 readiness universe -> historical pre-roll OHLCV -> feature initialization -> evaluation start -> signal/outcome study`

The pre-roll portion is feature context only and must never count as evaluated observations, trades, or validation outcomes. Source provenance and same-date compatibility checks must be retained so warm-up differences are not confused with vendor-data differences. Any implementation must prevent future data from leaking into earlier feature states.

## Decision discipline

A diagnostic result may establish a root-cause hypothesis, but it does not itself authorize a strategy change. Any proposed threshold, entry rule, exit rule, or alert semantic change must be linked back to its `PROB-*` and evidence, then enter a separate development/validation cycle.
