"""Strict bilingual Phase 6 raw-text candidate extraction tests."""
import unittest
from tools.phase6_broader_semantics_v0_1.extract import extract_candidate_graph
from tools.phase6_broader_semantics_v0_1.engine import compose, project_loss_aware

CASES=[
 ("en","Lina and Omar read books.","en.coordinated.subjects.v1","COORDINATION"),
 ("ar","قرأ علي و سارة الكتاب.","ar.coordinated.subjects.v1","COORDINATION"),
 ("en","Lina knows that Omar left.","en.embedded.complement.v1","EMBEDDED_CLAUSE"),
 ("ar","علمت ليلى أن عمر غادر.","ar.embedded.complement.v1","EMBEDDED_CLAUSE"),
 ("en","Was the book read?","en.passive.question.v1","VOICE"),
 ("ar","هل قُرئ الكتاب؟","ar.passive.question.v1","VOICE"),
 ("en","Lina may not leave.","en.modal.negation.scope.v1","OPERATOR"),
 ("ar","قد لا يغادر علي.","ar.modal.negation.scope.v1","OPERATOR"),
 ("en","Lina met Omar. She smiled.","en.discourse.pronoun.candidates.v1","DISCOURSE_REFERENCE"),
 ("ar","قابلت ليلى عمر. هي ابتسمت.","ar.discourse.pronoun.candidates.v1","DISCOURSE_REFERENCE"),
]
class Phase6RawCandidateExtractionTests(unittest.TestCase):
 def test_all_ten_closed_bilingual_templates_emit_composable_candidate_graphs(self):
  for lang,source,template,feature in CASES:
   with self.subTest(template=template):
    extracted=extract_candidate_graph(source,lang)
    self.assertEqual(extracted["status"],"CANDIDATE_PATTERN_MATCH")
    self.assertEqual(extracted["template_id"],template)
    self.assertIn(feature,extracted["graph"]["features"])
    result=compose(source,lang,extracted["graph"])
    self.assertEqual(result["status"],"CANDIDATE_ONLY")
    self.assertEqual(result["source"]["text"],source)
    self.assertFalse(result["safety"]["canonical_assertions_emitted"])
    self.assertEqual(project_loss_aware(result)["status"],"NOT_PROJECTABLE")
 def test_unsupported_free_text_abstains(self):
  for lang,source in [("en","The quick brown fox jumps over a lazy dog."),("ar","هذه جملة عربية غير مسجلة في القواعد.")]:
   with self.subTest(language=lang):
    result=extract_candidate_graph(source,lang)
    self.assertEqual(result["status"],"ABSTAIN")
    self.assertEqual(result["graph"]["nodes"],[])
    self.assertEqual(result["capability_state"],"CANDIDATE_ONLY")
 def test_all_extracted_node_and_evidence_spans_match_original_source(self):
  for lang,source,_,_ in CASES:
   graph=extract_candidate_graph(source,lang)["graph"]
   for node in graph["nodes"]:
    span=node["span"]; self.assertEqual(source[span["start"]:span["end"]],span["surface"])
   for relation in graph["relations"]:
    span=relation["evidence"]; self.assertEqual(source[span["start"]:span["end"]],span["surface"])
   for operator in graph["operators"]:
    span=operator["span"]; self.assertEqual(source[span["start"]:span["end"]],span["surface"])
 def test_reference_candidates_remain_unresolved(self):
  extracted=extract_candidate_graph("Lina met Omar. She smiled.","en")
  result=compose("Lina met Omar. She smiled.","en",extracted["graph"])
  reference=result["graph"]["references"][0]
  self.assertEqual(reference["status"],"UNRESOLVED")
  self.assertIsNone(reference["resolved_antecedent"])

if __name__=="__main__": unittest.main()
