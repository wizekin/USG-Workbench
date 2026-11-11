"""Tests for additive Phase 6 benchmark annotation correction."""
import unittest
from tools.phase6_interpretation_benchmark_v0_3_1.run import load_corpus
class Phase6Benchmark031Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.corpus=load_corpus()
 def test_v030_is_versioned_forward_not_mutated(self):
  self.assertEqual(self.corpus["version"],"0.3.1")
  self.assertEqual(len(self.corpus["cases"]),400)
 def test_predicate_heads_are_not_semantic_roles(self):
  for case in self.corpus["cases"]:
   self.assertFalse({"ACTION","COPULA","RELATION"} & set(case["expected_roles"]))
   if case["gold_class"]=="POSITIVE":
    self.assertTrue(case["expected_predicate_span"] or case["expected_grammatical_markers"])
 def test_predicate_and_marker_spans_are_exact(self):
  for case in self.corpus["cases"]:
   spans=list(case["expected_role_spans"].values())
   if case["expected_predicate_span"]: spans.append(case["expected_predicate_span"])
   spans.extend(case["expected_grammatical_markers"])
   for span in spans: self.assertEqual(case["text"][span["start"]:span["end"]],span["surface"])
if __name__=="__main__": unittest.main()
