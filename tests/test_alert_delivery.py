import unittest
from alert_delivery import canonical_event_key

BASE={"symbol":"AAA","as_of_date":"2026-09-18","event":"ACTIONABLE","previous_state":"NEAR_TRIGGER","current_state":"ACTIONABLE"}

class AlertDeliveryIdentityTests(unittest.TestCase):
 def test_identical_replay_same_event(self): self.assertEqual(canonical_event_key(BASE),canonical_event_key(dict(BASE)))
 def test_different_transition_distinct(self):
  other=dict(BASE,event="LOST_TRADABILITY",previous_state="ACTIONABLE",current_state="NEAR_TRIGGER")
  self.assertNotEqual(canonical_event_key(BASE),canonical_event_key(other))
 def test_different_symbol_distinct(self):
  other=dict(BASE,symbol="BBB"); self.assertNotEqual(canonical_event_key(BASE),canonical_event_key(other))
 def test_a_b_a_are_distinct_directions(self):
  ab=dict(BASE,previous_state="NEAR_TRIGGER",current_state="ACTIONABLE",event="ACTIONABLE")
  ba=dict(BASE,previous_state="ACTIONABLE",current_state="NEAR_TRIGGER",event="LOST_TRADABILITY")
  self.assertNotEqual(canonical_event_key(ab),canonical_event_key(ba))
 def test_malformed_fails_closed(self):
  bad=dict(BASE); del bad["previous_state"]
  with self.assertRaises(ValueError): canonical_event_key(bad)
if __name__=="__main__": unittest.main()
