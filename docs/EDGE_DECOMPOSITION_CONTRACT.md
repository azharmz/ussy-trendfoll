# TrendFoll Edge Decomposition — Frozen Diagnostic Contract

Status: **DEVELOPMENT-FROZEN / OBSERVATIONAL / NO PRODUCTION CHANGE**

## Question
Does the current TrendFoll entry-ready onset retain forward continuation edge from executable T+1 Open, and is there a distinct post-breakout rejection/acceptance failure mode hidden by aggregate gap statistics?

This diagnostic does not import CAN SLIM/O'Neil morphology. The reference is the existing TrendFoll rolling-60-session prev_pivot_high.

## Corpus
Use governed research-history: current READY universe authority, deterministic SHA256-ranked 100-security sample, full canonical history, 500-bar pre-roll, adj_close historical EMA basis, and independent entry_ready False→True onsets detected on the full decision stream before restricting T0 to research_eligible. Baseline execution is T+1 Open.

## Frozen structural classifications
No fitted threshold is introduced.
- T+1 accepted: T+1 close >= T0 prev_pivot_high.
- T+1 rejected: T+1 close < T0 prev_pivot_high.
- T+1 retest-held: T+1 low <= pivot AND T+1 close >= pivot.
- T+1 stayed-above: T+1 low > pivot AND T+1 close >= pivot.
- Record whether any close is below the T0 pivot by T+3/T+5/T+10.

These are structural relationships to the existing breakout reference, not optimized margins.

## Outcomes
Baseline T+1 Open: close return T+1/T+3/T+5/T+10; MFE/MAE through 5 and 10 bars.

Causal post-T+1 observation: T+2 Open is the earliest clean execution anchor after T+1 close/low is known. For accepted, rejected, retest-held and stayed-above groups, report T+2 Open→T+5/T+10 and excursions where mature.

Never use T+1 close information while filling at T+1 Open.

## Governance
DIAG-001/002 remain authoritative for momentum, gap, volume/tightness and component attribution. EXIT-ISO-001 remains authoritative for exit isolation. This run must not re-mine thresholds.

A descriptive acceptance/rejection difference cannot itself authorize delayed entry, acceptance entry, retest entry, a pivot margin, or production change. If a causal T+2 representation is materially supported, freeze a candidate before untouched validation.

Boundaries: current READY universe is not PIT historical membership; daily OHLC cannot establish intraday ordering; this is event-path research, not portfolio simulation.
