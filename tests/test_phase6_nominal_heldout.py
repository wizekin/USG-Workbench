import unittest
from tools.phase6_nominal_candidate_v0_4_1.holdout import build_corpus,evaluate
class TestPhase6NominalHeldout(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.corpus=build_corpus(); cls.report=evaluate(cls.corpus)
 def test_500_fixtures_and_profile_denominators(self):
  self.assertEqual(len(self.corpus["cases"]),500)
  self.assertEqual(len(self.corpus["construction_inventory"]),10)
  for x in self.corpus["construction_inventory"].values():
   self.assertEqual(x,{"positive":20,"negative":20,"ambiguous":10})
 def test_positive_role_combinations_are_held_out(self):
  self.assertEqual(self.corpus["split"],"HELD_OUT_ROLE_COMBINATIONS")
  self.assertIn("not an unseen-lexicon",self.corpus["evaluation_boundary"])
 def test_every_profile_passes_exact_candidate_and_abstention_gates(self):
  self.assertTrue(self.report["all_profile_gates_passed"],self.report["by_construction"])
 def test_no_construction_is_enabled(self):
  self.assertEqual(self.report["benchmark_enabled_constructions"],[])
  self.assertEqual(self.report["runtime_capability_state"],"CANDIDATE_ONLY")
if __name__=="__main__": unittest.main()
