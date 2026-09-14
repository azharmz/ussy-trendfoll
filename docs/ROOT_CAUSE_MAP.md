# TrendFoll Root Cause Map

Status: **REVISED AFTER VALID-HISTORY DIAG-001 / EVIDENCE-LINKED / NOT A ROADMAP**

This document translates diagnostic evidence into root-cause hypotheses. A root-cause hypothesis is not a development authorization. Historical conclusions from the original rolling-window DIAG-001 are superseded where they conflict with `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md`.

## RC-001 — Signal-day momentum expands post-entry risk dispersion

Linked problems: `PROB-009`, `PROB-011`.
Evidence: governed research-history rebuild of `DIAG-001`.

Observed under the valid-history contract:
- median T-1 -> T0 move is +3.07%;
- momentum-vs-T+5 Spearman rho is only +0.011, so there is no meaningful monotonic evidence that stronger signal-day momentum reduces T+5 return;
- momentum-vs-MFE5 rho is +0.232;
- momentum-vs-MAE5 rho is -0.210;
- strongest-momentum quartile has median MFE5 +3.66% and MAE5 -3.54%, versus +2.08% / -1.84% in the weakest quartile.

Current interpretation:
- the robust effect is **wider post-entry excursion**, not systematic return decay;
- stronger signal-day moves create more upside opportunity and more downside risk;
- the old claim that upper momentum buckets systematically produce worse T+5 returns is not reproduced and must not justify a momentum ceiling.

Status: **PARTIALLY SUPPORTED — DISPERSION/RISK EFFECT SUPPORTED; RETURN-DECAY EFFECT NOT SUPPORTED**.

## RC-002 — Early post-entry median fade is not supported after valid-history correction

Linked problems: `PROB-008`, `PROB-010`, `PROB-011`.
Evidence: governed research-history rebuild of `DIAG-001`.

Observed whole-sample medians:
- T0 close -> T+1 open: 0.00%;
- T+1 open -> T+1 close: +0.05%;
- T+1 open -> T+3 close: +0.22%;
- T+1 open -> T+5 close: +0.15%.

Current interpretation:
- the rebuilt corpus does not show deterioration from T+1 through T+5 at the median;
- the previous -0.27% median T+5 result came from the pre-PROB-019 historical architecture and is not robust evidence of early edge decay;
- T+1 execution remains a real execution constraint, but median post-entry fade is no longer a supported root cause.

Status: **NOT SUPPORTED BY VALID-HISTORY REBUILD / REOPEN ONLY WITH NEW EVIDENCE**.

## RC-003 — Large positive overnight gaps remain a weak execution-quality hypothesis

Linked problems: `PROB-010`, `PROB-011`.
Evidence: governed research-history `DIAG-001` descriptive gap quartiles.

Observed:
- largest gap-down quartile: median gap -0.95%, median T+5 +0.37%, positive rate 52.6%, MAE5 -2.56%;
- middle quartiles remain mildly positive at T+5;
- largest gap-up quartile: median gap +0.96%, median T+5 -0.10%, positive rate 48.7%, MAE5 -3.09%.

Current interpretation:
- the old symmetric “both gap extremes are weak” result is not reproduced;
- the largest positive-gap bucket is somewhat weaker and has worse adverse excursion, so positive-gap execution quality remains worth decomposing;
- no numeric gap limit is authorized because this is descriptive same-corpus evidence.

Status: **WEAK / UNRESOLVED HYPOTHESIS — INCLUDE IN DIAG-002, DO NOT TUNE**.

## RC-004 — Exit / risk conversion remains an open root cause

Linked problems: `PROB-011`, `PROB-013`.
Evidence:
- valid-history DIAG-001 event median T+5 is +0.15%;
- MFE5 median is +2.57% while MAE5 median is -2.50%;
- the valid-history rebuild intentionally does not link the small, later-calendar Supabase forward-position subset;
- `docs/CANSLIM_EXIT_AUDIT.md` separately challenges the current 45-day maximum and identifies the current 2 ATR / EMA20 exit rules as TrendFoll-specific rules requiring evidence.

Current interpretation:
- DIAG-001 no longer supports a claim that signals are broadly decaying by T+5;
- whether current stop/trend/time exits convert available excursion well remains unanswered;
- this must be measured directly by DIAG-003 rather than inferred from the old linked-position subset.

Status: **HIGH-PRIORITY OPEN ROOT CAUSE — DIAG-003 REQUIRED**.

## RC-005 — Position-history integrity can contaminate forward-outcome attribution

Linked problem: `PROB-017`.
Evidence from the original production-linked DIAG-001:
- 27 Supabase position rows contained one duplicate `(symbol, entry_date)` key: `ANF / 2026-08-26`;
- the rows had conflicting states/outcomes.

Current interpretation:
- the integrity issue is independent of the historical pre-roll correction;
- signal-path linkage must not silently select one duplicate and treat it as canonical;
- position persistence / active-position uniqueness history needs audit before forward exit attribution is treated as definitive.

Status: **CONFIRMED ENGINEERING/DATA-INTEGRITY ROOT CAUSE**.

## Not resolved by the rebuilt DIAG-001

- Point-in-time universe membership / survivorship bias: research still uses the current R2 readiness universe.
- Regime dependence: requires deliberate segmentation under the valid history contract.
- Investability component attribution: not yet decomposed.
- Volume/tightness incremental contribution: not yet decomposed.
- Pivot-extension contribution separate from signal-day raw momentum: not yet decomposed.
- Large positive-gap execution effect: only descriptive, not validated.
- Correct alternative entry rule: not researched or validated.
- Correct alternative exit rule: not researched or validated.

## Handoff to diagnostics

The valid-history rebuild changes the next questions. Recommended sequence:
1. `DIAG-002` entry-quality attribution: decompose momentum, ATR/pivot extension, positive opening gap, volume, tightness, Investability components, and interactions descriptively/pre-registered without threshold mining.
2. `DIAG-003` exit/risk conversion: measure early failure, current 2 ATR behavior, time-to-MFE, MFE/MAE, give-back, EMA20-loss timing, and the day-45 counterfactual.
3. Repair/audit position-history integrity before treating forward exit evidence as canonical.
4. Only then freeze a Roadmap/Development Plan from root causes that survive the governed diagnostics.
