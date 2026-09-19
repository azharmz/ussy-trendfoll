import hashlib
import json
import os
import unittest
from unittest.mock import patch

import verify_upstream_dispatch as v


class Body:
    def __init__(self, raw): self.raw = raw
    def read(self): return self.raw


class S3:
    def __init__(self, objects): self.objects = objects
    def get_object(self, Bucket, Key): return {"Body": Body(self.objects[Key])}


def raw(payload): return json.dumps(payload, sort_keys=True).encode()


class UpstreamDispatchContract(unittest.TestCase):
    def setUp(self):
        self.completion = {
            "schema_version": 1, "status": "FULLY_COMPLETE",
            "ready_as_of_date": "2026-09-18",
            "ready_parquet_key": "production/ready/runs/2026-09-18.parquet",
            "ready_sha256": "r"*64,
            "ema_parquet_key": "production/indicators/ema/runs/run-1-1.parquet",
            "ema_sha256": "e"*64,
            "ema_source_ready_parquet_key": "production/ready/runs/2026-09-18.parquet",
            "ema_source_ready_sha256": "r"*64,
        }
        self.craw = raw(self.completion)
        self.ckey = "production/completions/runs/2026-09-18-rrrr.json"
        self.objects = {
            self.ckey: self.craw,
            "production/completions/current.json": raw({
                **self.completion, "completion_key": self.ckey,
                "completion_sha256": hashlib.sha256(self.craw).hexdigest(),
            }),
            "production/ready/current.json": raw({
                "as_of_date": "2026-09-18",
                "parquet_key": self.completion["ready_parquet_key"],
                "sha256": self.completion["ready_sha256"],
            }),
            "production/indicators/ema/current.json": raw({
                "parquet_key": self.completion["ema_parquet_key"],
                "sha256": self.completion["ema_sha256"],
                "source_ready_parquet_key": self.completion["ready_parquet_key"],
                "source_ready_sha256": self.completion["ready_sha256"],
            }),
        }
        self.env = {
            "R2_BUCKET_NAME": "ussy-data",
            "UPSTREAM_COMPLETION_KEY": self.ckey,
            "UPSTREAM_COMPLETION_SHA256": hashlib.sha256(self.craw).hexdigest(),
            "UPSTREAM_READY_AS_OF_DATE": "2026-09-18",
            "UPSTREAM_READY_PARQUET_KEY": self.completion["ready_parquet_key"],
            "UPSTREAM_READY_SHA256": self.completion["ready_sha256"],
            "UPSTREAM_EMA_PARQUET_KEY": self.completion["ema_parquet_key"],
            "UPSTREAM_EMA_SHA256": self.completion["ema_sha256"],
        }

    def test_exact_identity_passes(self):
        with patch.dict(os.environ, self.env, clear=True), patch.object(v, "make_r2_client", return_value=S3(self.objects)):
            self.assertEqual("FULLY_COMPLETE", v.verify()["status"])

    def test_ready_mismatch_fails_closed(self):
        env = dict(self.env); env["UPSTREAM_READY_SHA256"] = "x"*64
        with patch.dict(os.environ, env, clear=True), patch.object(v, "make_r2_client", return_value=S3(self.objects)):
            with self.assertRaises(RuntimeError):
                v.verify()


if __name__ == "__main__":
    unittest.main()
