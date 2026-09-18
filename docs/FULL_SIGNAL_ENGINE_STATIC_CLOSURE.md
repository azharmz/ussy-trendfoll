# Full Signal Engine Audit — Static Closure

Status: **STATIC REVIEW COMPLETE / DYNAMIC E2E PENDING / NO PRODUCTION CHANGE**

This document closes the production-path checks that do not require a fresh R2 READY publication. It does not replace the terminal E2E rerun.

## 1. Downstream contract

### Investability

`compute_investability()` is non-compensatory across exactly four structural statuses: trend, liquidity, RS, and price. Any FAIL -> FAIL; otherwise any NEAR_PASS -> NEAR_PASS; otherwise PASS. Market regime is deliberately excluded.

NaN handling occurs upstream in `hard_filter.py`: threshold-based NaN values fail closed; invalid/missing trend state fails closed; missing/unknown market regime fails closed in the hard filter.

Verdict: **MATCH / VALID USSY DEFINITION / RETAIN**.

### Tradability

Breakout is the hard gate. The reference is prior-row `pivot_high` via per-symbol shift. Volume confirmation and tightness distinguish PASS from NEAR_PASS. A breakout with neither confirmation is still NEAR_PASS by explicit code contract.

NaN pivot cannot create breakout because `prev_pivot_high.notna()` is required. NaN volume percentile and NaN tightness evaluate false in the threshold comparisons, so they cannot create confirmations.

Verdict: **MATCH mechanics / VALID USSY internal aggregation / RETAIN**, subject to already-recorded semantic findings for rolling-high pivot, volume proxy, and VCP/tightness proxy.

## 2. Dual downstream contracts

The code intentionally has two different consumers:

1. Watchlist/alerts: monitored when Investability >= NEAR_PASS; ACTIONABLE only when Investability PASS and Tradability PASS.
2. Authoritative position entry: `hard_filter_status == PASS` AND breakout AND volume confirmation. Tightness is not an entry gate.

These predicates are not interchangeable. Production entry includes market regime through `hard_filter_status`, while Investability intentionally excludes regime.

Verdict: **FSE-011 intentional dual contract / RETAIN + REDOCUMENT**. Do not silently unify the predicates.

## 3. Lifecycle / alert absence semantics

`compute_alert_transitions()` distinguishes a previous watchlist symbol absent from the common-date latest snapshot from a symbol that has left the R2 universe:

- still in current READY universe but absent from latest -> `DATA_UNAVAILABLE`;
- absent from current READY universe -> `OUT_OF_UNIVERSE`;
- present but no longer Investability >= NEAR_PASS -> `INVALIDATED`.

It also rejects a latest snapshot containing symbols outside the declared current R2 universe.

Verdict: **VALID USSY DEFINITION / fail-closed semantics retained**.

## 4. Production position coverage and T0/T+1 boundary

Before lifecycle/position processing, `main.py` calls `validate_active_position_coverage()`. Any active position missing from the common-date latest snapshot raises and fails the run. The Sep-16 mixed-date READY incident demonstrated this guard operating as intended.

New positions are triggered from T0 close-state facts. The trigger record initially stores T0 close and ATR14(T0). `fill_realistic_entry_prices()` later fills `realistic_entry_price` from the first subsequent trading row's `open_raw` and reanchors the active stop to H+1 Open - 2*ATR14(T0). Thus modeled realistic execution is separated from T0 signal detection.

Verdict: **temporal boundary PASS**, while FSE-016 remains applicable to the corporate-action basis of ATR14 itself.

## 5. Latest-date contract

`main.py` currently defines `as_of_date = decided.date.max()` and constructs `latest` from that date. This is safe only when upstream READY has a coherent terminal-date publication contract. The Sep-16 incident showed why a mixed leading edge is unsafe. The upstream `ussy-data` terminal-date histogram publication guard is therefore a required external precondition for terminal E2E closure; TrendFoll must not weaken its active-position fail-closed guard to accommodate mixed READY.

Verdict: **downstream behavior correct under coherent READY precondition / dynamic verification pending upstream #49**.

## 6. Auxiliary/dead feature classification

Static consumer tracing of the current decision and production path establishes that production decisions are driven by the explicitly traced fields in hard filter, Investability, Tradability, alert state, and positions. Auxiliary feature-engine outputs such as volatility regime, sector RS, RS persistence, volume ratio/dry-up, ADX, 52-week-high distance, and `base_length_days` are not part of the authoritative entry predicate shown in `positions.py`, nor the Investability/Tradability aggregation in `decision_layer.py`.

Classification for the Full Signal Engine decision audit: **DEAD / UNUSED as authoritative production decision inputs unless a separate consumer is demonstrated**. They may remain diagnostic/explanatory/research fields; this classification is not permission to delete them.

## 7. Remaining dynamic closure

Static review is complete. Do not spend Actions compute on additional static validation.

Terminal acceptance requires a healthy upstream READY publication and then one production-path rerun demonstrating:

- coherent common effective date across READY securities;
- exact SPY T0 readiness PASS;
- shared EMA lineage PASS against that READY;
- active-position coverage PASS;
- hard filter -> decision layer -> watchlist/lifecycle/alerts -> position path reaches terminal success;
- no new correctness defect appears in the final funnel.

Known non-terminal blockers remain explicit rather than hidden:

- FSE-014 liquidity split normalization: blocked on authoritative upstream corporate-action factors.
- FSE-016 ATR split-sensitive state: research correction PASS, blocked on authoritative upstream corporate-action factors.

Neither blocker should be faked or silently approximated merely to close this audit.
