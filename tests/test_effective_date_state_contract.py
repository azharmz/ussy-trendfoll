import unittest
import pandas as pd
from alert_state import compute_alert_transitions
from candidate_lifecycle import build_candidate_lifecycle


def frame(rows): return pd.DataFrame(rows)


class EffectiveDateStateContractTests(unittest.TestCase):
    def test_failed_current_row_is_invalidated(self):
        prev=frame([{"symbol":"AAA","date":"2026-09-13","investability_status":"NEAR_PASS","tradability_status":"FAIL"}])
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"FAIL","tradability_status":"FAIL"}])
        self.assertEqual(compute_alert_transitions(latest,prev,{"AAA"})[0]["event"],"INVALIDATED")

    def test_current_member_missing_row_is_data_unavailable(self):
        prev=frame([{"symbol":"BBB","date":"2026-09-13","investability_status":"NEAR_PASS","tradability_status":"FAIL"}])
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"PASS","tradability_status":"FAIL"}])
        events=compute_alert_transitions(latest,prev,{"AAA","BBB"})
        self.assertEqual([e for e in events if e["symbol"]=="BBB"][0]["event"],"DATA_UNAVAILABLE")

    def test_removed_member_is_out_of_universe(self):
        prev=frame([{"symbol":"BBB","date":"2026-09-13","investability_status":"NEAR_PASS","tradability_status":"FAIL"}])
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"PASS","tradability_status":"FAIL"}])
        events=compute_alert_transitions(latest,prev,{"AAA"})
        self.assertEqual([e for e in events if e["symbol"]=="BBB"][0]["event"],"OUT_OF_UNIVERSE")

    def test_absence_states_cannot_be_actionable(self):
        prev=frame([
            {"symbol":"BBB","date":"2026-09-13","investability_status":"PASS","tradability_status":"FAIL"},
            {"symbol":"CCC","date":"2026-09-13","investability_status":"PASS","tradability_status":"FAIL"},
        ])
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"PASS","tradability_status":"PASS"}])
        events=compute_alert_transitions(latest,prev,{"AAA","BBB"})
        absent=[e for e in events if e["symbol"] in {"BBB","CCC"}]
        self.assertEqual({e["event"] for e in absent},{"DATA_UNAVAILABLE","OUT_OF_UNIVERSE"})

    def test_lifecycle_preserves_three_way_state(self):
        history=frame([{"symbol":"BBB","date":"2026-09-13","investability_status":"NEAR_PASS","tradability_status":"FAIL"}])
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"PASS","tradability_status":"FAIL"}])
        unavailable=build_candidate_lifecycle(history,latest,{"AAA","BBB"}).iloc[0]
        removed=build_candidate_lifecycle(history,latest,{"AAA"}).iloc[0]
        self.assertEqual(unavailable["current_state"],"DATA_UNAVAILABLE")
        self.assertEqual(removed["current_state"],"OUT_OF_UNIVERSE")

    def test_latest_must_be_subset_of_universe(self):
        latest=frame([{"symbol":"AAA","date":"2026-09-14","investability_status":"PASS","tradability_status":"FAIL"}])
        with self.assertRaises(ValueError): compute_alert_transitions(latest,pd.DataFrame(),{"BBB"})


if __name__ == "__main__": unittest.main()