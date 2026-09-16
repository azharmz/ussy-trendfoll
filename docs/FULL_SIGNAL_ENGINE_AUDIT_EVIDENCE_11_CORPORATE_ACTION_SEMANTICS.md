# Full Signal Engine Audit — Evidence 11: Corporate-Action Semantics

Status: **EMPIRICAL AUDIT COMPLETE / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

Workflow: `Signal Engine Corporate-Action Semantics Audit`

Run: `35051771611`

Job: `104653495258`

Head: `7f71bb481c17c851beb8e6c1bae66fbc6aba0ca1`

Artifact: `corporate-action-semantics-1`

Artifact ID: `10428413999`

Artifact SHA-256: `cfbaaca29dd9623a695a9ad65322def4e5491ee7c608496b33c8de50e0a1435a`

## Population

Current R2 READY contains 367,499 rows. The Evidence-09 raw/adjusted-price diagnostic isolated 31 rows across 18 securities where `abs(pct_change(close / adj_close)) > 5%`.

Tickers: AD, BGSF, BIRD, BKE, BRLT, CPIX, DHT, ETD, FIZZ, HTCR, INSW, NLOP, RECT, SITC, SNY, TLK, VISN, VOC.

This ratio-change rule is a corporate-action-sensitive diagnostic proxy. It is not, by itself, evidence of bad market data.

## Empirical result

Across the 31 event rows:

- 30/31 have an absolute raw-vs-adjusted one-session return gap greater than 5%.
- 23/31 have an absolute raw-vs-adjusted 63-session return gap greater than 5%.
- Maximum observed one-session return gap: 53.19 percentage points.
- Maximum observed 63-session return gap: 62.55 percentage points.

Therefore raw and adjusted price bases are materially non-interchangeable around this event population.

## Signal-field interpretation

### Relative strength

The stock side of current 63-session RS uses `adj_close`. This is the appropriate internal basis for a return measure intended to avoid mechanical split/distribution discontinuities. The audit found no reason to replace it with raw close. D3.9 is closed at the stock-basis level.

SPY benchmark alignment/basis was separately audited under benchmark evidence; this evidence does not redefine the benchmark contract.

Classification: **MATCH / CORPORATE-ACTION-ADJUSTED RETURN BASIS**.

### Price floor

Current price-floor thresholds use raw close. That makes the rule a nominal tradable-price rule, intentionally sensitive to a split/reverse-split changing the nominal share price. This is coherent if the intended contract is literally a current nominal-price floor, not an economic-return measure.

Classification: **VALID USSY DEFINITION**, with the raw/nominal basis required in documentation.

### Liquidity

Current liquidity uses rolling mean of raw share volume. Share-count-changing corporate actions can mechanically change the scale of raw share volume, so pre/post-action observations inside one 50-session window are not guaranteed to be economically comparable. Evidence 11 establishes the exposure but does not establish a corrected volume basis or threshold.

Classification: **NEEDS CORRECTION SPEC / CORPORATE-ACTION-SENSITIVE WINDOW**.

D4.4 empirical behavior is closed; any formula correction remains governed and must be specified before code change.

## Audit disposition

- D3.9: closed empirically; adjusted-close stock return basis retained.
- D4.4: closed empirically; raw-volume corporate-action sensitivity confirmed and promoted to correction-governance work.
- D5.4: closed empirically; raw-close price floor is coherent as a nominal-price rule.
- K5 remains open until a governed liquidity correction, if adopted, has explicit corporate-action regression tests.

No production formula is changed by this evidence.
