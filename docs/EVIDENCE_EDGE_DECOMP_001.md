# EDGE-DECOMP-001 — Development Evidence

Status: **DEVELOPMENT EVIDENCE LOCKED / NO PRODUCTION CHANGE**

Run: 35417415666  
Commit: 95efacfe72e9e140ba117ed11c26443a35d53ce1  
Artifact: edge-decomposition-3 (ID 10575644775)  
Artifact SHA256: 1c919d04cbf2b28490cc0e8758bb835258c9280211470c4d3364201789f0c3e5

## Corpus

- deterministic SHA256-ranked first 100 READY securities
- 87 securities had research-eligible history after 500-bar pre-roll
- canonical history: history/ohlcv/{security_id}.parquet
- canonical historical EMA basis: adj_close
- 519,288 history rows; 470,890 eligible rows
- 1,610 full-stream independent entry-ready onsets
- 1,545 eligible onsets
- current READY membership is not point-in-time historical membership; survivorship bias remains

## Result

Baseline across 1,545 onsets from executable T+1 Open:
- median T+5: +0.151%
- median T+10: +0.175%
- median MFE10: +3.692%
- median MAE10: -3.580%

T+1 **accepted** (T+1 close >= T0 rolling-60D pivot):
- n=1,217
- median T+5 from T+1 Open: +0.535%
- median T+10: +0.633%
- median MFE10: +4.040%
- median MAE10: -3.081%

T+1 **rejected** (T+1 close < pivot):
- n=328
- median T+5 from T+1 Open: -1.860%
- median T+10: -1.231%
- median MFE10: +2.279%
- median MAE10: -5.779%

T+1 retest-held:
- n=324
- median T+5 from T+1 Open: +0.202%
- median T+10: -0.157%

T+1 stayed-above:
- n=893
- median T+5 from T+1 Open: +0.629%
- median T+10: +0.832%
- median MFE10: +4.251%
- median MAE10: -2.958%

Any close below the T0 pivot occurred in 21.23% by T+1, 38.58% by T+3, 46.37% by T+5, and 58.14% by T+10.

## Causal observation

After T+1 information is actually known, T+2 Open is the earliest clean next-session anchor.

For the rejected group, median T+2 Open→T+5 was +0.250% and T+2 Open→T+10 +0.429%. Therefore the large negative T+1-Open path of rejected events is concentrated before the causal post-rejection T+2 anchor; this development evidence does **not** support pretending that T+1 rejection was knowable at T+1 Open.

For accepted events, T+2 Open→T+5 median was +0.170% and T+2 Open→T+10 +0.215%.

## Interpretation

Development evidence supports a specific structural hypothesis: the current unconditional T+1 Open baseline includes a materially weaker subset that closes T+1 back below the existing TrendFoll breakout reference. This is not explained by aggregate T0→T+1 gap alone.

This result does not authorize production change. The structural acceptance rule was frozen before this run and no fitted margin was searched.

## Next governed step

Freeze one candidate before untouched validation:

**EDGE-CAND-001 — post-breakout acceptance**
1. T0 current TrendFoll entry-ready onset.
2. Observe T+1 normally; no hypothetical T+1 fill for the candidate.
3. Candidate qualifies only if T+1 close >= the T0 prev_pivot_high.
4. Earliest candidate fill = T+2 Open.
5. No pivot margin, gap threshold, momentum threshold, retest requirement, or parameter fitting.
6. Compare on a deterministic untouched security holdout, not the first-100 development securities.

No production semantics change is authorized unless untouched validation is separately passed and governed.
