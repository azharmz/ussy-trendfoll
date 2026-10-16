import hashlib
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_research_history_contract_audit import deterministic_sample, sample_fingerprint


class Prob019SampleManifestTests(unittest.TestCase):
    def authority(self):
        return pd.DataFrame({
            "security_id": ["sec-c", "sec-a", "sec-b", "sec-a"],
            "ticker": ["CCC", "AAA", "BBB", "AAA"],
        }).drop_duplicates()

    def test_sample_is_deterministic_and_records_selection_hash(self):
        first = deterministic_sample(self.authority())
        second = deterministic_sample(self.authority().sample(frac=1, random_state=17))
        self.assertEqual(first[["security_id", "ticker"]].values.tolist(),
                         second[["security_id", "ticker"]].values.tolist())
        self.assertEqual(first["selection_hash"].tolist(), [
            hashlib.sha256(f"{r.security_id}|{r.ticker}".encode()).hexdigest()
            for r in first.itertuples()
        ])

    def test_fingerprint_tracks_ordered_membership(self):
        sample = deterministic_sample(self.authority())
        expected_rows = sample[["security_id", "ticker", "selection_hash"]].to_dict("records")
        expected = hashlib.sha256(
            json.dumps(expected_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
        self.assertEqual(sample_fingerprint(sample), expected)
        self.assertNotEqual(sample_fingerprint(sample), sample_fingerprint(sample.iloc[::-1].reset_index(drop=True)))


if __name__ == "__main__":
    unittest.main()
