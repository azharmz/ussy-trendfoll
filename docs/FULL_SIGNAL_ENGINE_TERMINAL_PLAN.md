# Full Signal Engine Audit — Terminal Plan

Status: **ACTIVE / CORE 10/10 FROZEN / TERMINAL E2E BLOCKED ON UPSTREAM READY VALIDATION / NO NEW PRODUCTION CHANGE**

This document reconciles the material audit state after the Core Indicator Audit and freezes the acceptance criteria for terminal closure. The older 269-item detailed checklist remains an Extended Engineering Audit ledger; unchecked legacy items do not automatically block the material correctness conclusion.

## 1. FSE-007 benchmark freshness — CLOSED

Production benchmark readiness now has an explicit fail-closed contract:

- RS requires an exact SPY row for the stock production as-of date.
- Missing exact SPY T0 raises and blocks production.
- A future SPY row cannot rescue a missing exact T0 row.
- SPY ahead of R2 is benign; rows after stock T0 are ignored for the decision date.
- Market regime may use same/prior SPY state through backward-as-of, but the production readiness boundary still requires exact SPY T0 because RS is decision-relevant.

`tests/test_benchmark_readiness.py` covers same-day readiness, R2-ahead-of-SPY fail-closed, SPY-ahead-of-R2, future-SPY non-rescue, and empty-SPY failure.

Operational evidence from TrendFoll run `35168011735`, rerun job `105038526592`, reached:

`[benchmark readiness] exact SPY T0 verified: as_of=2026-09-16`

before failing later on incoherent upstream READY terminal dates. Therefore that failure does not invalidate FSE-007.

Final FSE-007 verdict: **VALID USSY READINESS CONTRACT / CLOSED**.

Remaining architectural fact: stock facts come from governed R2 READY while benchmark facts are downloaded separately. This is documented architecture, not an unresolved silent-freshness defect under the current exact-SPY-T0 guard.

## 2. Material findings reconciliation

| Finding | Material status | Terminal action |
|---|---|---|
| FSE-001 Stage semantics | APPROXIMATION | RETAIN + REDOCUMENT; methodology research separate |
| FSE-002 VCP/tightness semantics | MISMATCH as literal VCP | RENAME/REDOCUMENT as ATR/volatility-tightness proxy; no threshold tuning here |
| FSE-003 pivot semantics | MISMATCH as O'Neil/base pivot | RENAME/REDOCUMENT as rolling-high breakout proxy; morphology research separate |
| FSE-004 breakout-volume semantics | APPROXIMATION | RETAIN as rolling volume-rank confirmation; evaluate normalized volume if FSE-014 becomes adoptable |
| FSE-005 historical EMA basis | MISMATCH | Separate legacy/history standardization debt; canonical terminal EMA remains governed adj_close state |
| FSE-006 price/EMA split | VALID USSY DEFINITION | RETAIN |
| FSE-007 benchmark freshness | CLOSED | Exact SPY T0 fail-closed contract retained |
| FSE-008 R2 warm-up/history | CHARACTERIZED / upstream readiness dependent | No silent terminal-EMA regression; final E2E requires coherent READY |
| FSE-009 regime architecture | MATCH | RETAIN |
| FSE-010 breakout temporal semantics | MATCH | RETAIN T0-close / T+1 execution governance |
| FSE-011 dual downstream contracts | INTENTIONAL | RETAIN + document: watchlist/actionability differs from authoritative production-entry predicate |
| FSE-012 entry semantics | VALID with naming caveat | RETAIN documented contract |
| FSE-013 effective-date lifecycle | CORRECTION VALIDATED / PRODUCTION ADOPTED | Preserve regression + untouched validation evidence |
| FSE-014 split-sensitive liquidity state | MISMATCH | BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_CONTRACT; do not fake split factors |
| FSE-015 Sep14 partial OHLCV/volume incident | CLOSED / VERIFIED | Do not reopen without new evidence |
| FSE-016 split-sensitive ATR state | MISMATCH | RESEARCH CORRECTION PASS / BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_FACTS |

## 3. Correction decision matrix

Production closure does not require silently solving every methodology approximation. Decisions are separated by correctness boundary:

- **Adopted/retained:** canonical terminal EMA, FSE-007 benchmark readiness, FSE-013 effective-date lifecycle correction, existing causal breakout mechanics, existing dual downstream contracts.
- **Retain but redocument/rename:** Stage approximation, rolling-high pivot/breakout proxy, rolling volume-rank confirmation, ATR-percentile tightness proxy.
- **Blocked rather than approximated:** FSE-014 and FSE-016 require authoritative upstream corporate-action facts. Synthetic `stock_splits=0.0` is not acceptable evidence and must not be used to manufacture a correction.
- **Closed incident:** FSE-015 upstream partial-current-day volume incident remains closed/verified unless new contradictory evidence appears.
- **Separate remediation:** historical legacy feature-engine raw/adjusted standardization is not folded into this terminal audit.

## 4. Current upstream blocker

TrendFoll run `35168011735` exposed an upstream READY coherence defect rather than a downstream signal-engine formula defect. The observed READY reported 1,227 securities / 367,522 rows, while the global latest date was 2026-09-16 for only 3 securities and 1,224 securities lacked that latest bar. Active-position coverage correctly failed closed for ANF, BOX, CF, OKTA, TXG, and VLO.

`ussy-data` root cause analysis identified a mixed terminal-date READY publication. Upstream validation run #49 (`35170777879`) is responsible for proving the new terminal-date-coherence publication guard. TrendFoll must not be rerun merely to obtain a green result until upstream READY is verified healthy.

## 5. Frozen terminal acceptance criteria

After upstream run #49 is terminal, rerun TrendFoll only if all upstream conditions are evidenced:

1. authoritative READY pointer is known and valid;
2. terminal-date histogram is coherent under the upstream publication contract;
3. manifest `as_of_date` and terminal-date coverage agree;
4. no partial leading-edge date was promoted;
5. shared EMA lineage matches the active READY object/checksum.

Then the TrendFoll terminal E2E run must demonstrate:

1. R2 READY loads and validates without mixed-date failure;
2. exact SPY T0 benchmark readiness passes;
3. canonical shared EMA lineage/equivalence passes;
4. feature store, hard filter, Investability and Tradability complete;
5. latest-date universe coverage is coherent under the READY contract;
6. candidate/watchlist/alert lifecycle completes without effective-date regression;
7. active-position coverage passes fail-closed checks;
8. production entry/exit path completes without contract error;
9. no finding is hidden by weakening readiness, temporal, or coverage guards.

A plausible funnel or a green workflow alone is not sufficient; logs must support these contract checks.

## 6. Terminal closure rule

If the upstream acceptance criteria and TrendFoll E2E criteria pass, the material Full Signal Engine Audit may be closed with explicit limitations for FSE-014/FSE-016 and methodology approximations. Those limitations are not to be mislabeled as validated O'Neil/Minervini semantics.

If terminal E2E exposes a new correctness defect, classify and resolve it under:

`finding -> root cause -> correction contract -> remediation -> regression -> untouched validation -> production decision`

Do not tune thresholds or broaden scope merely to make the terminal run green.

## 7. Progress

Material audit progress after formal FSE-007 closure and terminal-plan freeze: **approximately 98%**.

The remaining material work is the upstream READY validation gate followed by one coherent TrendFoll terminal production-funnel verification and final evidence recording.
