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

The discrepancy is proven. A read-only counterfactual now shows that replacing only CCTG's 2026-09-22 adjusted-close in memory—from the current canonical value `0.5180000066757202` to the frozen recovery value `0.5184`—reproduces all four persisted EMA values exactly at the 2026-10-14 cutoff. This confirms that the row-value difference is sufficient to explain the EMA discrepancy. The historical write event that changed the canonical row remains unproven. Do not loosen EMA tolerance, rebuild the production pointer, or modify production R2 from this diagnostic. The upstream `ussy-data` overlap-protection fix is already merged on `main` in commit `2141f6180a2ac2a4730b1fe4277f8a6a2a4a59fb` and its isolated test workflow passed; that prevents recurrence but does not repair the existing CCTG history or persisted EMA. Any historical correction/rebuild still requires a separately governed repair plan with downstream dispatch disabled.

## Governance and current disposition

The temporary branch-specific push trigger was used for one intentional run and is now being removed. The workflow returns to manual-only `workflow_dispatch`; no further compute should be triggered by ordinary commits. The audit was read-only against R2 and did not modify production state.

**PROB-019 remains OPEN.** Closure requires an official-tolerance 100-security audit with zero EMA failures, after the lineage/ingestion discrepancy is resolved and validated.

## CCTG in-memory counterfactual — 2026-10-16

Read-only workflow [38827227580](https://github.com/azharmz/ussy-trendfoll/actions/runs/38827227580) passed **107 repository tests** and completed the counterfactual diagnostic. Artifact: [prob-019-research-history-18](https://github.com/azharmz/ussy-trendfoll/actions/runs/38827227580/artifacts/12014429767), artifact ID `12014429767`, ZIP SHA256 `ae3d43cc38ae3f0a5d48713b8c12257a1fb1917254fd1f750c22c7126fc4467`.

The script read, without writing:
- current canonical history `history/ohlcv/KYG1993R1184.parquet`, SHA256 `114607d8182240df68954f8eff761046745dcfd3426e39104090033f0e19d842`;
- frozen recovery history `recovery/stooq-2026-09-25/history/ohlcv/KYG1993R1184.parquet`, SHA256 `049dc36a0341fc43229b30229f92d6947d8d308f4bc626c039a22dc2a53e91c9`;
- current shared EMA state, as-of `2026-10-14`.

Current-history EMA absolute errors versus shared state were EMA20 `7.6809041154e-6`, EMA50 `8.2704097277e-6`, EMA150 `4.2801099882e-6`, EMA200 `3.3915559445e-6`; all four failed the official tolerance. After replacing only the 2026-09-22 adjusted-close **in memory**, all four EMA values matched the shared state exactly (absolute error `0.0` for each; official-tolerance PASS). No R2 object, pointer, READY snapshot, or production state was modified.

This isolates the numerical cause to the CCTG adjusted-close value on 2026-09-22. It does **not** establish which production write introduced the changed value, and it is not authorization to overwrite canonical history or rebuild the shared EMA pointer. **PROB-019 remains OPEN** pending a governed historical repair/rebuild decision and a fresh 100-security official-tolerance audit with zero failures.
