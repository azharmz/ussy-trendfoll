# Evidence — PROB-019 Research History / Pre-roll Architecture Gate

Status: **ARCHITECTURE CONTRACT RESOLVED; OFFICIAL-TOLERANCE RE-AUDIT BLOCKED ON CCTG EMA LINEAGE**

Date locked: 2026-09-15 (Asia/Makassar)

This evidence closes the architecture question in PROB-019. It does not change or validate any trading threshold, entry rule, exit rule, or profitability claim.

## Frozen contract

- Current R2 readiness remains the universe authority.
- Canonical stock history is read-only from `history/ohlcv/{security_id}.parquet`.
- Features use full preceding history with 500-bar pre-roll; only `research_eligible` rows enter evaluation.
- Canonical EMA basis is `adj_close`; official equivalence is `np.isclose(rtol=1e-8, atol=1e-8)`.
- Strict absolute deltas above `1e-10` are diagnostic only.
- No production pointers, EMA objects, signal rules, or thresholds may be changed as part of this audit.

## Latest official-tolerance re-audit — 2026-10-16

Workflow run [38826554447](https://github.com/azharmz/ussy-trendfoll/actions/runs/38826554447), run #16, on commit `4c77714134a8c6db260da5b109b7213f2949053c`.

- Repository tests: **PASS**.
- Audit result: **BLOCKED** — `CANONICAL_EMA_EQUIVALENCE_FAILURE`.
- Ready snapshot: `2026-08-28`; comparison as-of: `2026-10-14`.
- Deterministic sample: **100 securities**; canonical history loaded: **100/100**; total history rows: **522,487**.
- READY/history overlap: **29,976 rows**, **0 source mismatches**.
- Shared EMA rows and dates: **100/100**, **0 date mismatches**.
- Latest Stage: **0 mismatches**; adjusted-price failures: **0**.
- Governed-tolerance EMA failures: **4**, all attributable to **CCTG (KYG1993R1184)** — one each for EMA20, EMA50, EMA150, EMA200.
- Maximum absolute errors: EMA20 `7.6809e-6`, EMA50 `8.2704e-6`, EMA150 `4.2801e-6`, EMA200 `3.3916e-6`.
- The scalar recursive reference reproduces the same failure. The strict `1e-10` counts remain diagnostic and do not independently determine the gate.

Artifact: [prob-019-research-history-16](https://github.com/azharmz/ussy-trendfoll/actions/runs/38826554447/artifacts/12014604046), artifact ID `12014604046`, SHA256 `53a1dd40c9f0575c7c3613c31992b58123f24864eae52ac6753989e5fbfdae48`.

## CCTG interpretation and next safe step

Prior read-only lineage evidence found that the current canonical CCTG history does not reproduce previously approved persisted EMA checkpoints, including the 2026-09-24 full-history rebuild checkpoint. A source-row comparison also found that the current 2026-09-22 CCTG row differs from the frozen Stooq recovery row and immutable READY snapshot. The likely mechanism is an overlapping Yahoo download replacing a repaired historical row during the normal OHLCV merge, but event-level attribution to a specific write remains a high-confidence hypothesis, not proven.

The discrepancy is proven; its complete root cause is not. Do not loosen EMA tolerance, patch only CCTG's persisted EMA, rebuild the production pointer, or modify production R2 from this audit. The next repair belongs in the upstream `ussy-data` ingestion contract: protect existing historical rows from silent provider overwrite, and ensure an explicitly reviewed history revision generates rebuild hints for every affected security. Prepare and validate that change in an isolated path, with downstream dispatch disabled, before any production action.

## Governance and current disposition

The temporary branch-specific push trigger was used for one intentional run and is now being removed. The workflow returns to manual-only `workflow_dispatch`; no further compute should be triggered by ordinary commits. The audit was read-only against R2 and did not modify production state.

**PROB-019 remains OPEN.** Closure requires an official-tolerance 100-security audit with zero EMA failures, after the lineage/ingestion discrepancy is resolved and validated.