# EXIT-ISO-001 — Exit Component Attribution Evidence

Status: **EVIDENCE-LOCKED / COMPONENT ATTRIBUTION ONLY / NO PRODUCTION CHANGE**

## Purpose

Isolate the contribution of the existing TrendFoll exit components without introducing or tuning any new parameter.

Frozen comparable variants:

- `CURRENT`: fixed 2 ATR initial stop + EMA20 trend exit + 45-trading-day maximum.
- `NO_STOP`: EMA20 trend exit + 45-day maximum; fixed stop ignored.
- `NO_EMA20`: fixed 2 ATR stop + 45-day maximum; EMA20 exit ignored.
- `DAY45_ONLY`: 45-day close only; stop and EMA20 ignored.

No ATR multiplier grid, EMA-period grid, holding-period grid, profit-target grid, or outcome-driven threshold selection was performed.

## Governed run

- Workflow: `EXIT-ISO-001 Component Isolation`
- Run: `34929214224` (run #2)
- Head commit: `ea7c3df121ec1f8712716d7728989517f41cbb9c`
- Result: **SUCCESS**
- Repository tests: **12/12 PASS**
- Artifact: `exit-iso001-2`
- Artifact ID: `10380648800`
- Artifact ZIP SHA256: `48c07ccf3b5d00d0147c4509ae651f17a315598c4096140ae087fc297243944e`
- R2 readiness snapshot: `2026-08-28`
- deterministic sample: 100 securities
- eligible onsets: 1,545
- exact 45-bar comparable events: 1,524

Run #1 is superseded for reporting because its `delta_vs_current_median` label was ambiguous: it represented the median paired event delta, not the difference between aggregate medians. Run #2 changes no exit semantics or outcomes; it explicitly reports both estimands.

## Results

| Variant | Median return | Positive | Q25 | Q75 | Median hold | Median MFE | Median MAE | Aggregate median difference vs CURRENT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CURRENT | -3.465% | 33.01% | -5.189% | +3.623% | 16 | +5.515% | -4.734% | 0.000 pp |
| NO_STOP | -0.346% | 48.62% | -6.247% | +6.971% | 45 | +7.645% | -6.225% | +3.118 pp |
| NO_EMA20 | -3.978% | 31.63% | -5.702% | +4.786% | 20 | +5.737% | -5.199% | -0.513 pp |
| DAY45_ONLY | +1.699% | 56.43% | -6.669% | +10.167% | 45 | +9.090% | -7.860% | +5.164 pp |

Exit reasons:

- CURRENT: stop 839, EMA20 trend exit 348, day45 337.
- NO_STOP: EMA20 trend exit 683, day45 841.
- NO_EMA20: stop 1,004, day45 520.
- DAY45_ONLY: day45 1,524.

Paired-event comparison versus CURRENT:

- NO_STOP: 27.03% improved, 28.02% worsened, 44.95% unchanged; paired median delta = 0 because nearly 45% of events are identical.
- NO_EMA20: 8.33% improved, 14.50% worsened, 77.17% unchanged; paired median delta = 0.
- DAY45_ONLY: 43.44% improved, 34.45% worsened, 22.11% unchanged; paired median delta = 0.

## Attribution

### Fixed 2 ATR stop is the dominant conversion mechanism

Removing only the fixed stop changes the aggregate median from -3.465% to -0.346% and the positive rate from 33.01% to 48.62%. It also increases adverse excursion (median MAE from -4.734% to -6.225%). Therefore the current fixed stop is strongly implicated in conversion loss, but simply deleting it is **not authorized** because the counterfactual accepts materially more path risk.

### EMA20 is not the primary harmful component

Removing only EMA20 while retaining the fixed stop slightly worsens the aggregate median to -3.978% and positive rate to 31.63%. Most events (77.17%) are unchanged. Thus the evidence does not support treating EMA20 as the principal source of the conversion problem.

### DAY45_ONLY is a diagnostic upper-path counterfactual, not a candidate rule

Holding every comparable event to day 45 produces +1.699% median and 56.43% positive outcomes, but median MAE expands to -7.860%. This confirms that the event corpus contains later opportunity that the current stack often fails to realize. It does not establish that removing risk controls is acceptable or that 45 days is an optimal holding period.

## Governance verdict

`RC-004 EXIT/RISK CONVERSION = SUPPORTED MATERIAL ROOT CAUSE`

Component attribution is now sharper:

`CURRENT FIXED 2 ATR STOP = PRIMARY IMPLICATED COMPONENT`

`EMA20 TREND EXIT = NOT PRIMARY HARMFUL COMPONENT IN THIS ISOLATION`

This evidence authorizes **development of a risk-preserving replacement representation**, not production modification. The next candidate-development work must preserve an explicit initial-risk function while avoiding an indefinitely fixed entry-anchored stop as the only risk-management mechanism.

No production change is authorized by EXIT-ISO-001.
