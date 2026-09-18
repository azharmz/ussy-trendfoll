# PROB-005 — R2 READY → TrendFoll identity boundary

Status: **CLOSED / EVIDENCE LOCKED**

## Mapping contract discovered

Production reads `production/ready/current.json`, verifies the immutable READY parquet checksum, schema, row count, manifest security-id membership and upstream `(security_id,date)` uniqueness. READY rows carry both `security_id` and `ticker`.

The TrendFoll adapter then maps:

`READY object row -> security_id -> ticker -> symbol -> normalized trading date -> (symbol,date)`.

Before PROB-005, `to_feature_contract()` renamed `ticker -> symbol` and intentionally omitted `security_id`. The feature engine then grouped by `symbol`. Consequently upstream `(security_id,date)` uniqueness alone was insufficient to prove downstream `(symbol,date)` uniqueness if two security IDs ever mapped to the same ticker.

Shared EMA already independently enforced one-to-one READY security_id/ticker mapping. Research history validates one ticker per requested security_id and later uses a one-to-one merge when restoring security lineage, but its authority mapping did not itself reject two security IDs sharing one ticker.

## Audit result

Current production contract evidence shows no known mapped `(symbol,date)` collision. The READY loader already rejects duplicate `(security_id,date)`; shared-EMA validation rejects duplicate ticker mapping and requires the security-id set and ticker mapping to match current READY. No historical collision was discovered in the governed TrendFoll evidence or existing validation paths.

This workstream did not mutate or enumerate R2 objects outside the canonical READY object because TrendFoll's available execution path has no direct R2 credentialed audit surface. Therefore the claim is intentionally scoped to the production-linked canonical READY/EMA contract and existing repository evidence, not a bucket-wide historical scan.

## Frozen loader identity contract

1. `security_id` is the stronger upstream security identity and must be retained through validation.
2. Current READY must map `security_id <-> ticker` one-to-one at the TrendFoll boundary.
3. Each downstream `(symbol,date)` must resolve to exactly one canonical upstream `(security_id,date)` observation.
4. Exact duplicates are not silently deduplicated: they fail closed.
5. Conflicting duplicates fail closed and diagnostics include symbol/date/security IDs and collision kind.
6. Mapping validation occurs before feature computation and before `security_id` is omitted from the legacy feature contract.
7. No first/last/drop_duplicates/groupby aggregation is an acceptable collision resolver.

## Downstream impact

Without the guard, duplicate symbol/date rows would enter per-symbol sorted timelines and could alter rolling EMA/ATR/Stage/RS/pivot/volume calculations, duplicate latest rows, and make T+1/exit lookup ambiguous. This is an engineering contamination path, not a trading-rule issue.

No frozen DIAG/CAND/Near-Trigger evidence is being recomputed or rewritten because no actual historical collision was established. The guard is preventive hardening.

## Ownership

No ussy-data patch was made. If the guard ever trips on canonical READY, TrendFoll must fail closed and hand the concrete security IDs/object lineage to ussy-data rather than resolve identity heuristically.
