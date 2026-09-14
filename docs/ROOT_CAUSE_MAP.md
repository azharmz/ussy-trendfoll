# TrendFoll Root Cause Map

Status: **INITIAL / EVIDENCE-LINKED / NOT A ROADMAP**

This document translates diagnostic evidence into root-cause hypotheses. A root-cause hypothesis is not yet a development authorization.

## RC-001 — Signal-day overextension / volatility expansion

Linked problems: `PROB-009`, `PROB-011`.
Evidence: `DIAG-001`.

Observed:
- median T-1 -> T0 move is +5.50%;
- upper momentum half has negative median T+5 returns;
- the strongest-momentum quartile has both higher MFE and materially worse MAE.

Current interpretation:
- strong signal-day momentum is not simply "bad"; it creates a wider post-entry outcome distribution;
- downside excursion worsens faster than the central T+5 outcome improves;
- overextension is therefore a credible contributor to execution risk, but no cutoff is validated.

Status: **SUPPORTED HYPOTHESIS — NEEDS DEVELOPMENT TEST**.

## RC-002 — Edge decays after executable entry, not primarily in the overnight bridge

Linked problems: `PROB-008`, `PROB-010`, `PROB-011`.
Evidence: `DIAG-001`.

Observed whole-sample medians:
- T0 close -> T+1 open: +0.03%;
- T+1 open -> T+1 close: +0.13%;
- T+1 open -> T+3 close: +0.03%;
- T+1 open -> T+5 close: -0.27%.

Current interpretation:
- the median overnight gap is too small to explain the deterioration by itself;
- central tendency is roughly flat through T+3 and becomes slightly negative by T+5;
- this supports an early post-entry fade / insufficient follow-through hypothesis more than a simple "T+1 gap makes entry too expensive" hypothesis.

Status: **SUPPORTED HYPOTHESIS — NEEDS ATTRIBUTION**.

## RC-003 — Extreme overnight gaps may degrade execution quality

Linked problems: `PROB-010`, `PROB-011`.
Evidence: `DIAG-001` descriptive quartiles.

Observed:
- middle gap buckets have positive median T+5 results;
- both largest gap-down and largest gap-up quartiles have negative median T+5 results and larger adverse excursion.

Current interpretation:
- execution quality may be non-linear with respect to overnight gap;
- no numeric gap limit is authorized because the buckets were created descriptively from the same corpus.

Status: **SUPPORTED HYPOTHESIS — DEVELOPMENT ONLY IF PRE-REGISTERED**.

## RC-004 — Exit / risk handling remains a plausible contributor

Linked problems: `PROB-011`, `PROB-013`.
Evidence:
- full event sample median T+5 return is only -0.27%;
- linked forward-position median realized return is about -6.09%;
- linked position sample is small and includes only 24 independently-linked events.

Current interpretation:
- the difference is large enough that exit/risk behavior must be diagnosed explicitly;
- it is not valid yet to conclude the exit rules are the cause, because the forward-position subset is small, non-random, later in calendar time, and subject to position-history integrity issues.

Status: **HIGH-PRIORITY OPEN ROOT CAUSE**.

## RC-005 — Position-history integrity can contaminate forward-outcome attribution

Linked problem: new integrity issue from DIAG-001.
Evidence:
- 27 Supabase position rows contain one duplicate `(symbol, entry_date)` key: `ANF / 2026-08-26`;
- the two rows have different states/outcomes.

Current interpretation:
- signal-path linkage must not silently select one duplicate and treat it as canonical;
- position persistence / active-position uniqueness history needs audit before exit attribution is treated as definitive.

Status: **CONFIRMED ENGINEERING/DATA-INTEGRITY ROOT CAUSE**.

## Not resolved by DIAG-001

- Regime dependence: all entry-ready events in this corpus passed the Bullish regime gate.
- Investability component attribution: not yet decomposed.
- Volume/tightness incremental contribution: not yet decomposed.
- Correct production alternative for overextension/gap handling: not researched or validated.
- Correct alternative exit rule: not researched or validated.

## Handoff to roadmap

Only after the next diagnostic layer should these become roadmap items. Recommended sequence:
1. `DIAG-002` entry-quality attribution: momentum/extension, gap, volume, tightness and pivot extension.
2. `DIAG-003` exit/risk attribution using reconstructed historical exits plus cleaned Supabase forward subset.
3. Repair/audit position-history integrity before treating forward exit evidence as canonical.
4. Then freeze Roadmap v1 and Development Plan v1 from the supported root causes.
