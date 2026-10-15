"""Read-only CCTG history/EMA lineage diagnostic for PROB-019."""
from __future__ import annotations

import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

import numpy as np
import pandas as pd

from r2_ready import make_r2_client
from shared_ema_state import load_shared_ema_state

SECURITY_ID = "KYG1993R1184"
TICKER = "CCTG"
HISTORY_KEY = "history/ohlcv/" + SECURITY_ID + ".parquet"
MANIFEST_PREFIX = "history/manifests/bootstrap/"


def extract_matches(payload: dict, manifest_key: str) -> list[dict]:
    """Extract only CCTG records from one bootstrap manifest."""
    matches = []
    for result in payload.get("results", []):
        if str(result.get("security_id", "")) == SECURITY_ID or str(result.get("ticker", "")) == TICKER:
            matches.append({
                "manifest_key": manifest_key,
                "created_at": payload.get("created_at"),
                "snapshot_date": payload.get("snapshot_date"),
                "force": payload.get("force"),
                "status": result.get("status"),
                "rows": result.get("rows"),
                "first_date": result.get("first_date"),
                "last_date": result.get("last_date"),
                "object_key": result.get("object_key"),
                "error": result.get("error"),
            })
    return matches


def list_manifest_keys(s3, bucket: str) -> list[str]:
    keys = []
    token = None
    while True:
        args = {"Bucket": bucket, "Prefix": MANIFEST_PREFIX, "MaxKeys": 1000}
        if token:
            args["ContinuationToken"] = token
        page = s3.list_objects_v2(**args)
        keys.extend(item["Key"] for item in page.get("Contents", []) if item["Key"].endswith(".json"))
        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")
    return sorted(keys)


def read_manifest_match(s3, bucket: str, key: str) -> list[dict]:
    response = s3.get_object(Bucket=bucket, Key=key)
    payload = json.loads(response["Body"].read())
    return extract_matches(payload, key)


def main() -> None:
    bucket = os.environ["R2_BUCKET_NAME"]
    s3 = make_r2_client()

    pointer_response = s3.get_object(Bucket=bucket, Key="production/indicators/ema/current.json")
    pointer = json.loads(pointer_response["Body"].read())
    shared, shared_manifest = load_shared_ema_state(s3=s3, bucket=bucket)
    shared_row = shared.loc[shared["security_id"].astype(str) == SECURITY_ID]
    if len(shared_row) != 1:
        raise RuntimeError("Expected exactly one CCTG row in shared EMA state")
    shared_row = shared_row.iloc[0]

    history_response = s3.get_object(Bucket=bucket, Key=HISTORY_KEY)
    history_bytes = history_response["Body"].read()
    history = pd.read_parquet(BytesIO(history_bytes), engine="pyarrow")
    history["date"] = pd.to_datetime(history["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    cutoff = pd.Timestamp(shared_row["as_of_date"]).tz_localize(None).normalize()
    through_cutoff = history.loc[history["date"] <= cutoff].sort_values("date")
    prices = through_cutoff["adj_close"].astype(float).tolist()
    if len(prices) < 200:
        raise RuntimeError("CCTG canonical history has fewer than 200 bars through shared EMA cutoff")
    values = {period: prices[0] for period in (20, 50, 150, 200)}
    for price in prices[1:]:
        for period in values:
            alpha = 2.0 / (period + 1.0)
            values[period] = alpha * price + (1.0 - alpha) * values[period]
    ema_comparison = {}
    for period, value in values.items():
        persisted = float(shared_row["ema" + str(period)])
        error = abs(value - persisted)
        ema_comparison["ema" + str(period)] = {
            "current_history_value": value,
            "persisted_shared_value": persisted,
            "absolute_error": error,
            "passes_official_tolerance": bool(np.isclose(value, persisted, rtol=1e-8, atol=1e-8)),
        }

    # Compare the current canonical object with the legacy object referenced by the only
    # CCTG bootstrap manifest. This is read-only and can establish whether overlapping
    # adjusted-close history changed between the two stored representations.
    legacy_key = "backtest/ohlcv/" + SECURITY_ID + ".parquet"
    legacy_comparison = {"object_key": legacy_key, "available": False}
    try:
        legacy_response = s3.get_object(Bucket=bucket, Key=legacy_key)
        legacy_bytes = legacy_response["Body"].read()
        legacy = pd.read_parquet(BytesIO(legacy_bytes), engine="pyarrow")
        legacy["date"] = pd.to_datetime(legacy["date"], errors="raise").dt.tz_localize(None).dt.normalize()
        overlap = history.merge(
            legacy[["date", "close", "adj_close"]],
            on="date",
            how="inner",
            suffixes=("_current", "_legacy"),
            validate="one_to_one",
        )
        price_diff_report = {}
        for column in ("close", "adj_close"):
            diff = (overlap[column + "_current"].astype(float) - overlap[column + "_legacy"].astype(float)).abs()
            price_diff_report[column] = {
                "mismatches_over_1e-10": int((diff > 1e-10).sum()),
                "max_absolute_difference": float(diff.max()) if len(diff) else None,
            }
        changed = overlap.loc[
            (overlap["close_current"].astype(float) - overlap["close_legacy"].astype(float)).abs().gt(1e-10)
            | (overlap["adj_close_current"].astype(float) - overlap["adj_close_legacy"].astype(float)).abs().gt(1e-10),
            ["date", "close_current", "close_legacy", "adj_close_current", "adj_close_legacy"],
        ].head(20)
        legacy_comparison = {
            "object_key": legacy_key,
            "available": True,
            "last_modified": legacy_response.get("LastModified").isoformat() if legacy_response.get("LastModified") else None,
            "etag": legacy_response.get("ETag"),
            "sha256_current_legacy_object": hashlib.sha256(legacy_bytes).hexdigest(),
            "rows": int(len(legacy)),
            "first_date": str(legacy["date"].min().date()),
            "last_date": str(legacy["date"].max().date()),
            "overlap_rows": int(len(overlap)),
            "price_comparison": price_diff_report,
            "changed_overlap_rows_sample": [
                {
                    "date": str(pd.Timestamp(row["date"]).date()),
                    "close_current": float(row["close_current"]),
                    "close_legacy": float(row["close_legacy"]),
                    "adj_close_current": float(row["adj_close_current"]),
                    "adj_close_legacy": float(row["adj_close_legacy"]),
                }
                for _, row in changed.iterrows()
            ],
        }
    except Exception as exc:
        legacy_comparison["read_error"] = str(exc)[:300]

    keys = list_manifest_keys(s3, bucket)
    matches = []
    errors = []
    print("Bootstrap manifest scan: {} JSON objects".format(len(keys)), flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(read_manifest_match, s3, bucket, key): key for key in keys}
        for done, future in enumerate(as_completed(futures), start=1):
            key = futures[future]
            try:
                matches.extend(future.result())
            except Exception as exc:
                errors.append({"manifest_key": key, "error": str(exc)[:250]})
            if done == len(futures) or done % 100 == 0:
                print("Bootstrap manifest progress: {}/{}".format(done, len(futures)), flush=True)

    force_uploads = [
        item for item in matches
        if item.get("force") is True and item.get("status") == "uploaded"
    ]
    head = {
        "last_modified": history_response.get("LastModified").isoformat() if history_response.get("LastModified") else None,
        "etag": history_response.get("ETag"),
        "version_id": history_response.get("VersionId"),
        "content_length": history_response.get("ContentLength"),
        "sha256_current_object": hashlib.sha256(history_bytes).hexdigest(),
    }
    report = {
        "status": "PASS" if not errors else "PARTIAL",
        "mode": "READ_ONLY",
        "security_id": SECURITY_ID,
        "ticker": TICKER,
        "current_history_object": head,
        "current_history_rows": int(len(history)),
        "legacy_history_comparison": legacy_comparison,
        "current_history_first_date": str(history["date"].min().date()),
        "current_history_last_date": str(history["date"].max().date()),
        "shared_ema_pointer": {
            key: pointer.get(key) for key in (
                "created_at", "parquet_key", "sha256", "source_ready_parquet_key",
                "source_ready_sha256", "update_method", "source_ready_as_of_date",
                "as_of_date_max", "bootstrap_count", "rebuild_count",
                "bootstrap_security_ids", "rebuild_security_ids", "forced_rebuild_security_ids",
            )
        },
        "shared_ema_manifest_created_at": shared_manifest.get("created_at"),
        "shared_ema_as_of_date": str(cutoff.date()),
        "bars_through_shared_cutoff": int(len(through_cutoff)),
        "ema_comparison_current_history_vs_persisted": ema_comparison,
        "bootstrap_manifest_prefix": MANIFEST_PREFIX,
        "bootstrap_manifest_count": len(keys),
        "cctg_manifest_record_count": len(matches),
        "cctg_manifest_records": matches,
        "cctg_force_upload_count": len(force_uploads),
        "cctg_force_uploads": force_uploads,
        "manifest_read_errors_count": len(errors),
        "manifest_read_errors_sample": errors[:20],
        "production_writes": 0,
    }
    print(json.dumps(report, indent=2, default=str), flush=True)
    with open("prob019_cctg_lineage_audit.json", "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, default=str)


if __name__ == "__main__":
    main()
