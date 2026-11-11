"""Phase 5 operator recognition, scope, and semantic graph tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0 import (
    LexicalAnalyzer, bundled_lexical_resource_v0_2_0, segment_document,
    OperatorAnalyzer, SyntaxAnalyzer, SemanticComposer,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPH_SCHEMA = json.loads((ROOT / "specifications/usg-interpret-expression-graph-0.2.0.schema.json").read_text(encoding="utf-8"))


class Phase5OperatorScopeTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(bundled_lexical_resource_v0_2_0())
        self.operator_analyzer = OperatorAnalyzer()
        self.syntax_analyzer = SyntaxAnalyzer()
        self.composer = SemanticComposer()

    def analyze(self, text, language):
        source = ingest_source(text, language)
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        operators = self.operator_analyzer.analyze(lexical, segmented)
        syntax = self.syntax_analyzer.analyze(lexical, segmented, operators)
        composition = self.composer.compose(lexical, segmented, syntax, operators)
        return source, lexical, segmented, operators, syntax, composition

    def assert_operator_graph(self, source, composition):
        self.assertTrue(composition.candidates)
        graph = composition.candidates[0].to_dict()
        Draft202012Validator(GRAPH_SCHEMA).validate(graph)
        nodes = {x["nodeId"]: x for x in graph["nodes"]}
        for node in nodes.values():
            if node["op"] == "OPERATOR":
                self.assertIn(node["params"]["scopeTargetRef"], nodes)
                self.assertEqual(source.text[node["sourceSpan"]["start"]:node["sourceSpan"]["end"]],
                                 node["params"]["surfaceText"])
        return graph, nodes

    def test_negation_is_an_explicit_operator_with_predicate_scope(self):
        source, _, _, operators, syntax, composition = self.analyze("Ada does not write code.", "en")
        self.assertEqual(operators.status, "RESOLVED")
        self.assertEqual(syntax.status, "COMPLETE")
        self.assertEqual(composition.status, "COMPOSED")
        graph, nodes = self.assert_operator_graph(source, composition)
        op = next(x for x in nodes.values() if x["op"] == "OPERATOR")
        self.assertEqual(op["params"]["operatorType"], "NEGATION")
        self.assertEqual(op["params"]["operatorValue"], "NOT")
        self.assertEqual(op["params"]["scopeTargetKind"], "PREDICATE")
        self.assertEqual(graph["rootRef"], op["nodeId"])

    def test_modality_and_future_tense_have_distinct_operator_types(self):
        for text, expected_type, expected_value in (
            ("Ada may write code.", "MODALITY", "POSSIBILITY"),
            ("Ada must write code.", "MODALITY", "NECESSITY"),
            ("Ada will write code.", "TENSE", "FUTURE"),
        ):
            source, _, _, _, _, composition = self.analyze(text, "en")
            self.assertEqual(composition.status, "COMPOSED", text)
            _, nodes = self.assert_operator_graph(source, composition)
            op = next(x for x in nodes.values() if x["op"] == "OPERATOR")
            self.assertEqual(op["params"]["operatorType"], expected_type)
            self.assertEqual(op["params"]["operatorValue"], expected_value)

    def test_perfect_aspect_requires_a_registered_participle(self):
        source, _, _, operators, _, composition = self.analyze("Ada has written code.", "en")
        self.assertEqual(operators.status, "RESOLVED")
        self.assertEqual(composition.status, "COMPOSED")
        _, nodes = self.assert_operator_graph(source, composition)
        op = next(x for x in nodes.values() if x["op"] == "OPERATOR")
        self.assertEqual(op["params"]["operatorType"], "ASPECT")
        self.assertEqual(op["params"]["operatorValue"], "PERFECT")

    def test_quantifier_scopes_to_the_following_argument(self):
        source, _, _, _, _, composition = self.analyze("Every student writes code.", "en")
        self.assertEqual(composition.status, "COMPOSED")
        _, nodes = self.assert_operator_graph(source, composition)
        op = next(x for x in nodes.values() if x["op"] == "OPERATOR")
        target = nodes[op["params"]["scopeTargetRef"]]
        self.assertEqual(target["op"], "REF")
        self.assertEqual(target["params"]["role"], "AGENT")
        self.assertEqual(op["params"]["operatorValue"], "UNIVERSAL")

    def test_arabic_negation_future_and_quantification_are_explicit(self):
        examples = (
            ("لا يكتب الطالب الرسالة", "NEGATION", "NOT"),
            ("سوف يكتب الطالب الرسالة", "TENSE", "FUTURE"),
            ("كل طالب يكتب الرسالة", "QUANTIFIER", "UNIVERSAL"),
            ("لم يكتب الطالب الرسالة", "NEGATION", "PAST_NEGATION"),
            ("لن يكتب الطالب الرسالة", "NEGATION", "FUTURE_NEGATION"),
        )
        for text, expected_type, expected_value in examples:
            source, _, _, _, _, composition = self.analyze(text, "ar")
            self.assertEqual(composition.status, "COMPOSED", text)
            _, nodes = self.assert_operator_graph(source, composition)
            op = next(x for x in nodes.values() if x["op"] == "OPERATOR")
            self.assertEqual(op["params"]["operatorType"], expected_type)
            self.assertEqual(op["params"]["operatorValue"], expected_value)

    def test_multiple_operator_scopes_are_retained_as_alternatives(self):
        source, _, _, operators, _, composition = self.analyze("Ada may not write code.", "en")
        clause = operators.clauses[0]
        self.assertEqual(clause.status, "AMBIGUOUS")
        self.assertEqual(len(clause.scope_alternatives), 2)
        self.assertEqual(composition.status, "AMBIGUOUS")
        self.assertEqual(len(composition.candidates), 2)
        outer_types = set()
        for candidate in composition.candidates:
            graph = candidate.to_dict()
            nodes = {x["nodeId"]: x for x in graph["nodes"]}
            outer_types.add(nodes[graph["rootRef"]]["params"]["operatorType"])
        self.assertEqual(outer_types, {"MODALITY", "NEGATION"})

    def test_operator_without_a_valid_scope_target_is_not_silently_dropped(self):
        _, _, _, operators, _, composition = self.analyze("Ada may code.", "en")
        self.assertEqual(operators.status, "PARTIAL")
        self.assertEqual(operators.clauses[0].status, "INCOMPLETE")
        self.assertEqual(composition.status, "PARTIAL")
        self.assertEqual(composition.candidates, ())

    def test_operator_and_syntax_artifacts_must_share_source_identity(self):
        source = ingest_source("Ada may write code.", "en")
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        operators = self.operator_analyzer.analyze(lexical, segmented)
        syntax = self.syntax_analyzer.analyze(lexical, segmented, operators)
        other = ingest_source("Mira must read reports.", "en")
        other_lexical = self.lexical.analyze(other)
        other_segmented = segment_document(other_lexical)
        other_operators = self.operator_analyzer.analyze(other_lexical, other_segmented)
        with self.assertRaises(ValueError):
            self.composer.compose(lexical, segmented, syntax, other_operators)

    def test_plain_clause_has_no_operator_nodes(self):
        source, _, _, operators, _, composition = self.analyze("Ada writes code.", "en")
        self.assertEqual(operators.status, "NONE")
        self.assertEqual(composition.status, "COMPOSED")
        graph = composition.candidates[0].to_dict()
        self.assertNotIn("OPERATOR", {x["op"] for x in graph["nodes"]})


if __name__ == "__main__":
    unittest.main()
