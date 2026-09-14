"""Strict reader for the governed shared EMA state published by ussy-data."""
from __future__ import annotations

import hashlib
import io
import json
import os

import pandas as pd

from r2_ready import make_r2_client

EMA_POINTER = "production/indicators/ema/current.json"
EMA_PREFIX = "production/indicators/ema/runs/"
PROMOTION_POLICY = "candidate_then_equivalence_then_immutable_run_then_current_pointer_last_v1"
PERIODS = (20, 50, 150, 200)


def load_shared_ema_state(s3=None, bucket: str | None = None):
    s3 = s3 or make_r2_client()
    bucket = bucket or os.environ.get("R2_BUCKET_NAME", "ussy-data")
    manifest = json.loads(s3.get_object(Bucket=bucket, Key=EMA_POINTER)["Body"].read())

    key = manifest.get("parquet_key", "")
    eq = manifest.get("equivalence")
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported shared EMA schema")
    if list(manifest.get("periods", [])) != list(PERIODS):
        raise ValueError("Unexpected shared EMA periods")
    if not isinstance(key, str) or not key.startswith(EMA_PREFIX):
        raise ValueError("Invalid shared EMA immutable key")
    if manifest.get("promotion_policy") != PROMOTION_POLICY:
        raise ValueError("Shared EMA state lacks approved promotion policy")
    if not isinstance(eq, dict) or eq.get("numeric_failures") != 0 or eq.get("classification_mismatches") != 0:
        raise ValueError("Shared EMA equivalence evidence did not pass")

    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if hashlib.sha256(body).hexdigest() != manifest.get("sha256"):
        raise ValueError("Shared EMA parquet checksum mismatch")
    frame = pd.read_parquet(io.BytesIO(body))
    required = {"security_id", "ticker", "as_of_date", "last_price", *(f"ema{p}" for p in PERIODS)}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Shared EMA state missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["security_id"] = frame["security_id"].astype(str)
    frame["as_of_date"] = pd.to_datetime(frame["as_of_date"], errors="raise")
    if frame.empty or frame["security_id"].duplicated().any():
        raise ValueError("Shared EMA state empty or duplicate security_id")
    if len(frame) != manifest.get("securities"):
        raise ValueError("Shared EMA manifest/data security count mismatch")
    return frame.sort_values("security_id").reset_index(drop=True), manifest
