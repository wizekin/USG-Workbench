"""End-to-end tests for the integrated bilingual Phase 6 candidate interpreter."""
import unittest

from tools.usg_local_api_v1_0_0.application import USGApplication


class Phase6IntegratedInterpreterTests(unittest.TestCase):
    def setUp(self):
        self.app = USGApplication(":memory:")

    def tearDown(self):
        self.app.close()

    def call(self, source, language="en", persist=False):
        return self.app.dispatch("POST", "/v3/phase6/interpret", {
            "source": source, "language": language, "persist": persist,
        })

    def test_simple_transitive_candidate_is_carried_into_phase6_graph(self):
        status, result = self.call("Ada writes code.")
        self.assertEqual(status, 200, result)
        interpretation = result["interpretation"]
        self.assertEqual(interpretation["status"], "CANDIDATE_ONLY")
        self.assertEqual(interpretation["phase5_completion_status"], "COMPLETE")
        roles = {node["role"]: node["span"]["surface"]
                 for node in interpretation["graph"]["nodes"]
                 if node.get("role") in {"AGENT", "ACTION", "PATIENT"}}
        self.assertEqual(roles, {"AGENT": "Ada", "ACTION": "writes", "PATIENT": "code"})
        self.assertEqual(len(interpretation["graph"]["relations"]), 2)

    def test_clause_coordination_and_attachment_are_composed(self):
        status, result = self.call("Ada writes code and Ben reads reports.")
        self.assertEqual(status, 200, result)
        graph = result["interpretation"]["graph"]
        self.assertIn("COORDINATION", graph["features"])
        self.assertTrue(any(edge["type"] == "AND" for edge in graph["relations"]))
        self.assertEqual(len(graph["clauses"]), 2)

    def test_causal_subordination_is_preserved_without_asserting_truth(self):
        status, result = self.call("Ada writes code because Ben reads reports.")
        self.assertEqual(status, 200, result)
        interpretation = result["interpretation"]
        graph = interpretation["graph"]
        self.assertIn("EMBEDDED_CLAUSE", graph["features"])
        self.assertTrue(any(edge["type"] == "CAUSAL" for edge in graph["relations"]))
        self.assertFalse(interpretation["composition"]["safety"]["canonical_assertions_emitted"])

    def test_phase6_closed_template_fallback_remains_available(self):
        status, result = self.call("Lina and Omar read books.")
        self.assertEqual(status, 200, result)
        interpretation = result["interpretation"]
        self.assertEqual(interpretation["status"], "CANDIDATE_ONLY")
        self.assertTrue(any(item.startswith("PHASE6_CLOSED_TEMPLATE_FALLBACK:")
                            for item in interpretation["diagnostics"]))
        self.assertIn("COORDINATION", interpretation["graph"]["features"])

    def test_lossless_canonical_preservation_is_opaque_and_validated(self):
        status, result = self.call("Ada writes code.")
        self.assertEqual(status, 200, result)
        projection = result["canonical_preservation_projection"]
        self.assertEqual(projection["status"], "LOSSLESS_PRESERVATION_ONLY", projection)
        document = projection["document"]
        self.assertEqual(document["profileId"], "USG-SEM/1.0")
        self.assertEqual(document["assertions"], [])
        self.assertEqual(document["expressions"][0]["op"], "OPAQUE")
        self.assertEqual(document["expressions"][0]["interpretationStatus"], "UNRESOLVED")
        self.assertFalse(projection["semantic_assertions_emitted"])
        self.assertEqual(self.app._validate(document)["completion_status"], "VALID")

    def test_saved_integrated_interpretation_has_deterministic_replay(self):
        status, result = self.call("Ada writes code.", persist=True)
        self.assertEqual(status, 200, result)
        run_id = result["persistence"]["run_id"]
        replay_status, replay = self.app.dispatch(
            "POST", "/v3/phase6/runs/" + run_id + "/replay", {}
        )
        self.assertEqual(replay_status, 200, replay)
        self.assertTrue(replay["deterministic_match"], replay)

    def test_unknown_language_is_rejected(self):
        status, result = self.call("Ada writes code.", language="xx")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "PHASE6_INTERPRET_INVALID")


if __name__ == "__main__":
    unittest.main()
