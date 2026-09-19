"""Fail-closed verification of an ussy-data cross-repo dispatch identity."""
from __future__ import annotations

import hashlib
import json
import os

from r2_ready import make_r2_client

COMPLETION_PREFIX = "production/completions/runs/"
READY_PREFIX = "production/ready/runs/"
EMA_PREFIX = "production/indicators/ema/runs/"
REQUIRED_ENV = (
    "UPSTREAM_COMPLETION_KEY",
    "UPSTREAM_COMPLETION_SHA256",
    "UPSTREAM_READY_AS_OF_DATE",
    "UPSTREAM_READY_PARQUET_KEY",
    "UPSTREAM_READY_SHA256",
    "UPSTREAM_EMA_PARQUET_KEY",
    "UPSTREAM_EMA_SHA256",
)


def _expected() -> dict:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Incomplete upstream dispatch identity: " + ", ".join(missing))
    return {name: os.environ[name] for name in REQUIRED_ENV}


def _read_json(s3, bucket: str, key: str) -> tuple[dict, bytes]:
    raw = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return json.loads(raw), raw


def verify() -> dict:
    expected = _expected()
    completion_key = expected["UPSTREAM_COMPLETION_KEY"]
    if not completion_key.startswith(COMPLETION_PREFIX):
        raise RuntimeError("Invalid upstream completion key prefix")
    if not expected["UPSTREAM_READY_PARQUET_KEY"].startswith(READY_PREFIX):
        raise RuntimeError("Invalid upstream READY key prefix")
    if not expected["UPSTREAM_EMA_PARQUET_KEY"].startswith(EMA_PREFIX):
        raise RuntimeError("Invalid upstream EMA key prefix")

    s3 = make_r2_client()
    bucket = os.environ.get("R2_BUCKET_NAME", "ussy-data")
    completion, raw = _read_json(s3, bucket, completion_key)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected["UPSTREAM_COMPLETION_SHA256"]:
        raise RuntimeError("Upstream completion document checksum mismatch")
    if completion.get("schema_version") != 1 or completion.get("status") != "FULLY_COMPLETE":
        raise RuntimeError("Upstream completion document is not authoritative FULLY_COMPLETE evidence")

    pairs = {
        "ready_as_of_date": expected["UPSTREAM_READY_AS_OF_DATE"],
        "ready_parquet_key": expected["UPSTREAM_READY_PARQUET_KEY"],
        "ready_sha256": expected["UPSTREAM_READY_SHA256"],
        "ema_parquet_key": expected["UPSTREAM_EMA_PARQUET_KEY"],
        "ema_sha256": expected["UPSTREAM_EMA_SHA256"],
    }
    for field, value in pairs.items():
        if completion.get(field) != value:
            raise RuntimeError(f"Dispatch/completion mismatch for {field}")

    if completion.get("ema_source_ready_parquet_key") != completion.get("ready_parquet_key"):
        raise RuntimeError("Completion EMA/READY key lineage mismatch")
    if completion.get("ema_source_ready_sha256") != completion.get("ready_sha256"):
        raise RuntimeError("Completion EMA/READY checksum lineage mismatch")

    current_completion, _ = _read_json(s3, bucket, "production/completions/current.json")
    if current_completion.get("completion_key") != completion_key:
        raise RuntimeError("Dispatched completion is no longer the current production completion")
    if current_completion.get("completion_sha256") != digest:
        raise RuntimeError("Current completion pointer checksum does not match dispatched completion")

    ready, _ = _read_json(s3, bucket, "production/ready/current.json")
    ema, _ = _read_json(s3, bucket, "production/indicators/ema/current.json")
    if (ready.get("as_of_date"), ready.get("parquet_key"), ready.get("sha256")) != (
        expected["UPSTREAM_READY_AS_OF_DATE"],
        expected["UPSTREAM_READY_PARQUET_KEY"],
        expected["UPSTREAM_READY_SHA256"],
    ):
        raise RuntimeError("Current READY pointer does not match dispatched production identity")
    if (ema.get("parquet_key"), ema.get("sha256")) != (
        expected["UPSTREAM_EMA_PARQUET_KEY"],
        expected["UPSTREAM_EMA_SHA256"],
    ):
        raise RuntimeError("Current EMA pointer does not match dispatched production identity")
    if (ema.get("source_ready_parquet_key"), ema.get("source_ready_sha256")) != (
        ready.get("parquet_key"), ready.get("sha256")
    ):
        raise RuntimeError("Current EMA pointer is not aligned with current READY")

    print(
        "[upstream dispatch] VERIFIED "
        f"as_of={expected['UPSTREAM_READY_AS_OF_DATE']} "
        f"ready={expected['UPSTREAM_READY_PARQUET_KEY']} "
        f"completion={completion_key}"
    )
    return completion


if __name__ == "__main__":
    verify()
