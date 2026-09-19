import unittest
import pandas as pd
from edge_decomposition import build_edge_events, summarize

class EdgeDecompositionTests(unittest.TestCase):
    def frame(self,t1close=11.0,t1low=9.8):
        rows=[]; closes=[9.5,10.5,t1close,11.2,11.3,11.4,11.5,11.6,11.7,11.8,11.9,12.0]
        for i,c in enumerate(closes):
            rows.append({"symbol":"X","date":pd.Timestamp("2020-01-01")+pd.Timedelta(days=i),
                         "open_raw":c,"high_raw":c+0.2,"low_raw":t1low if i==2 else c-0.2,"close_raw":c,
                         "hard_filter_status":"PASS" if i>=1 else "FAIL","has_breakout":i>=1,
                         "has_volume_confirmation":i>=1,"prev_pivot_high":10.0,"atr14":1.0})
        return pd.DataFrame(rows)
    def test_acceptance_and_causal_t2(self):
        e=build_edge_events(self.frame()).iloc[0]
        self.assertTrue(e["t1_accepted"]); self.assertTrue(e["t1_retest_held"]); self.assertAlmostEqual(e["t2_open"],11.2)
    def test_rejection(self):
        e=build_edge_events(self.frame(t1close=9.7,t1low=9.5)).iloc[0]
        self.assertTrue(e["t1_rejected"]); self.assertFalse(e["t1_accepted"])
    def test_duplicate_identity_fails_closed(self):
        d=self.frame(); d=pd.concat([d,d.iloc[[0]]],ignore_index=True)
        with self.assertRaises(ValueError): build_edge_events(d)
    def test_summary(self):
        s=summarize(build_edge_events(self.frame()))
        self.assertEqual(s["events"],1); self.assertEqual(s["groups"]["t1_accepted"]["n"],1)

if __name__=="__main__": unittest.main()
