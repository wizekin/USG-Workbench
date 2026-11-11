import unittest
from tools.phase6_benchmark_v0_4_1.validate import validate as gold
from tools.phase6_nominal_candidate_v0_4_1.validate import validate as lexicon
from tools.phase6_nominal_candidate_v0_4_1.analyzer import analyze, predict_corpus
from tools.phase6_nominal_candidate_v0_4_1.run import evaluate
class TestPhase6NominalCandidate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.corpus=gold(); cls.resource=lexicon(); cls.pred=predict_corpus(cls.corpus); cls.report=evaluate(cls.corpus,cls.pred)
 def test_candidate_lexicon_is_valid_and_closed(self):
  self.assertTrue(self.resource["entries"]); self.assertEqual(self.resource["morphology_rules"],[])
 def test_every_fixture_is_processed(self):
  self.assertEqual(len(self.pred["predictions"]),500)
 def test_development_self_consistency_gate(self):
  self.assertTrue(self.report["development_gate_passed"],self.report["by_construction"])
 def test_no_construction_is_benchmark_enabled(self):
  self.assertEqual(self.report["benchmark_enabled_constructions"],[])
  self.assertEqual(self.report["runtime_capability_state"],"CANDIDATE_ONLY")
 def test_unknown_words_abstain(self):
  self.assertEqual(analyze("unlisted blorple","en")["status"],"ABSTAIN")
if __name__=="__main__": unittest.main()
