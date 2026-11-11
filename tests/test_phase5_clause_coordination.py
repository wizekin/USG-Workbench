"""Phase 5 clause coordination and multi-clause composition tests."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0 import (
    LexicalAnalyzer, bundled_lexical_resource, segment_document,
    SyntaxAnalyzer, SemanticComposer,
)


class Phase5ClauseCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(bundled_lexical_resource())
        self.syntax = SyntaxAnalyzer()
        self.composer = SemanticComposer()

    def compose(self, text, language):
        source = ingest_source(text, language)
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        syntax = self.syntax.analyze(lexical, segmented)
        return source, segmented, syntax, self.composer.compose(lexical, segmented, syntax)

    def test_english_and_builds_typed_coordination_node(self):
        source, segmented, syntax, result = self.compose(
            "Ada writes code, and Mira reads reports.", "en"
        )
        self.assertEqual(syntax.status, "COMPLETE")
        self.assertEqual(result.status, "COMPOSED")
        self.assertEqual(len(segmented.clauses), 2)
        graph = result.candidates[0].to_dict()
        coord = next(x for x in graph["nodes"] if x["op"] == "COORDINATION")
        self.assertEqual(coord["params"]["operatorValue"], "AND")
        self.assertEqual(len(coord["operandRefs"]), 2)
        self.assertEqual(source.text[slice(*coord["params"]["markerSpan"])], "and")

    def test_english_or_and_contrast_remain_distinct(self):
        for text, value in (
            ("Ada writes code or Mira reads reports.", "OR"),
            ("Ada writes code but Mira reads reports.", "CONTRAST"),
        ):
            _, _, _, result = self.compose(text, "en")
            self.assertEqual(result.status, "COMPOSED")
            coord = next(x for x in result.candidates[0].nodes if x.op == "COORDINATION")
            self.assertEqual(dict(coord.params)["operatorValue"], value)

    def test_three_clauses_preserve_left_associative_grouping(self):
        _, segmented, _, result = self.compose(
            "Ada writes code, and Mira reads reports, or Noah builds models.", "en"
        )
        self.assertEqual(len(segmented.clauses), 3)
        self.assertEqual(result.status, "COMPOSED")
        nodes = result.candidates[0].nodes
        coords = [x for x in nodes if x.op == "COORDINATION"]
        self.assertEqual(len(coords), 2)
        root = next(x for x in nodes if x.node_id == result.candidates[0].root_ref)
        self.assertEqual(root.op, "COORDINATION")
        self.assertEqual(dict(root.params)["grouping"], "LEFT_ASSOCIATIVE")
        self.assertEqual(nodes[-1].node_id, root.node_id)

    def test_standalone_arabic_wa_coordinates_clauses(self):
        text = "كتب الطالب الرسالة و قرأ المعلم الكتاب"
        source, segmented, syntax, result = self.compose(text, "ar")
        self.assertEqual(len(segmented.clauses), 2)
        self.assertEqual(segmented.boundaries[0].relation, "COORDINATION_AND")
        self.assertEqual(syntax.status, "COMPLETE")
        self.assertEqual(result.status, "COMPOSED")
        coord = next(x for x in result.candidates[0].nodes if x.op == "COORDINATION")
        self.assertEqual(dict(coord.params)["operatorValue"], "AND")
        self.assertEqual(source.text[slice(*dict(coord.params)["markerSpan"])], "و")

    def test_semicolon_and_temporal_links_remain_candidate_groups_not_boolean_coordination(self):
        for text, language in (
            ("Ada writes code; Mira reads reports.", "en"),
            ("كتب الطالب الرسالة ثم قرأ المعلم الكتاب", "ar"),
        ):
            _, _, _, result = self.compose(text, language)
            self.assertEqual(result.status, "COMPOSED")
            self.assertTrue(any(x.op == "CLAUSE_GROUP" for x in result.candidates[0].nodes))
            self.assertFalse(any(x.op == "COORDINATION" for x in result.candidates[0].nodes))


if __name__ == "__main__":
    unittest.main()
