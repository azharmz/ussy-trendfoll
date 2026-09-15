import hashlib
import unittest
import pandas as pd
import run_exit_candidate003_validation as v


class ExitCandidate003ValidationTests(unittest.TestCase):
    def test_rank_slice_is_101_200_and_zero_overlap(self):
        ready=pd.DataFrame({"security_id":[f"id{i:03d}" for i in range(1,221)],"ticker":[f"T{i:03d}" for i in range(1,221)]})
        dev,val,p=v.ranked_ids(ready)
        expected=p.iloc[100:200].security_id.tolist()
        self.assertEqual(val,expected)
        self.assertEqual(len(dev),100)
        self.assertEqual(len(val),100)
        self.assertFalse(set(dev)&set(val))

    def test_rank_hash_contract(self):
        ready=pd.DataFrame({"security_id":[f"id{i:03d}" for i in range(1,201)],"ticker":[f"T{i:03d}" for i in range(1,201)]})
        _,_,p=v.ranked_ids(ready)
        first=p.iloc[0]
        self.assertEqual(first.rank_hash,hashlib.sha256(f"{first.security_id}|{first.ticker}".encode()).hexdigest())

    def test_requires_200_securities(self):
        ready=pd.DataFrame({"security_id":[f"id{i}" for i in range(199)],"ticker":[f"T{i}" for i in range(199)]})
        with self.assertRaises(RuntimeError): v.ranked_ids(ready)


if __name__=="__main__": unittest.main()
