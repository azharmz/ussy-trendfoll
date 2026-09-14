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
| PROB-008 | CONFIRMED | High | T0 signal close differs from executable T+1 open; current tracking stores both, so trigger performance and executable performance must not be conflated. | Continue execution-quality attribution in DIAG-002; no T0-close execution assumption. |
| PROB-009 | OPEN DIAGNOSIS | Highest | Does strong T-1 -> T0 momentum/extension create a materially different risk/quality profile before executable T+1 entry? Valid-history DIAG-001 finds wider MFE/MAE but no monotonic T+5 return decay. | DIAG-002: separate raw momentum from pivot/ATR extension and other entry-quality components. |
| PROB-010 | OPEN DIAGNOSIS | Highest | Does T+1 execution quality depend on overnight gap or other entry-state features? Valid-history DIAG-001 does not support general T+1-to-T+5 median fade; the largest positive-gap quartile remains mildly weaker descriptively. | DIAG-002: pre-registered attribution of positive gap and other entry components; no gap cutoff mining. |
| PROB-011 | OPEN DIAGNOSIS | Highest | When outcomes disappoint, is the dominant failure in selection, breakout quality, execution timing, regime, risk, or exit? Valid-history DIAG-001 removes general early median fade as a supported explanation but leaves component attribution and exit conversion open. | DIAG-002 entry attribution followed by DIAG-003 exit conversion. |
| PROB-012 | OPEN DIAGNOSIS | High | Which entry components provide separation: momentum/extension, breakout onset/repeat, volume confirmation, tightness, Investability components, or regime? | DIAG-002 attribution using the governed research-history contract. |
| PROB-013 | OPEN DIAGNOSIS | **High** | Is the current exit contract (2 ATR stop anchored to filled T+1 entry, EMA20 trend exit, 45 trading-day maximum) aligned with a short-to-medium swing system adapted from the CAN SLIM/O'Neil family? The 45-day hard maximum is formally challenged. | Use `docs/CANSLIM_EXIT_AUDIT.md` as methodology baseline. DIAG-003 must measure early failure, current 2 ATR behavior, time-to-MFE, MFE/MAE, give-back, EMA20-loss timing, and a day-45 counterfactual. |
| PROB-014 | OPEN DIAGNOSIS | Medium-High | How regime-dependent are signal and executable-entry outcomes? | Segment outcomes by frozen regime labels using governed research history. |
| PROB-015 | OPEN DIAGNOSIS | Medium | Which Investability components actually contribute outcome separation? | Component-level descriptive attribution under governed research history; no threshold tuning. |
| PROB-016 | GOVERNED VALIDATION | High | <=0.60 ATR proximity has development evidence for near-term breakout onset, but not untouched production validation and not profitability evidence. | Continue frozen Cycle 1 forward validation independently. |
| PROB-017 | ENGINEERING DEBT | High | Supabase position history contains a duplicate `(symbol, entry_date)` key (`ANF`, `2026-08-26`) with conflicting state/outcome rows, which can contaminate forward attribution. | Audit position lifecycle history and enforce/verify canonical uniqueness semantics. |
| PROB-018 | **CONFIRMED / RESOLVED DIAGNOSIS** | **Highest / VALIDITY GATE** | The ~300-bar R2 window is adequate for the current-end trend classification in the audited deterministic 100-symbol sample, but is **not** valid as a full historical feature/backtest window. Run #1 found 0% latest EMA-stack/Stage/trend-status disagreement, while historical trend-status disagreement was 15.64–21.76% in bars 1–150, 5.68% in 151–200, 2.14% in 201–250, and 0.96% at 251+. | Evidence locked in `docs/EVIDENCE_PROB_018.md`. Do not retune MAs. Historical work must use the governed research-history contract. |
| PROB-019 | **CONFIRMED / RESOLVED ARCHITECTURE** | **Highest / ARCHITECTURE GATE** | Historical diagnostics/backtests require pre-roll before evaluated rows. The governed contract now uses current R2 readiness as universe authority, R2 `backtest/ohlcv/{security_id}.parquet` as full stock history, a frozen 500-bar engineering pre-roll, pre-feature `evaluation_end` trimming, post-feature `research_eligible` gating, and canonical `EMA(adj_close)`. Audit run `34905314921` passed with 100/100 histories loaded, 29,930/29,930 source-compatible overlap rows, exact canonical EMA parity, and 0 latest Stage mismatches. | Evidence locked in `docs/EVIDENCE_PROB_019.md`. New historical diagnostics/backtests may proceed through `research_history.py` or an explicitly equivalent governed successor. Current-universe results are not claimed survivorship-bias-free. |

## Diagnostic work order

0. **PROB-018 completed** — evidence is in `docs/EVIDENCE_PROB_018.md`.
1. **PROB-019 completed** — governed research-history/pre-roll architecture is implemented and audited in `docs/EVIDENCE_PROB_019.md` and `docs/RESEARCH_HISTORY_CONTRACT.md`.
2. **DIAG-001 rebuilt/verified** — valid-history evidence is locked in `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md`; the original rolling-window evidence is retained but superseded for causal interpretation.
3. **DIAG-002 Entry Attribution — NEXT**: PROB-009/010/012 plus relevant PROB-014/015 components. Separate momentum from pivot/ATR extension, positive gap, volume, tightness, Investability components and regime without threshold mining.
4. DIAG-003 Exit Conversion / Give-back: PROB-013, including the 45-day counterfactual.
5. Continue PROB-016 frozen validation in parallel; it must not be tuned from these diagnostics.
6. Engineering debt PROB-003/004/005/017 can be hardened without changing trading semantics.

## PROB-018 evidence boundary

The audit used the then-current EMA20/50/150/200 and weekly Stage formulas, a deterministic 100-symbol R2 sample, and a 5-year yfinance reference. Of 29,901 overlapping observations, 29,900 passed the raw-close compatibility guard. The latest observation for all 100 sampled symbols had 0% disagreement for EMA-stack, Stage, and `trend_status`.

However, early historical bars were materially contaminated by finite-history initialization. In particular, the weekly 30-week Stage could not be equivalent to a long-history reference during much of the first ~150 bars, and EMA150/EMA200 convergence remained materially slower than EMA20/EMA50. See `docs/EVIDENCE_PROB_018.md` for the full table and provenance.

This evidence supports why the old rolling dataset was not a valid historical backtest window.

## PROB-019 resolved contract

Historical research now uses:

`R2 readiness universe -> R2 full stock history -> pre-roll feature initialization -> research_eligible rows -> signal/outcome study`

The pre-roll portion is feature context only and never counts as evaluated observations, trades, or validation outcomes. Each security's history is trimmed to the requested `evaluation_end` before feature computation, preventing future stock rows from entering earlier states. Canonical historical EMA is based on `adj_close`, matching production shared EMA, while Stage2 remains the existing raw-close weekly implementation.

The successful deterministic 100-security audit loaded 520,282 full-history rows and produced 25,064 eligible rows across 87 securities for its bounded evaluation window. All 29,930 exact ready/full-history overlap rows passed the 0.25% source compatibility guard; all 100 latest canonical EMA states matched production exactly with zero numeric/stack/date mismatches; and all 100 latest Stage classifications matched. See `docs/EVIDENCE_PROB_019.md`.

The universe authority remains current R2 readiness. This contract does not reconstruct historical point-in-time membership and therefore does not authorize claims that historical results are survivorship-bias-free.

## DIAG-001 valid-history correction

The rebuilt DIAG-001 on the same deterministic 100-security sampling framework produced 1,545 eligible independent entry-ready onsets. Median T+1-open to T+5-close return was +0.15%, not the -0.27% seen in the original rolling-window run. Momentum-vs-T+5 Spearman rho was +0.011, while momentum-vs-MFE5 was +0.232 and momentum-vs-MAE5 was -0.210.

Therefore the current evidence supports a **risk-dispersion** effect from stronger signal-day momentum, but not a monotonic T+5 return-decay effect. The old early-fade and symmetric extreme-gap interpretations are superseded. See `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md` and the revised `docs/ROOT_CAUSE_MAP.md`.

## Decision discipline

A diagnostic result may establish or reject a root-cause hypothesis, but it does not itself authorize a strategy change. Any proposed threshold, entry rule, exit rule, or alert semantic change must be linked back to its `PROB-*` and evidence, then enter a separate development/validation cycle.
