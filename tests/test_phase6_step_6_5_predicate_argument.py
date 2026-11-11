"""Phase 6 Step 6.5 predicate and argument structure acceptance."""
import unittest
from tools.phase6_interpretation_benchmark_v0_3_1.run import load_corpus,evaluate,quality_gate
from tools.phase6_predicate_argument_v0_3_0.analyzer import analyze,predict_corpus
class Phase6Step65Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.corpus=load_corpus(); cls.predictions=predict_corpus(cls.corpus)
  cls.report=evaluate(cls.corpus,cls.predictions); cls.gate=quality_gate(cls.report)
 def test_all_eight_bilingual_construction_profiles_pass(self):
  self.assertTrue(self.gate["passed"],self.report)
 def test_exact_participant_roles_and_spans_are_returned(self):
  gold={x["id"]:x for x in self.corpus["cases"]}
  for p in self.predictions["predictions"]:
   c=gold[p["case_id"]]
   if c["gold_class"]=="POSITIVE":
    self.assertEqual(p["role_bindings"],c["expected_roles"],c["id"])
    self.assertEqual(p["role_spans"],c["expected_role_spans"],c["id"])
    self.assertEqual(p["predicate_span"],c["expected_predicate_span"],c["id"])
    self.assertEqual(p["grammatical_markers"],c["expected_grammatical_markers"],c["id"])
 def test_negative_and_ambiguous_fixtures_abstain(self):
  gold={x["id"]:x for x in self.corpus["cases"]}
  for p in self.predictions["predictions"]:
   if gold[p["case_id"]]["gold_class"]!="POSITIVE": self.assertIsNone(p["construction_id"],p["case_id"])
 def test_word_order_is_not_a_standalone_role_rule(self):
  result=analyze("The teacher saw the student with the book.","en")
  self.assertIsNone(result["construction_id"])
if __name__=="__main__": unittest.main()
