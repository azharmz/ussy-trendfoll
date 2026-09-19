# TrendFoll Root Cause Map

Status: **REVISED AFTER VALID-HISTORY DIAG-001/002/003 / EVIDENCE-LINKED / NOT A ROADMAP**

This document translates diagnostic evidence into root-cause hypotheses. A root-cause hypothesis is not a development authorization. Historical conclusions from the original rolling-window DIAG-001 are superseded where they conflict with governed research-history evidence.

## RC-001 — Signal-day momentum expands post-entry risk dispersion

Linked problems: `PROB-009`, `PROB-011`.
Evidence: governed research-history DIAG-001 and DIAG-002.

Observed under the valid-history contract:
- momentum-vs-T+5 Spearman rho is approximately +0.011, so there is no meaningful monotonic evidence that stronger signal-day momentum reduces T+5 return;
- momentum-vs-MFE5 is positive while momentum-vs-MAE5 is negative;
- stronger signal-day moves expand both upside opportunity and downside risk.

Current interpretation: the robust effect is wider post-entry excursion, not systematic T+5 return decay. No momentum ceiling is authorized.

Status: **PARTIALLY SUPPORTED — DISPERSION/RISK EFFECT SUPPORTED; RETURN-DECAY EFFECT NOT SUPPORTED**.

## RC-002 — Early post-entry median fade is not supported

Linked problems: `PROB-008`, `PROB-010`, `PROB-011`.
Evidence: governed research-history DIAG-001/002.

Observed whole-sample medians remain slightly positive from T+1 Open through T+5, and DIAG-003 shows checkpoint-close negative rates near one half rather than broad immediate collapse.

Current interpretation: T+1 execution is a real constraint, but general early median fade is not a supported root cause.

Status: **NOT SUPPORTED BY VALID-HISTORY EVIDENCE / REOPEN ONLY WITH NEW EVIDENCE**.

## RC-003 — Large positive overnight gaps remain a weak execution-quality hypothesis

Linked problems: `PROB-010`, `PROB-011`.
Evidence: governed DIAG-001/002 descriptive attribution.

The largest positive-gap bucket is somewhat weaker and has worse adverse excursion, but the effect is descriptive and does not authorize a numeric gap limit.

Status: **WEAK / UNRESOLVED HYPOTHESIS — DO NOT TUNE**.

## RC-004 — Current exit / risk conversion is materially implicated

Linked problems: `PROB-011`, `PROB-013`.
Evidence: `docs/EVIDENCE_DIAG_003_EXIT_RISK.md`.

DIAG-003 directly reproduced the current exit stack on 1,545 governed entry-ready event paths. On the 1,524 paths mature for 45 bars:
- current-rule median realized return: **-3.46%**;
- current-rule positive rate: **33.01%**;
- day-45 close counterfactual ignoring earlier exits: **+1.70% median**;
- day-45 positive rate: **56.43%**;
- stop loss is the dominant exit reason (839/1,524 mature paths);
- median current holding time is 16 bars, while median time-to-45-bar-MFE is 27 bars;
- median MFE grows from +2.57% at 5 bars to +9.09% at 45 bars, while MAE also widens from -2.50% to -7.86%.

Current interpretation:
- exit/risk conversion is now supported as a **material root cause** in the governed corpus;
- the mechanism is not isolated: this evidence cannot determine whether the 2 ATR stop, EMA20 exit, 45-day maximum, or interactions should change;
- the day-45 counterfactual is diagnostic, not a hold-45 strategy recommendation;
- any replacement exit hypothesis requires a separate evidence-backed development and untouched-validation cycle.

Status: **SUPPORTED MATERIAL ROOT CAUSE / MECHANISM ISOLATED / EXIT-CAND-003 OOS-SUPPORTED + SHADOW ACTIVE**.

Subsequent governed component isolation (`EXIT-ISO-001`) identified the fixed 2 ATR stop as the primary implicated conversion mechanism. Frozen `EXIT-CAND-003` then passed development and untouched validation, improving median return, positive rate, and median MAE versus the frozen CURRENT comparator. It remains not production-authorized and is accumulating genuine shadow evidence.

## RC-005 — Position-history integrity can contaminate forward-outcome attribution

Linked problem: `PROB-017`.
Evidence from production-linked position history: duplicate `(symbol, entry_date)` rows can contain conflicting states/outcomes.

Current interpretation: signal-path linkage must not silently select one duplicate and treat it as canonical. This engineering/data-integrity issue remains independent of the historical research-path evidence.

Status: **RESOLVED / EVIDENCE LOCKED**. Canonical lifecycle linkage is `positions.id`; `(symbol, entry_date)` is a replay/idempotency invariant, not the downstream foreign key.

## RC-006 — R2 symbol/date mapping ambiguity can contaminate feature timelines

Linked problem: `PROB-005`.
Evidence: `docs/EVIDENCE_PROB_005.md`.

TrendFoll historically validated upstream `(security_id,date)` uniqueness but dropped `security_id` when adapting READY rows to the feature-engine contract. Therefore a future many-to-one `security_id -> ticker` mapping could collapse into the same downstream `(symbol,date)` timeline without an explicit boundary guard.

Current canonical READY mapping is one-to-one under the audited contract; no collision evidence was found in the available production/validation lineage. The remediation is preventive and fail-closed.

Status: **RESOLVED / EVIDENCE LOCKED — PREVENTIVE LOADER HARDENING**.

## RC-007 — Alert delivery lacked durable event identity and acknowledgement state

Linked problems: `PROB-003`, `PROB-004`.
Evidence: `docs/EVIDENCE_PROB_003_004.md`.

The old pipeline computed transitions in memory and called Telegram directly. Watchlist persistence stored state observations, not alert-event identity or transport outcomes. Same-day replay could therefore recreate the same transition and resend it, while transport failures were swallowed.

Status: **RESOLVED / EVIDENCE LOCKED**. Semantic events, transport delivery state and append-only attempts are now persisted separately; normal replay/concurrency is database-arbitrated and failures remain retryable. Telegram Bot API crash-window exactly-once delivery remains an explicit transport limitation.

## Still unresolved

- Point-in-time universe membership / survivorship bias.
- Regime dependence beyond the currently identifiable corpus.
- Investability component causal contribution where components are constant by construction.
- Correct production-authorized alternative entry rule. EDGE-CAND-001 acceptance is structurally informative but closed for promotion under the tested economic representation.
- Production authorization for an alternative exit remains unresolved. EXIT-CAND-003 is the current frozen OOS-supported candidate in operational shadow; the fixed 2 ATR stop is the primary implicated current component.
- Portfolio/capital-level performance.

## Handoff after diagnostics

DIAG-001/002/003 now support the following governance sequence:
1. Treat general early post-entry fade as rejected under current valid-history evidence.
2. Retain entry momentum/gap effects only as risk/weak descriptive hypotheses; do not mine thresholds.
3. Promote `RC-004` to a supported root cause, but **do not tune the production exit stack from DIAG-003 itself**.
4. Build a separately justified exit-development hypothesis set from authoritative methodology/literature and/or a frozen component-isolation diagnostic.
5. Freeze the selected development representation before outcome comparison; then perform untouched validation with no post-validation tuning.
6. Continue PROB-016 frozen forward validation independently.
7. Harden engineering debts PROB-003/004/005/017 without changing trading semantics.

## RC-008 — T+1 breakout rejection is structurally weaker but acceptance did not solve realized economics

Linked problems: `PROB-008`, `PROB-012`, `PROB-013`.
Evidence: `docs/EVIDENCE_EDGE_DECOMP_001.md`, `docs/EVIDENCE_EDGE_CAND_001_OOS.md`, `docs/EVIDENCE_EDGE_ECON_001.md`.

Development and security-holdout evidence support a descriptive distinction between T+1 acceptance and rejection relative to the existing TrendFoll rolling-60D breakout reference. A frozen causal acceptance candidate passed path-level OOS gates. However, combining the accepted T+2 entry with frozen EXIT-CAND-003 still yielded negative realized median economics at every tested cost sensitivity, with weak 2022–2026 results.

Status: **STRUCTURAL FAILURE MODE SUPPORTED / PRODUCTION ENTRY REPLACEMENT NOT SUPPORTED UNDER TESTED REPRESENTATION**.
