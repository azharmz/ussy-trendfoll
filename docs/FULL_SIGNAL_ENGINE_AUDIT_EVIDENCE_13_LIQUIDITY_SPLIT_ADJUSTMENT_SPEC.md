# Full Signal Engine Audit — Evidence 13: FSE-014 Liquidity / Split Adjustment Correction Specification

Status: **CORRECTION SPECIFICATION FROZEN / IMPLEMENTATION NOT STARTED / NO PRODUCTION CHANGE**

## Scope

Freeze the intended correction contract for FSE-014 before any implementation or validation work.

FSE-014 exists because current `avg_volume_50d` is the rolling mean of raw daily share volume. Around a stock split or stock dividend, raw pre-event and post-event share counts are expressed on different share-unit bases. A 50-session window can therefore mix structurally incomparable observations even when underlying trading activity is economically continuous.

Evidence 11 already established empirical exposure to this condition in the current data population.

## External methodology evidence

CRSP documents the standard comparability principle directly: price, shares, and volume histories may be adjusted for split events so observations at different points in a security history are comparable on a common adjustment-base date. CRSP further states that shares and volumes are adjusted using stock splits and stock dividends, and exposes a cumulative factor specifically for adjusting shares/volume (`CFACSHR`).

Relevant methodology references:

- CRSP Stock/Index Data Descriptions: adjusted data are converted to a common base date; shares and volumes are adjusted for stock splits and stock dividends.
- CRSP/WRDS variable definitions expose `CFACSHR` as the cumulative factor to adjust shares/volume.
- yfinance exposes explicit split-event retrieval (`Ticker.get_splits()` / `Ticker.splits`), so split events can be obtained independently of dividend adjustment factors.

These references support split-adjusting historical share volume when the intended metric is average daily share liquidity across a window spanning a split. They do **not** support using the `adj_close / close` ratio as a volume factor because that price-adjustment relationship can include cash-distribution effects that are not share-count transformations.

## Frozen intended contract

### Semantic target

`avg_volume_50d` remains a **share-liquidity** measure, not a dollar-liquidity measure.

The correction therefore preserves the existing meaning and existing PASS/NEAR thresholds as a separate governance question. It does not silently redefine liquidity from average shares traded to average dollar turnover.

### Canonical volume basis

For each security and each evaluation date `T0`, all raw volume observations inside the rolling liquidity window must be expressed on the **T0 share-unit basis** using only stock-split / stock-dividend share factors effective between the historical observation and T0.

Conceptually:

`volume_on_T0_basis(t) = raw_volume(t) * cumulative_share_factor(t -> T0)`

where the cumulative factor contains only share-count-changing split/stock-dividend events relevant to volume normalization.

For a conventional 2-for-1 split between historical date `t` and T0, a pre-split observation of 100,000 shares becomes 200,000 shares on the T0 basis. Post-split observations remain unchanged. Reverse splits transform in the opposite direction.

### Rolling formula

After normalization:

`avg_volume_50d = rolling_mean(volume_on_T0_basis, window=50, min_periods=20)`

The current 50-session window and `min_periods=20` are retained in this correction cycle. Their rationale is audited separately under D4.3/D4.5 and must not be changed inside FSE-014 implementation merely to improve validation results.

### Thresholds

Current thresholds remain unchanged for this correction cycle:

- PASS: `avg_volume_50d >= 300,000`
- NEAR_PASS: `avg_volume_50d >= 240,000`
- FAIL: below NEAR_PASS threshold or existing governed missing-state behavior.

This freeze does **not** claim those thresholds are methodologically validated; D4.3 remains open. It only prevents FSE-014 from combining a unit-basis correction with threshold tuning.

## Explicitly rejected alternatives for this correction cycle

### 1. Raw-volume window segmentation at each split

Rejected as the canonical correction because it discards otherwise valid pre-split trading observations and creates avoidable warm-up discontinuities after every split. It may be used only as a fail-closed fallback if trustworthy split factors are unavailable.

### 2. Dollar volume (`price * volume`)

Not adopted in FSE-014 because it changes the economic meaning and units of the production liquidity feature and makes the existing 240k/300k share thresholds meaningless. Dollar-volume liquidity may be researched separately under a new governed finding/specification.

### 3. Deriving volume factors from `adj_close / close`

Rejected. Price adjustment can reflect distributions that are not share-count transformations. Volume normalization must use an explicit share/split factor, not a generic adjusted-price ratio.

### 4. Threshold tuning to absorb split artifacts

Rejected. A data-unit inconsistency must be corrected at the data/feature basis, not hidden by changing liquidity thresholds.

## Required data contract before implementation

Implementation must have a reproducible split-event/share-factor source keyed by stable `security_id` and effective date.

Preferred architecture:

1. upstream `ussy-data` obtains and persists explicit split events/factors with lineage;
2. READY or a companion governed derived-state contract exposes the factors needed to normalize the rolling window;
3. TrendFoll consumes those governed factors rather than independently downloading live corporate-action facts during production decisioning.

A research prototype may use yfinance split events to test the frozen formula, but such live retrieval is not automatically approved as the production contract.

If a required split factor is missing or internally inconsistent for a known corporate-action-sensitive window, implementation must fail closed for the corrected liquidity fact rather than silently reverting to mixed-unit raw volume.

## Temporal semantics

Only split events effective on or before T0 may affect the T0 normalized volume window. Future split events must never back-propagate into a historical as-of calculation used for signal/backtest evaluation.

This creates two distinct legitimate representations:

- current production T0 liquidity: history normalized to the T0 share basis using events known/effective through T0;
- historical research row at historical date H: history normalized only using events effective through H, not later events.

The implementation must therefore be as-of causal, not a globally back-adjusted dataset that leaks future corporate actions into historical signal states.

## Required tests before governed validation

At minimum:

1. no-split identity: corrected volume equals raw volume when no split occurs in the relevant history;
2. 2-for-1 split: pre-split volume is multiplied by 2 on post-split T0 basis;
3. reverse split: pre-event volume is transformed by the inverse share-unit change correctly;
4. multiple split events: cumulative factor composes correctly;
5. split exactly inside/outside the 50-session window;
6. min-period behavior remains exactly 20 observations;
7. no future-event leakage into historical as-of rows;
8. missing/inconsistent factor fails closed rather than mixing units;
9. unaffected securities retain identical liquidity status;
10. corporate-action-sensitive Evidence-11 symbols show removal of mechanical split-unit discontinuity without threshold changes.

## Validation governance

Sequence is frozen as:

`development sample -> implementation -> regression tests -> freeze implementation -> untouched validation population -> one-shot validation -> explicit production decision`

No threshold, window, factor logic, or fallback rule may be tuned after untouched validation without opening a new governed cycle.

## Disposition

FSE-014 now has a frozen intended correction specification. The next permitted step is a **research-only implementation/prototype plus tests** against explicit split-event factors. Production remains unchanged.

D4.3 (threshold rationale) and D4.5 (min-period/warm-up behavior) remain separate open audit items. Passing an FSE-014 split-normalization validation will not by itself validate the 240k/300k thresholds or `min_periods=20` policy.
