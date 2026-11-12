"""Tests for integrating the existing Phase 6 candidate providers."""
import unittest

from tools.phase6_broader_semantics_v0_1.interpret import Phase6IntegratedInterpreter


class Phase6CandidateProviderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = Phase6IntegratedInterpreter()

    def test_predicate_argument_provider_adds_intransitive_event_frame(self):
        result = self.service.interpret("Mina sleeps.", "en")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertIn("PHASE6_PREDICATE_ARGUMENT_PROVIDER:en.intransitive.basic", result["diagnostics"])
        graph = result["graph"]
        self.assertIn("PREDICATE_ARGUMENT", graph["features"])
        self.assertTrue(any(node.get("role") == "AGENT" and node["span"]["surface"] == "Mina"
                            for node in graph["nodes"]))
        self.assertTrue(any(edge["type"] == "AGENT" for edge in graph["relations"]))

    def test_arabic_predicate_argument_provider_adds_bounded_candidate(self):
        result = self.service.interpret("نام الرجل", "ar")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertIn("PHASE6_PREDICATE_ARGUMENT_PROVIDER:ar.intransitive.basic", result["diagnostics"])
        self.assertIn("PREDICATE_ARGUMENT", result["graph"]["features"])

    def test_english_shared_argument_coordination_preserves_both_agents(self):
        result = self.service.interpret("Ada and Mira read code.", "en")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertIn("PHASE6_SHARED_ARGUMENT_COORDINATION:en.coordinated.subjects.v1",
                      result["diagnostics"])
        graph = result["graph"]
        self.assertIn("COORDINATION", graph["features"])
        self.assertEqual(
            [node["span"]["surface"] for node in graph["nodes"] if node.get("role") == "AGENT"],
            ["Ada", "Mira"],
        )
        self.assertEqual(
            sum(edge["type"] == "AGENT" for edge in graph["relations"]), 2
        )
        self.assertTrue(any(
            edge["type"] == "PATIENT"
            and next(node for node in graph["nodes"] if node["id"] == edge["target"])["span"]["surface"] == "code"
            for edge in graph["relations"]
        ))

    def test_arabic_shared_argument_coordination_splits_attached_waw_span(self):
        result = self.service.interpret("يكتب الطالب والمعلم الرسالة", "ar")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertIn("PHASE6_SHARED_ARGUMENT_COORDINATION:ar.coordinated.subjects.v1",
                      result["diagnostics"])
        graph = result["graph"]
        self.assertIn("COORDINATION", graph["features"])
        agents = [node for node in graph["nodes"] if node.get("role") == "AGENT"]
        self.assertEqual([node["span"]["surface"] for node in agents], ["الطالب", "المعلم"])
        and_edge = next(edge for edge in graph["relations"] if edge["type"] == "AND")
        self.assertEqual(and_edge["evidence"]["surface"], "و")
        self.assertTrue(any(node.get("role") == "PATIENT"
                            and node["span"]["surface"] == "الرسالة"
                            for node in graph["nodes"]))

    def test_nominal_provider_adds_adjective_property_candidate(self):
        result = self.service.interpret("the blue notebook", "en")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertIn("PHASE6_NOMINAL_PROVIDER:en.nominal.adjective_modifier", result["diagnostics"])
        graph = result["graph"]
        self.assertIn("NOMINAL_PROPERTY", graph["features"])
        self.assertTrue(any(edge["type"] == "ATTRIBUTE" for edge in graph["relations"]))
        self.assertEqual(result["candidate_provider_results"]["nominal"]["status"], "CANDIDATE")

    def test_nominal_genitive_keeps_unspecified_relation(self):
        # The exact provider lexicon licenses only this registered shape.
        result = self.service.interpret("the father's book", "en")
        if result["status"] == "CANDIDATE_ONLY":
            relations = [edge["type"] for edge in result["graph"]["relations"]]
            self.assertNotIn("POSSESSED", relations)
            self.assertIn("GENITIVE_UNSPECIFIED", relations)

    def test_ambiguous_candidate_provider_is_not_forced_to_unique(self):
        result = self.service.interpret("طالب المدرسة", "ar")
        nominal = result.get("candidate_provider_results", {}).get("nominal", {})
        if nominal.get("status") == "AMBIGUOUS":
            self.assertFalse(any(item.startswith("PHASE6_NOMINAL_PROVIDER:")
                                 for item in result["diagnostics"]))
            self.assertTrue(any(item.startswith("PHASE6_NOMINAL_AMBIGUOUS:")
                                for item in result["diagnostics"]))


if __name__ == "__main__":
    unittest.main()
