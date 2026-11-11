"""Phase 5 nested semantic composition and graph validation tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0 import (
    LexicalAnalyzer, bundled_lexical_resource, segment_document, SyntaxAnalyzer,
    SemanticComposer,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "specifications/usg-interpret-expression-graph-0.2.0.schema.json").read_text(encoding="utf-8"))


class Phase5SemanticCompositionTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(bundled_lexical_resource())
        self.syntax_analyzer = SyntaxAnalyzer()
        self.composer = SemanticComposer()

    def compose(self, text, language):
        source = ingest_source(text, language)
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        syntax = self.syntax_analyzer.analyze(lexical, segmented)
        return source, lexical, segmented, syntax, self.composer.compose(lexical, segmented, syntax)

    def assert_graph_integrity(self, source, candidate):
        encoded = candidate.to_dict()
        Draft202012Validator(SCHEMA).validate(encoded)
        nodes = {node["nodeId"]: node for node in encoded["nodes"]}
        self.assertIn(encoded["rootRef"], nodes)
        for node in nodes.values():
            for ref in node["operandRefs"]:
                self.assertIn(ref, nodes)
            span = node["sourceSpan"]
            self.assertEqual(span["offsetUnit"], "unicode_code_point")
            self.assertGreaterEqual(span["start"], 0)
            self.assertLessEqual(span["end"], len(source.text))
            self.assertLess(span["start"], span["end"])
        for ref in encoded["clauseRootRefs"]:
            self.assertIn(ref, nodes)
        return encoded

    def test_simple_english_clause_composes_typed_entity_and_predicate_nodes(self):
        source, _, _, _, result = self.compose("Ada writes code.", "en")
        self.assertEqual(result.status, "COMPOSED")
        graph = self.assert_graph_integrity(source, result.candidates[0])
        ops = [x["op"] for x in graph["nodes"]]
        self.assertEqual(ops.count("REF"), 2)
        self.assertEqual(ops.count("PREDICATE"), 1)
        predicate = next(x for x in graph["nodes"] if x["op"] == "PREDICATE")
        self.assertEqual(predicate["params"]["predicateRef"], "frame:write.transitive")
        self.assertEqual(set(predicate["params"]["roleBindings"]), {"AGENT", "PATIENT"})
        self.assertEqual(len(predicate["operandRefs"]), 2)

    def test_arabic_vso_and_svo_map_to_the_same_predicate_frame(self):
        for text in ("كتب الطالب الرسالة", "الطالب كتب الرسالة"):
            source, _, _, _, result = self.compose(text, "ar")
            self.assertEqual(result.status, "COMPOSED")
            graph = self.assert_graph_integrity(source, result.candidates[0])
            predicate = next(x for x in graph["nodes"] if x["op"] == "PREDICATE")
            self.assertEqual(predicate["params"]["predicateRef"], "frame:write.transitive")

    def test_multi_clause_graph_preserves_nested_clause_roots_and_attachment_evidence(self):
        text = "Ada writes code, and Mira reads reports."
        source, _, _, _, result = self.compose(text, "en")
        self.assertEqual(result.status, "COMPOSED")
        graph = self.assert_graph_integrity(source, result.candidates[0])
        group = next(x for x in graph["nodes"] if x["op"] == "CLAUSE_GROUP")
        self.assertEqual(len(group["operandRefs"]), 2)
        self.assertEqual(len(graph["clauseRootRefs"]), 2)
        attachments = group["params"]["attachmentCandidates"]
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["relation"], "COORDINATION_AND")
        self.assertEqual(attachments[0]["status"], "CANDIDATE")

    def test_lexical_ambiguity_creates_multiple_graph_candidates(self):
        source, _, _, _, result = self.compose("Ada writes bank.", "en")
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertEqual(len(result.candidates), 2)
        patient_senses = set()
        for candidate in result.candidates:
            graph = self.assert_graph_integrity(source, candidate)
            patient = next(x for x in graph["nodes"]
                           if x["op"] == "REF" and x["params"]["role"] == "PATIENT")
            patient_senses.add(patient["params"]["senseRef"])
        self.assertEqual(patient_senses, {"en:noun.bank.financial", "en:noun.bank.river"})

    def test_unknown_word_returns_partial_without_inventing_a_predicate(self):
        _, _, _, _, result = self.compose("Ada writes flibbertigibbet.", "en")
        self.assertEqual(result.status, "UNSUPPORTED")
        self.assertEqual(result.candidates, ())

    def test_known_but_unsupported_order_does_not_compose(self):
        _, _, _, _, result = self.compose("Ada code writes.", "en")
        self.assertEqual(result.status, "UNSUPPORTED")
        self.assertEqual(result.candidates, ())

    def test_candidate_budget_is_explicit(self):
        source = ingest_source("Ada writes bank.", "en")
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        syntax = self.syntax_analyzer.analyze(lexical, segmented)
        result = SemanticComposer(max_candidates=1).compose(lexical, segmented, syntax)
        self.assertEqual(result.status, "INCOMPLETE_RESOURCE_LIMIT")
        self.assertEqual(len(result.candidates), 1)

    def test_syntax_from_a_different_source_is_rejected_even_when_clause_ids_match(self):
        source = ingest_source("Ada writes code.", "en")
        other = ingest_source("Mira reads reports.", "en")
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        other_lexical = self.lexical.analyze(other)
        other_segmented = segment_document(other_lexical)
        other_syntax = self.syntax_analyzer.analyze(other_lexical, other_segmented)
        with self.assertRaises(ValueError):
            self.composer.compose(lexical, segmented, other_syntax)

    def test_source_evidence_and_derivation_refs_are_retained_on_every_node(self):
        source, _, _, _, result = self.compose("كتب الطالب الرسالة", "ar")
        for node in result.candidates[0].nodes:
            self.assertTrue(node.derivation_refs)
            start, end = node.source_span
            self.assertLessEqual(end, len(source.text))
            self.assertLess(start, end)


if __name__ == "__main__":
    unittest.main()
