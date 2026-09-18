import unittest
import pandas as pd
from r2_ready import validate_ready_identity_contract, to_feature_contract

def row(sid,ticker,date="2026-09-17",close=10.0):
    return {"security_id":sid,"ticker":ticker,"date":date,"open":9.0,"high":11.0,"low":8.0,"close":close,"adj_close":close,"volume":100}

class ReadyIdentityContractTests(unittest.TestCase):
    def test_unique_data_passes(self):
        f=pd.DataFrame([row("s1","AAA"),row("s1","AAA","2026-09-18"),row("s2","BBB")])
        report=validate_ready_identity_contract(f)
        self.assertEqual(report["collision_groups"],0)
        self.assertEqual(len(to_feature_contract(f)),3)

    def test_exact_duplicate_fails_closed(self):
        f=pd.DataFrame([row("s1","AAA"),row("s1","AAA")])
        with self.assertRaisesRegex(ValueError,"Duplicate canonical security/date"):
            validate_ready_identity_contract(f)

    def test_conflicting_duplicate_fails_closed(self):
        f=pd.DataFrame([row("s1","AAA"),row("s1","AAA",close=12.0)])
        with self.assertRaisesRegex(ValueError,"Duplicate canonical security/date"):
            validate_ready_identity_contract(f)

    def test_different_symbols_same_date_pass(self):
        validate_ready_identity_contract(pd.DataFrame([row("s1","AAA"),row("s2","BBB")]))

    def test_same_symbol_different_dates_pass(self):
        validate_ready_identity_contract(pd.DataFrame([row("s1","AAA"),row("s1","AAA","2026-09-18")]))

    def test_multiple_security_ids_same_symbol_fails_closed(self):
        f=pd.DataFrame([row("s1","AAA"),row("s2","AAA")])
        with self.assertRaisesRegex(ValueError,"ticker maps from multiple security_ids"):
            validate_ready_identity_contract(f)

if __name__=="__main__":
    unittest.main()
