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
| PROB-013 | OPEN DIAGNOSIS | **High** | Is the current exit contract (2 ATR stop anchored to filled T+1 entry, EMA20 trend exit, 45 trading-day maximum) aligned with a short-to-medium swing system adapted from the CAN SLIM/O'Neil family? The 45-day hard maximum is now formally challenged: the reviewed CAN SLIM/IBD methodology emphasizes failed-breakout defense, disciplined loss cutting, profit-taking into strength, exceptional-winner hold exceptions, and technical/market deterioration rather than a universal fixed-age exit. | Use `docs/CANSLIM_EXIT_AUDIT.md` as methodology baseline. DIAG-003 must measure early failure, current 2 ATR behavior, time-to-MFE, MFE/MAE, give-back, EMA20-loss timing, and a day-45 counterfactual including what still-healthy positions did after day 45. Do not delete or replace the 45-day rule before evidence. |
| PROB-014 | OPEN DIAGNOSIS | Medium-High | How regime-dependent are signal and executable-entry outcomes? | Segment DIAG-001 outcomes by frozen regime labels. |
| PROB-015 | OPEN DIAGNOSIS | Medium | Which Investability components actually contribute outcome separation? | Component-level descriptive attribution; no threshold tuning. |
| PROB-016 | GOVERNED VALIDATION | High | <=0.60 ATR proximity has development evidence for near-term breakout onset, but not untouched production validation and not profitability evidence. | Continue frozen Cycle 1 forward validation independently. |
| PROB-017 | ENGINEERING DEBT | High | Supabase position history contains a duplicate `(symbol, entry_date)` key (`ANF`, `2026-08-26`) with conflicting state/outcome rows, which can contaminate forward attribution. | Audit position lifecycle history and enforce/verify canonical uniqueness semantics. |
| PROB-018 | OPEN DIAGNOSIS | **Highest / VALIDITY GATE** | The R2 stock dataset provides only about 300 daily bars per security, while the current trend contract uses EMA20/50/150/200 plus a 30-week stage MA. Long-period recursive EMA values and weekly stage classification may be affected by finite-history warm-up, and the usable historical test window is materially shorter than the raw 300 bars. Until quantified, feature validity—especially EMA150/EMA200, `ema_stack_aligned`, Stage2 and downstream Trend PASS—cannot be assumed equivalent to a long-history reference calculation. | Before DIAG-002 or development backtesting, compare R2-window features against the same-date features computed from substantially longer OHLCV history. Measure numeric EMA error and, more importantly, disagreement rates for `ema_stack_aligned`, Stage2 and `trend_status`. Establish a documented safe warm-up / usable-window contract. Do not discard or retune EMA thresholds before evidence. |

## Diagnostic work order

0. **DATA/FEATURE VALIDITY GATE — PROB-018**: audit 300-bar R2 warm-up against long-history reference. This now blocks interpretation of further feature-attribution diagnostics and development backtests until resolved.
1. **DIAG-001 — Signal-to-Outcome Funnel**: PROB-008/009/010/011. Existing evidence remains diagnostic, but its trend-filter-dependent interpretation must be revisited if PROB-018 finds material classification disagreement.
2. Entry attribution: PROB-012, only after PROB-018 validity gate.
3. **DIAG-003 — Exit Conversion / Give-back**: PROB-013, using the CAN SLIM/O'Neil exit audit as methodology context and explicitly testing the 45-day counterfactual rather than assuming it is valid.
4. Regime and Investability segmentation: PROB-014/015.
5. Continue PROB-016 frozen validation in parallel; it must not be tuned from DIAG-001.
6. Engineering debt PROB-003/004/005/017 can be hardened without changing trading semantics.

## PROB-018 validity protocol boundary

The purpose of the R2 warm-up audit is **not** to search for a better moving-average combination. The current production formulas remain the object under test. For the same symbol/date, compute the existing EMA20/50/150/200 and 30-week Stage features using (a) the R2-limited history and (b) a substantially longer reference history. Report absolute/relative numeric differences by available-history age and classification disagreement for `ema_stack_aligned`, `stage`, `trend_status`, and where practical `hard_filter_status`.

A small numeric EMA difference is operationally acceptable only if it does not materially change downstream classification. Conversely, even modest numeric error is material if it changes PASS/NEAR_PASS/FAIL decisions. The audit must therefore prioritize **decision agreement**, not cosmetic numerical equality.

No development backtest should use the early portion of a finite R2 window merely because an indicator returns a number. The audit must establish the earliest history age at which the current feature contract is sufficiently stable, or conclude that the current R2 history contract is insufficient for the current trend feature contract.

## Decision discipline

A diagnostic result may establish a root-cause hypothesis, but it does not itself authorize a strategy change. Any proposed threshold, entry rule, exit rule, or alert semantic change must be linked back to its `PROB-*` and evidence, then enter a separate development/validation cycle.
