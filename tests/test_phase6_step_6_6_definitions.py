"""Step 6.6 definition-only conformance tests."""
import unittest
from tools.phase6_nominal_modifier_v0_3_0.validate import validate
class Phase6Step66Definitions(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.data=validate()
 def test_five_families_are_defined_for_both_languages(self):
  expected={"ADJECTIVE_MODIFIER","POSSESSION","NOUN_COMPOUND","PREPOSITIONAL_MODIFIER","TEMPORAL_MODIFIER"}
  for lang in ("en","ar"):
   self.assertEqual({r["family"] for r in self.data["rules"] if r["language"]==lang},expected)
 def test_every_rule_has_explicit_evidence_and_ambiguity_policy(self):
  self.assertTrue(all(r["required_evidence"] and r["ambiguity_policy"] for r in self.data["rules"]))
 def test_no_candidate_rule_is_runtime_enabled(self):
  self.assertEqual(self.data["status"],"CANDIDATE")
  self.assertTrue(all(r["status"]=="CANDIDATE" for r in self.data["rules"]))
if __name__=="__main__": unittest.main()
