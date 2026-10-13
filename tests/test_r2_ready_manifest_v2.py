"""Contract tests for the canonical ussy-data READY manifest."""
import hashlib
import io
import json
import unittest

import pandas as pd

from r2_ready import READY_POINTER, load_ready_dataset


class FakeS3:
    def __init__(self, objects):
        self.objects = objects

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


class ReadyManifestV2Tests(unittest.TestCase):
    def setUp(self):
        frame = pd.DataFrame([{
            "date": pd.Timestamp("2026-09-16"),
            "security_id": "sid-1",
            "ticker": "ABC",
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "adj_close": 10.5,
            "volume": 1000,
        }])
        parquet = io.BytesIO()
        frame.to_parquet(parquet, index=False, engine="pyarrow")
        body = parquet.getvalue()
        self.manifest = {
            "schema_version": 2,
            "snapshot_date": "2026-09-16",
            "as_of_date": "2026-09-16",
            "parquet_key": "production/ready/runs/2026-09-16.parquet",
            "sha256": hashlib.sha256(body).hexdigest(),
            "rows": 1,
            "security_ids": ["sid-1"],
        }
        self.s3 = FakeS3({
            READY_POINTER: json.dumps(self.manifest).encode(),
            self.manifest["parquet_key"]: body,
        })

    def test_accepts_canonical_schema_v2(self):
        frame, manifest = load_ready_dataset(s3=self.s3, bucket="test")
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.loc[0, "ticker"], "ABC")

    def test_rejects_legacy_schema_v1(self):
        self.manifest["schema_version"] = 1
        self.s3.objects[READY_POINTER] = json.dumps(self.manifest).encode()
        with self.assertRaisesRegex(ValueError, "Invalid ready manifest"):
            load_ready_dataset(s3=self.s3, bucket="test")


if __name__ == "__main__":
    unittest.main()
