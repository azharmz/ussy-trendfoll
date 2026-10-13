# TrendFoll Root Cause Map

Status: **REVISED AFTER VALID-HISTORY DIAG-001 + DIAG-002 / EVIDENCE-LINKED / NOT A ROADMAP**

This document translates diagnostic evidence into root-cause hypotheses. A root-cause hypothesis is not a development authorization. Historical conclusions from the original rolling-window DIAG-001 are superseded where they conflict with `docs/EVIDENCE_DIAG_001_RESEARCH_HISTORY.md`.

## RC-001 — Signal-day momentum expands post-entry risk dispersion

Linked problems: `PROB-009`, `PROB-011`.
Evidence: governed research-history rebuild of `DIAG-001` and entry attribution in `docs/EVIDENCE_DIAG_002_ENTRY_ATTRIBUTION.md`.

Observed under the valid-history contract:
- median T-1 -> T0 move is +3.07%;
- momentum-vs-T+5 Spearman rho is only +0.011, so there is no meaningful monotonic evidence that stronger signal-day momentum reduces T+5 return;
- momentum-vs-MFE5 rho is +0.232;
- momentum-vs-MAE5 rho is -0.210;
- strongest-momentum quartile has median MFE5 +3.66% and MAE5 -3.54%, versus +2.08% / -1.84% in the weakest quartile.
- DIAG-002 corroborates this shape across 1,545 eligible onsets: momentum-vs-T+5 rho +0.011, MFE5 rho +0.232, MAE5 rho -0.210.

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
Evidence: governed research-history `DIAG-001` and pre-registered `DIAG-002` descriptive gap attribution.

Observed:
- largest gap-down quartile: median gap -0.95%, median T+5 +0.37%, positive rate 52.6%, MAE5 -2.56%;
- middle quartiles remain mildly positive at T+5;
- largest gap-up quartile: median gap +0.96%, median T+5 -0.10%, positive rate 48.7%, MAE5 -3.09%.
- within positive-gap events only (N=729), the largest gap quartile has median gap +1.71%, median T+5 -0.33%, positive rate 47.3%, and MAE5 -3.77%; overall positive-gap-vs-T+5 rho is only -0.019.

Current interpretation:
- the old symmetric “both gap extremes are weak” result is not reproduced;
- the largest positive-gap bucket is somewhat weaker and has worse adverse excursion, so positive-gap execution quality remains worth decomposing;
- no numeric gap limit is authorized because this is descriptive same-corpus evidence.

Status: **WEAK / UNRESOLVED HYPOTHESIS — DIAG-002 COMPLETED; DO NOT TUNE**.

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

## RC-006 — Volume/tightness show limited and mixed T+5 separation

Linked problems: `PROB-012`, `PROB-015`.
Evidence: `docs/EVIDENCE_DIAG_002_ENTRY_ATTRIBUTION.md`.

Observed:
- breakout-volume-percentile vs T+5 rho is +0.024; quartile medians are non-monotonic.
- VCP-tightness vs T+5 rho is +0.026, while rho vs MFE5 is -0.141 and vs MAE5 is +0.149.
- the tight-structure subset (N=234) has median T+5 +0.229% and positive rate 55.1%, versus +0.093% and 50.7% when false (N=1,311); its median MFE5 is lower (+2.13% vs +2.73%) and MAE5 is less adverse (-2.08% vs -2.57%).

Current interpretation:
- volume percentile does not show a clear monotonic T+5 association in this sample;
- tight structure has modest descriptive separation, but outcome and excursion summaries are mixed;
- repeated events are clustered within 60 symbols, and current-universe sampling is not point-in-time. These are hypothesis-prioritization observations, not incremental-effect estimates.

Status: **WEAK / MIXED — NO ENTRY-GATE OR THRESHOLD CHANGE AUTHORIZED**.

## Not resolved after DIAG-002

- Point-in-time universe membership / survivorship bias: research still uses the current R2 readiness universe.
- Regime dependence: non-identifiable in the entry-ready corpus because all observed events have market regime Bullish after the hard-filter gate; a pre-gate candidate corpus is needed.
- Investability component attribution: non-identifiable in the entry-ready corpus because all observed component statuses are PASS; a separately defined pre-gate corpus is needed.
- Volume/tightness incremental contribution: only univariate descriptive evidence; no incremental or causal effect established.
- Pivot-extension contribution separate from signal-day raw momentum: DIAG-002 shows weak/non-monotonic T+5 separation; no cap is justified.
- Large positive-gap execution effect: weak descriptive signal, not validated.
- Correct alternative entry rule: not researched or validated.
- Correct alternative exit rule: not researched or validated.

## Handoff to diagnostics

The valid-history rebuild changes the next questions. Recommended sequence:
1. `DIAG-002` entry attribution **completed**; evidence is locked in `docs/EVIDENCE_DIAG_002_ENTRY_ATTRIBUTION.md`. No entry threshold or rule change is authorized.
2. `DIAG-003` exit/risk conversion: measure early failure, current 2 ATR behavior, time-to-MFE, MFE/MAE, give-back, EMA20-loss timing, and the day-45 counterfactual under a frozen contract.
3. Repair/audit position-history integrity before treating linked forward-position outcomes as canonical; keep this separate from full historical event reconstruction.
4. Resolve regime/Investability identifiability with a separately defined pre-gate corpus if still needed; do not infer no effect from the entry-ready sample.
5. Only then freeze a Roadmap/Development Plan from root causes that survive the governed diagnostics.
