"""Load the trusted USSY ready dataset from the private Cloudflare R2 bucket.

Contract source: ussy-data production/ready/current.json -> immutable Parquet.
The loader validates schema version, key prefix, SHA-256, row count, and
security-id membership before exposing rows to TrendFoll.
"""
from __future__ import annotations

import hashlib
import io
import json
import os

import boto3
import pandas as pd

READY_POINTER = "production/ready/current.json"
READY_PREFIX = "production/ready/runs/"


def make_r2_client():
    required = ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing R2 credentials: {', '.join(missing)}")
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def load_ready_dataset(s3=None, bucket: str | None = None):
    s3 = s3 or make_r2_client()
    bucket = bucket or os.environ.get("R2_BUCKET_NAME", "ussy-data")

    manifest = json.loads(
        s3.get_object(Bucket=bucket, Key=READY_POINTER)["Body"].read()
    )
    key = manifest.get("parquet_key")
    if manifest.get("schema_version") != 1 or not isinstance(key, str) or not key.startswith(READY_PREFIX):
        raise ValueError("Invalid ready manifest")

    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if hashlib.sha256(body).hexdigest() != manifest.get("sha256"):
        raise ValueError("Ready Parquet checksum mismatch")

    frame = pd.read_parquet(io.BytesIO(body))
    expected = {"date", "security_id", "ticker", "open", "high", "low", "close", "adj_close", "volume"}
    missing = expected - set(frame.columns)
    if missing:
        raise ValueError(f"Ready dataset missing columns: {sorted(missing)}")

    if len(frame) != manifest.get("rows"):
        raise ValueError("Ready manifest/data row-count mismatch")
    if set(frame["security_id"].astype(str)) != set(manifest.get("security_ids", [])):
        raise ValueError("Ready manifest/data security-id mismatch")

    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    if frame.duplicated(["security_id", "date"]).any():
        raise ValueError("Duplicate security/date rows in ready dataset")

    return frame.sort_values(["security_id", "date"]).reset_index(drop=True), manifest


def to_feature_contract(frame: pd.DataFrame) -> pd.DataFrame:
    """Map ussy-data ready schema into the legacy TrendFoll feature contract."""
    out = frame.rename(columns={
        "ticker": "symbol",
        "open": "open_raw",
        "high": "high_raw",
        "low": "low_raw",
        "close": "close_raw",
        "adj_close": "close_adj",
        "volume": "volume_raw",
    }).copy()
    out["dividends"] = 0.0
    out["stock_splits"] = 0.0
    cols = [
        "date", "symbol", "open_raw", "high_raw", "low_raw", "close_raw",
        "close_adj", "volume_raw", "dividends", "stock_splits",
    ]
    return out[cols].sort_values(["symbol", "date"]).reset_index(drop=True)
