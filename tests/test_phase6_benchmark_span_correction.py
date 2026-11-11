"""Tests for additive Phase 6 benchmark annotation correction."""
import unittest
from tools.phase6_interpretation_benchmark_v0_3_2.run import load_corpus
class Phase6Benchmark031Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.corpus=load_corpus()
 def test_v030_is_versioned_forward_not_mutated(self):
  self.assertEqual(self.corpus["version"],"0.3.2")
  self.assertEqual(len(self.corpus["cases"]),400)
 def test_predicate_heads_are_not_semantic_roles(self):
  for case in self.corpus["cases"]:
   self.assertFalse({"ACTION","COPULA","RELATION"} & set(case["expected_roles"]))
   if case["gold_class"]=="POSITIVE":
    self.assertTrue(case["expected_predicate_span"] or case["expected_grammatical_markers"])
 def test_repeated_participant_mentions_have_distinct_role_spans(self):
  for case in self.corpus["cases"]:
   if case["gold_class"]!="POSITIVE": continue
   spans=list(case["expected_role_spans"].values())
   for left,right in zip(spans,spans[1:]): self.assertLessEqual(left["end"],right["start"])
 def test_predicate_and_marker_spans_are_exact(self):
  for case in self.corpus["cases"]:
   spans=list(case["expected_role_spans"].values())
   if case["expected_predicate_span"]: spans.append(case["expected_predicate_span"])
   spans.extend(case["expected_grammatical_markers"])
   for span in spans: self.assertEqual(case["text"][span["start"]:span["end"]],span["surface"])
if __name__=="__main__": unittest.main()
