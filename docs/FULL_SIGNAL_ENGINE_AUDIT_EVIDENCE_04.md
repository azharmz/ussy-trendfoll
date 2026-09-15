# Full Signal Engine Audit — Evidence 04

Status: **DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Feature-by-feature classification checkpoint

This checkpoint consolidates code-traced feature semantics before any correction specification.

| Component | Current implementation | Audit classification |
|---|---|---|
| EMA stack | `close_raw > EMA20 > EMA50 > EMA150 > EMA200`; terminal EMA state replaced from canonical R2 EMA | `MISMATCH` historically / terminal mitigation present |
| Stage | weekly W-FRI close, 30-week SMA, recent slope; Stage1–4 heuristic | `APPROXIMATION` |
| RS | stock 63-session adjusted return minus SPY 63-session return | `VALID USSY DEFINITION` for internal RS metric; not an O'Neil RS Rating |
| Liquidity | 50-session average raw share volume; PASS >=300k, NEAR >=240k | `VALID USSY DEFINITION` |
| Price | PASS >=10, NEAR >=8 | `VALID USSY DEFINITION` |
| Regime | benchmark-derived Bullish/Neutral/Bearish | `MATCH` to current USSY contract; benchmark freshness still `NEEDS_EVIDENCE` |
| Pivot | prior rolling 60-session high (`shift(1)` downstream) | `MISMATCH` versus O'Neil/base-specific pivot semantics; valid generic breakout level |
| Tightness | `100 - ATR percentile(63)` | `MISMATCH` versus VCP morphology; valid volatility-compression proxy |
| Breakout volume | current raw-volume percentile in rolling 50 sessions; confirmation >=80 | `APPROXIMATION` |
| Tradability | breakout + volume confirmation + tightness | `VALID USSY DECISION COMPOSITION`, subject to component semantic findings |

## Hard filter and Investability

Hard filter is non-compensatory. Its components are trend, liquidity, RS, price and regime. Investability is separately composed from trend, liquidity, RS and price only.

This means a symbol can have an Investability status that does not encode market regime. Downstream code must preserve that distinction.

## Tradability temporal boundary

`prev_pivot_high = pivot_high.shift(1)` is causal. A breakout decision using T0 close and T0 completed volume is knowable only after the T0 session closes. It is therefore a **signal-time T0-close** state, not an executable T0-close fill assumption. Research that measures an executable entry must use a later executable price such as T+1 Open under current governance.

## Correction boundary

No formula is changed here. In particular:

- Stage is not silently redefined.
- rolling-high pivot is not silently relabeled as an O'Neil pivot.
- ATR-percentile compression is not silently relabeled as a full VCP detector.
- current volume percentile is not silently relabeled as an authoritative breakout-volume rule.

Any future correction must first state the intended contract, freeze the correction specification, add tests, and then undergo governed validation.