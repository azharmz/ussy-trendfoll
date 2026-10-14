# Evidence — PROB-019 Research History / Pre-roll Architecture Gate

Status: **HISTORICAL GATE RESOLVED; 2026-10-14 CANONICAL-PREFIX RE-AUDIT BLOCKED ON EMA PARITY**

Date locked: 2026-09-15 (Asia/Makassar)

This evidence closes the architecture question in PROB-019. It does not change or validate any trading threshold, entry rule, exit rule, or profitability claim.

## Problem

The rolling ~300-bar R2 readiness window is appropriate for production scanning, but it is not a valid initialization history for historical EMA150/EMA200 and weekly Stage across an evaluation window. Historical diagnostics therefore require preceding feature context (pre-roll) that is excluded from evaluated observations.

## Frozen contract

Implemented in `research_history.py` and documented in `docs/RESEARCH_HISTORY_CONTRACT.md`:

`R2 current readiness universe -> R2 full stock history -> pre-roll feature initialization -> research_eligible rows -> signal/outcome study`

Frozen architecture rules:

- current R2 readiness remains universe authority;
- current canonical stock-history namespace is `history/ohlcv/{security_id}.parquet` in `ussy-data` (aligned on 2026-10-14);
- stock history is trimmed to `evaluation_end` before feature computation;
- default minimum pre-roll is 500 prior daily bars per security;
- 500 bars is an engineering warm-up, not a trading parameter and must not be performance-tuned;
- features are computed on preceding full history first;
- only `research_eligible == True` rows may enter signal/outcome evaluation;
- canonical historical EMA uses `adj_close`, matching the production shared EMA contract;
- Stage2 remains the existing raw-close weekly 30-week-SMA implementation;
- historical earnings lookup is disabled in this research adapter because it is not point-in-time safe and is not part of the frozen hard-filter path;
- all other signal/Investability/Tradability/entry/exit thresholds remain unchanged.

## Validation provenance

Workflow: `PROB-019 research history contract`

Successful run:

- run ID: `34905314921`
- job ID: `104180499914`
- branch head: `95a09997509cdd4aea9520a7da42931f875362da`
- conclusion: `SUCCESS`
- repository tests: **12/12 PASS**
- evidence artifact: `prob-019-research-history-2`
- artifact ID: `10372198703`
- artifact ZIP SHA256: `d7ccf8b7c61b05938c006a5a9c72e985a83be054c85f739121732aa57641b9b4`

The first audit run (`34905140346`) failed before evidence evaluation because Pandas 3 rejected a benchmark merge between `datetime64[ns]` and `datetime64[s]`. The research adapter was corrected to normalize auxiliary benchmark dates to `datetime64[ns]`, matching the existing production R2 adapter. No formula or threshold changed.

## Audit design

- universe authority: current R2 readiness;
- deterministic sample: SHA256-ranked `security_id|ticker`;
- sample: 100 securities;
- stock feature context at the original 2026-09-15 audit: R2 `backtest/ohlcv/{security_id}.parquet` full history (historical provenance; superseded namespace);
- minimum pre-roll: 500 daily bars;
- evaluation window in this audit: 2025-07-03 through 2026-09-14;
- source compatibility guard: 0.25% for overlapping `close` and `adj_close` values;
- canonical EMA comparison: research full-history `EMA(adj_close)` vs governed production shared EMA state;
- Stage comparison: latest Stage from full-history context vs latest Stage from rolling readiness context.

## Results

### History coverage

- requested securities: **100**
- loaded securities: **100**
- full-history rows: **520,282**
- research-eligible rows: **25,064**
- research-eligible securities: **87**

The 13 sampled securities without eligible rows are not treated as missing-data failures. Under the frozen contract, a security remains non-eligible until it has more than 500 of its own prior daily observations before/inside the evaluation horizon.

### Source compatibility

- exact security/date overlap rows: **29,930**
- source-compatible rows: **29,930**
- source mismatches: **0**

This establishes that the governed full-history R2 objects are compatible with the current ready data over the audited overlap, rather than introducing a separate stock-data vendor path inside TrendFoll.

### Canonical EMA equivalence

Shared production state compared: **100 / 100 securities**.

- missing shared rows: **0**
- as-of-date mismatches: **0**
- numeric failures: **0**
- EMA-stack mismatches: **0**
- max absolute error EMA20: **0.0**
- max absolute error EMA50: **0.0**
- max absolute error EMA150: **0.0**
- max absolute error EMA200: **0.0**

Thus the historical research path exactly reproduces the governed production canonical EMA state at the audited latest dates when fed the same full-history R2 source.

### Weekly Stage

- comparable latest symbols: **100**
- Stage mismatches: **0**

So introducing governed full-history pre-roll does not create a latest Stage classification divergence in the audited sample.

## No-look-ahead boundary

The implementation trims each security's stock history to `evaluation_end` **before** feature computation. Signals and outcomes may then use only rows marked `research_eligible` after the complete preceding feature state has been built.

Filtering stock history to the evaluation window before computing EMA/Stage is explicitly prohibited by the contract.

## Universe / survivorship boundary

This architecture preserves the current project mandate that **current R2 readiness is the universe authority**. It does not reconstruct point-in-time historical membership.

Therefore historical results produced under this contract must not be described as survivorship-bias-free. A future point-in-time universe project would be a separate governance workstream and is not required to resolve PROB-019 as currently defined.

## Snapshot metadata note

The audited ready manifest reported `snapshot_date = 2026-08-28`, while the sampled data/evaluation horizon contained bars through 2026-09-14. The source-overlap audit and the governed shared EMA state were internally date-consistent, so this did not invalidate the research-history architecture gate. The distinction is retained as provenance rather than silently interpreting the manifest field as the maximum bar date.

## Verdict

**PROB-019 = RESOLVED ARCHITECTURE GATE.**

New historical TrendFoll diagnostics and development backtests may proceed only through this governed research-history contract (or an explicitly equivalent governed successor). Existing frozen evidence is not rewritten retroactively; any rerun under the new contract is a new evidence cycle/version.

## Canonical R2 prefix reconciliation — 2026-10-14

The current `ussy-data` full-history contract uses the canonical object key
`history/ohlcv/{security_id}.parquet`, not the legacy `backtest/ohlcv/`
prefix. TrendFoll's current `research_history.py::HISTORY_PREFIX`,
`ResearchHistoryReport.stock_history_source`, fixture key, and the
`RESEARCH_HISTORY_CONTRACT.md` / `DIAG_003_EXIT_RISK_CONTRACT.md` references
were aligned to `history/ohlcv/` in commit
`afe38c60e5e54d9a93175dfd3e2c783e7eb7315f`.

Validation:
- Repository-wide pytest run: [run 38558808568](https://github.com/azharmz/ussy-trendfoll/actions/runs/38558808568)
- Tested code base: main commit `afe38c60e5e54d9a93175dfd3e2c783e7eb7315f`
- Result: **104 passed, 4 warnings**.
- The test run verifies repository regressions and the updated path fixture. The live R2 architecture audit was subsequently rerun on the canonical prefix (run 38560571911) and is **BLOCKED** on exact canonical EMA parity; see the next section. The original 2026-09-15 audit metrics above remain historical evidence from the old prefix and must not be represented as a fresh audit of the new namespace.

The namespace reconciliation changes object-key selection only. It does not change pre-roll length, feature formulas, evaluation bounds, EMA basis, Stage semantics, signal/exit rules, or any trading thresholds.

### Canonical-prefix re-audit — 2026-10-14 — BLOCKED

Workflow run [38560571911](https://github.com/azharmz/ussy-trendfoll/actions/runs/38560571911) ran the repository suite (**104 passed, 4 warnings**) and then read the current R2 history and shared EMA state for the deterministic 100-security sample. It did not write production data.

Observed:
- Canonical source prefix: `history/ohlcv/`; 100/100 requested securities loaded.
- Full-history rows: 522,387; research-eligible rows: 25,201 across 88 securities.
- READY/history overlap: 29,974 rows; exact `close` and `adj_close` mismatches at 1e-10: **0**; max absolute source difference: **0.0**.
- Shared EMA rows/date matches: 100/100; latest adjusted price mismatches: **0**.
- Exact EMA parity still fails: 301 period comparisons exceed 1e-10 (EMA20 76, EMA50 76, EMA150 76, EMA200 73); maximum absolute differences are approximately 8.61e-6.
- Trend-stack mismatches: **0**; latest Stage mismatches: **0**.
- A second comparison using the same scalar recurrence as `ussy-data/src/ema_state.py` produced the same EMA differences, so this is not explained solely by pandas EWM implementation.

Interpretation boundary: current READY-overlap prices and latest prices are exact, but this does not establish equality of the entire pre-roll lineage used to build the persisted EMA state. The audit does **not** prove the root cause; stale/divergent historical state lineage remains a hypothesis requiring upstream evidence. Do not loosen the 1e-10 gate or alter feature/strategy semantics to force PASS.

Next action: inspect the upstream shared-EMA manifest and rebuild lineage, then compare its recorded source history/version with the current `history/ohlcv/` objects. Any production EMA rebuild must follow `ussy-governance` and the `ussy-data` production workflow contract; this audit made no production writes.
