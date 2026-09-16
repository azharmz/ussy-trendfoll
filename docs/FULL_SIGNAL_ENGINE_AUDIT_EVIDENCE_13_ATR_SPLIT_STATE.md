# Full Signal Engine Audit — Evidence 13: ATR Split-Sensitive State

Status: **RESEARCH CORRECTION CONTRACT PASS / BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_FACTS / NO PRODUCTION CHANGE**

Date: 2026-09-17

## Finding

Core C06 established that the existing ATR equation is mechanically valid on ordinary continuous raw-price windows, but raw OHLC state is not continuous across share-split boundaries. A pre-split `prev_close_raw` and post-split `high_raw`/`low_raw` are different per-share units. True-range gap terms can therefore interpret a corporate-action discontinuity as volatility. Because ATR uses recursive EWM state, that mechanical shock can persist after the event.

This is production-relevant because `positions.py` stores ATR at T0 and derives the realistic stop from `H+1 Open - 2 * ATR(T0)`.

## Frozen research correction contract

The research correction does not tune strategy parameters. ATR remains period 14 with `alpha=1/14`, `adjust=False`, and the existing true-range equation.

For each as-of evaluation row T0:

1. historical raw OHLC observations are expressed on the share basis effective at T0;
2. only split ratios effective on or before T0 may be used;
3. a split effective on date j transforms observations strictly before j, not the same-day/post-event raw bar;
4. a future split must never rewrite an earlier as-of ATR value;
5. a required split whose authoritative factor is unknown fails closed rather than silently mixing price units.

Research implementation: `atr_split_adjustment.py`.

## Frozen contract tests

`tests/test_atr_split_adjustment.py` covers:

- no-split identity against the existing ATR equation;
- 2-for-1 split mechanical-gap removal;
- reverse-split mechanical-gap removal;
- future-split non-leakage;
- unknown-factor fail-closed behavior;
- same-day event bar not double-adjusted.

Workflow: `.github/workflows/audit-atr-split-adjustment.yml`.

Run `35161603163`, job `105013382516`: **SUCCESS**. The frozen ATR split-adjustment contract test step completed successfully.

## Production disposition

The research correction is **not production-integrable yet**. Current R2 READY/TrendFoll ingestion does not carry authoritative split facts; the adapter currently synthesizes `stock_splits=0.0`. Therefore absence of a split in the current frame is not evidence that no split occurred.

This creates the same upstream dependency already exposed by FSE-014 liquidity normalization: `ussy-data` must provide authoritative corporate-action/split facts with effective-date and lineage semantics before TrendFoll can safely normalize split-sensitive rolling state.

No production file is changed by this evidence cycle.

## Verdict

- Existing ATR equation on continuous/no-action windows: **MATCH / VALID USSY DEFINITION**.
- Existing raw ATR state across split boundaries: **MISMATCH**.
- Frozen causal normalization contract: **PASS in research tests**.
- Temporal semantics: **PASS**; future splits do not alter prior as-of ATR.
- Production integration: **BLOCKED_ON_UPSTREAM_CORPORATE_ACTION_FACTS**.
- Threshold/period tuning: **OUT OF SCOPE / NOT PERFORMED**.

This finding is now dispositioned rather than open-ended: the correction mechanics are demonstrated, while production adoption is explicitly blocked until the required upstream facts exist.