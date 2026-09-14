# CAN SLIM / O'Neil Exit Methodology Audit

Status: **RESEARCH NOTE / GOVERNANCE INPUT / NO PRODUCTION CHANGE**

Purpose: audit whether TrendFoll's current exit contract (`2 ATR stop + close < EMA20 + 45 trading-day maximum`) is conceptually aligned with the CAN SLIM / O'Neil family from which TrendFoll is adapted.

## Source-backed findings

### 1. Defensive loss control is central
Investor's Business Daily (IBD), founded by William J. O'Neil, describes the canonical loss-control rule as cutting a position around **7%-8% below the purchase price**, with earlier exits possible when technical or market weakness warrants it. This is a capital-protection rule, not a fixed holding-period rule.

### 2. Default profit-taking is strength-based, not age-based
IBD describes a default profit-taking guideline of roughly **20%-25% from the proper buy point** for many growth-stock breakouts. The logic is that many leaders advance materially after breakout and then correct, consolidate, or form another base. This is fundamentally different from forcing every trade out after a fixed number of trading days.

### 3. Exceptional strength creates an explicit hold exception
IBD's **eight-week hold rule** applies when a stock reaches roughly a 20% gain very quickly (about one to three weeks after breakout). Rather than forcing a time exit, unusually strong early performance can justify holding longer to capture a potential exceptional winner.

### 4. Failed breakouts should be distinguished from ordinary pullbacks
IBD notes that modest dips back toward or slightly below a buy point are common, while a deeper decline around 7%-8% below the proper entry is treated as breakout failure. This supports separating an **early breakout-failure state** from later trend deterioration.

### 5. IBD's CAN SLIM-adapted SwingTrader is much shorter-horizon than classic position CAN SLIM
IBD's own SwingTrader guide explicitly states that its methodology adapts CAN SLIM for swing trading. It describes most trades as roughly **5-10 days**, typical profit capture around **5%-10%**, and loss cutting around **2%-3%**. It also allows partial profit-taking and market-condition-dependent exits. This demonstrates that CAN SLIM-derived exit design is intentionally adapted to trading horizon rather than copied mechanically from the position-trading version.

## Implication for TrendFoll

The current **45 trading-day hard maximum** has no clear conceptual support from the CAN SLIM/O'Neil exit framework reviewed here. A fixed maximum age can mechanically terminate a still-healthy winner, while CAN SLIM-family methods emphasize:

`entry quality -> failed-breakout defense -> capital-loss control -> profit protection -> exceptional-winner handling -> technical deterioration`

This does **not** authorize deleting the 45-day rule immediately. It establishes that the rule should be treated as an unvalidated TrendFoll-specific implementation choice rather than as a CAN SLIM-derived principle.

## Required diagnostic decomposition for PROB-013 / DIAG-003

Before changing production exits, measure each historical/forward position through the following lifecycle:

1. **Early failure**
   - loss of pivot / re-entry into base
   - first 1/2/3/5-day path after executable entry
   - early adverse excursion and recovery

2. **Initial risk**
   - current 2 ATR stop behavior
   - realized loss distribution
   - compare descriptive risk distance with percentage loss, without tuning yet

3. **Profit development**
   - time-to-MFE
   - MFE at T+1/T+3/T+5/T+10/T+20 and later where data permits
   - first time reaching +5%, +10%, +20%, +25%

4. **Give-back / trend deterioration**
   - peak-to-exit give-back
   - EMA20 loss timing relative to MFE
   - pivot/base failure after initial progress

5. **45-day counterfactual**
   - among positions still structurally healthy at day 45, what happened afterward?
   - how many would have continued to new highs / additional MFE?
   - how many deteriorated soon after?
   - quantify opportunity cost and risk avoided by the forced exit.

6. **Exceptional-winner behavior**
   - identify unusually strong early advances observationally
   - test whether stronger early winners behave differently after the current 45-day boundary
   - do not define a production threshold from the same development sample.

## Governance conclusion

Current state:

- `2 ATR initial stop`: **TrendFoll-specific; requires evidence audit**.
- `close < EMA20`: **TrendFoll-specific trend-deterioration rule; requires evidence audit**.
- `45 trading-day maximum`: **not established as CAN SLIM-derived; formally challenged and must be tested as a counterfactual rather than assumed correct**.
- classic CAN SLIM `7%-8%` loss control, `20%-25%` profit zone, and eight-week exception: **reference behaviors, not automatic TrendFoll production rules**.
- IBD SwingTrader `2%-3%` loss / `5%-10%` profit / roughly 5-10-day trade horizon: **important evidence that O'Neil methodology is adapted to horizon, not a rule set to copy directly**.

No production exit rule changes are authorized by this document. The next step is DIAG-003 Exit Conversion / Give-back, after the PROB-018 feature-validity gate and position-identity integrity issue are sufficiently controlled.
