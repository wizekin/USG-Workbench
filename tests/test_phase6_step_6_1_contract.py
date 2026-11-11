"""Phase 6 Step 6.1 interpretation contract and schema tests."""
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specifications"
CONTRACT = ROOT / "documentation" / "PHASE-6-STEP-6.1-INTERPRETATION-AND-PROJECTION-CONTRACT.md"
ENVELOPE_PATH = SPEC / "usg-interpret-0.3.0.schema.json"
GRAPH_PATH = SPEC / "usg-interpret-expression-graph-0.3.0.schema.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_graph():
    return {
        "graphId": "g1", "graphVersion": "0.3.0", "sourceRef": "src1",
        "sourceSha256": "a" * 64, "status": "RESOLVED", "rootRefs": ["p1"],
        "nodes": [
            {"nodeId": "p1", "nodeType": "PROPOSITION", "status": "RESOLVED",
             "sourceSpans": [{"sourceRef": "src1", "start": 0, "end": 4, "offsetUnit": "unicode_code_point"}],
             "derivationRefs": ["d1"], "attributes": {"predicate": "arrive"}},
            {"nodeId": "d1", "nodeType": "DERIVATION", "status": "RESOLVED",
             "sourceSpans": [], "derivationRefs": [], "attributes": {"ruleId": "fixture.rule/1"}}
        ],
        "edges": [{"edgeId": "e1", "relationType": "DERIVED_FROM", "fromRef": "p1",
                   "toRef": "d1", "sourceSpans": [], "derivationRefs": ["d1"]}]
    }


def valid_envelope():
    graph = valid_graph()
    return {
        "pipelineContract": "USG-INTERPRET/0.3.0", "pipelineVersion": "0.3.0.dev0",
        "languageProfile": "en/standard-written-1.0", "completionStatus": "COMPLETE",
        "sourceSnapshot": {"sourceRef": "src1", "sourceText": "John left",
                           "sourceSha256": "a" * 64, "offsetUnit": "unicode_code_point"},
        "interpretationGraph": graph, "stages": [
            {"stageId": "source", "status": "COMPLETE", "implementationVersion": "0.3.0"}
        ], "diagnostics": [], "alternatives": [],
        "resourceLimits": {"declared": {"candidateCount": 1000}, "interrupted": False},
        "projection": {"status": "NOT_ATTEMPTED", "diagnostics": [], "canonicalDocument": None}
    }


class Phase6Step61ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = CONTRACT.read_text(encoding="utf-8")
        cls.graph_schema = load_json(GRAPH_PATH)
        cls.envelope_schema = load_json(ENVELOPE_PATH)
        cls.graph_validator = Draft202012Validator(cls.graph_schema)
        resolver = RefResolver.from_schema(
            cls.envelope_schema,
            store={cls.graph_schema["$id"]: cls.graph_schema,
                   "usg-interpret-expression-graph-0.3.0.schema.json": cls.graph_schema}
        )
        cls.envelope_validator = Draft202012Validator(cls.envelope_schema, resolver=resolver)

    def test_contract_freezes_versions_and_architecture_boundaries(self):
        for phrase in (
            "USG-INTERPRET/0.3.0", "USG-INTERPRET/0.2.0", "USG-INTERPRET/0.1.0",
            "USG-SEM/1.0", "SQLite", "Unicode code-point", "semantic roles",
            "LOSSLESS", "BLOCKED", "LOSSY", "benchmark-enabled", "Step 6.2"
        ):
            self.assertIn(phrase, self.contract)

    def test_valid_graph_and_envelope_pass(self):
        graph = valid_graph()
        self.graph_validator.validate(graph)
        envelope = valid_envelope()
        self.envelope_validator.validate(envelope)

    def test_envelope_rejects_wrong_contract_missing_digest_and_invalid_status(self):
        for mutate in (
            lambda x: x.update(pipelineContract="USG-INTERPRET/0.2.0"),
            lambda x: x["sourceSnapshot"].pop("sourceSha256"),
            lambda x: x.update(completionStatus="SUCCESS"),
        ):
            candidate = valid_envelope()
            mutate(candidate)
            self.assertTrue(list(self.envelope_validator.iter_errors(candidate)))

    def test_lossless_projection_requires_document_and_lossy_projection_forbids_it(self):
        candidate = valid_envelope()
        candidate["projection"] = {"status": "LOSSLESS", "diagnostics": []}
        self.assertTrue(list(self.envelope_validator.iter_errors(candidate)))
        candidate["projection"] = {"status": "LOSSY", "diagnostics": [],
                                   "canonicalDocument": {"profileId": "USG-SEM/1.0"}}
        self.assertTrue(list(self.envelope_validator.iter_errors(candidate)))

    def test_graph_rejects_bad_spans_and_malformed_edges(self):
        candidate = valid_graph()
        candidate["nodes"][0]["sourceSpans"][0]["end"] = 0
        self.assertTrue(list(self.graph_validator.iter_errors(candidate)))
        candidate = valid_graph()
        candidate["edges"][0].pop("toRef")
        self.assertTrue(list(self.graph_validator.iter_errors(candidate)))

    def test_phase5_and_semantic_interchange_contracts_are_not_modified_by_this_step(self):
        self.assertIn("MUST NOT", self.contract)
        self.assertIn("USG-SEM/1.0", self.contract)


if __name__ == "__main__":
    unittest.main()
