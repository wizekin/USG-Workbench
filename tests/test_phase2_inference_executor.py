"""Regression tests for Phase 2 Step 2.6 deterministic inference."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from tools.semantic_inference_v1_0_0.engine import InferenceExecutor, RULE_MP, RULE_AND_LEFT

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "specifications/usg-sem-1.0.schema.json").read_text(encoding="utf-8"))
FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
FIXTURE_SCHEMA = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.schema.json").read_text(encoding="utf-8"))


def make_document(kind="mp"):
    document_id = "DOC-EXEC-" + kind.upper()
    expressions = [
        {"id":"expr-a","op":"PREDICATE_APP","sort":"PROP","operandRefs":[],"params":{"predicate":"A"},"interpretationStatus":"RESOLVED"},
        {"id":"expr-b","op":"PREDICATE_APP","sort":"PROP","operandRefs":[],"params":{"predicate":"B"},"interpretationStatus":"RESOLVED"},
        {"id":"expr-c","op":"PREDICATE_APP","sort":"PROP","operandRefs":[],"params":{"predicate":"C"},"interpretationStatus":"RESOLVED"},
    ]
    assertions = []
    if kind in {"mp","converse","context","disputed","ambiguous","unresolved","unknown"}:
        expressions.append({"id":"expr-imp","op":"IMPLIES","sort":"PROP","operandRefs":["expr-a","expr-b"],"params":{},"interpretationStatus":"RESOLVED"})
        a_status = "SOURCE_ASSERTED"
        if kind == "disputed": a_status = "DISPUTED"
        if kind == "unknown": a_status = "UNKNOWN"
        if kind == "ambiguous": expressions[0]["interpretationStatus"] = "AMBIGUOUS"
        if kind == "unresolved": expressions[0]["interpretationStatus"] = "UNRESOLVED"
        if kind == "converse":
            assertions = [
                {"id":"assert-b","expressionRef":"expr-b","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"},
                {"id":"assert-imp","expressionRef":"expr-imp","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"},
            ]
        else:
            assertions = [
                {"id":"assert-a","expressionRef":"expr-a","origin":"SOURCE_TEXT","epistemicStatus":a_status,"commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"},
                {"id":"assert-imp","expressionRef":"expr-imp","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"},
            ]
            if kind == "context":
                assertions[0]["evaluationContext"]["contextRef"] = "ctx-other"
    elif kind == "and":
        expressions.append({"id":"expr-and","op":"AND","sort":"PROP","operandRefs":["expr-a","expr-b"],"params":{},"interpretationStatus":"RESOLVED"})
        assertions = [{"id":"assert-and","expressionRef":"expr-and","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"}]
    return {
        "profileId":"USG-SEM/1.0","documentId":document_id,"createdAt":"2026-11-10T00:00:00Z",
        "sources":[{"id":"source-main","text":"A. B. If A then B.","language":"en","sourceType":"CURATED","trustTier":"STANDARD","sensitivity":"PUBLIC","offsetUnit":"unicode_code_point"}],"primarySourceRef":"source-main",
        "definitions":{"ontologyRelease":"ontology-2026.1","grammarVersion":"grammar-1.0","concepts":[],"frames":[],"roles":[],"relations":[]},
        "referents":[],"mentions":[],"expressions":expressions,"rootExpressionRefs":[item["id"] for item in expressions],
        "assertions":assertions,"evidence":[],"contexts":[{"id":"ctx-world","kind":"WORLD"},{"id":"ctx-other","kind":"WORLD"}],
        "expressionRelations":[],"unresolvedItems":[],"derivations":[],
        "validation":{"structuralStatus":"PASS","checks":[],"contractVersion":"USG-SEM/1.0"},
        "mapping":{"sourceProfile":"USG-SEM/1.0","sourceVersion":"1.0","status":"LOSSLESS","unmappedRefs":[]},
        "extensions":{}
    }


def task(rule_id, **extra):
    return {"task_id":"test-task","rule_ids":[rule_id],"world_assumption":"OPEN","allow_inferred_premises":False,"evidence_assessment":False,**extra}


class Phase2InferenceExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor = InferenceExecutor()

    def assert_canonical(self, document):
        errors = list(Draft202012Validator(SCHEMA).iter_errors(document))
        self.assertEqual(errors, [], [f"{e.json_path}: {e.message}" for e in errors])

    def test_benchmark_bundle_schema_and_fixture_declarations(self):
        errors = list(Draft202012Validator(FIXTURE_SCHEMA).iter_errors(FIXTURES))
        self.assertEqual(errors, [])
        self.assertEqual(len(FIXTURES["fixtures"]), 10)
        for fixture in FIXTURES["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                self.assert_canonical(fixture["document"])
                result = self.executor.execute(fixture["document"], fixture["task"])
                self.assertEqual(result["completion_status"], fixture["expected"]["completion_status"])
                self.assertEqual(len(result["conclusion_candidates"]), fixture["expected"]["candidate_count"])
                self.assertTrue(set(fixture["expected"]["diagnostics"]).issubset(set(result["diagnostics"])))

    def test_modus_ponens_creates_non_truth_promoting_candidate(self):
        document = make_document("mp")
        self.assert_canonical(document)
        result = self.executor.execute(document, task(RULE_MP))
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(len(result["conclusion_candidates"]), 1)
        candidate = result["conclusion_candidates"][0]
        self.assertEqual(candidate["expression_ref"], "expr-b")
        self.assertEqual(candidate["epistemic_effect"], "DERIVED_NOT_VERIFIED")
        self.assertFalse(candidate["truth_promotion"])
        self.assertNotIn(candidate["id"], {item["id"] for item in document["assertions"]})
        self.assertEqual(len(result["derivations"]), 1)
        self.assertEqual(result["derivations"][0]["input_refs"], ["assert-a","assert-imp","expr-imp"])
        self.assertEqual(len(result["document_sha256"]), 64)

    def test_left_conjunction_elimination_preserves_operand_order(self):
        document = make_document("and")
        self.assert_canonical(document)
        result = self.executor.execute(document, task(RULE_AND_LEFT))
        self.assertEqual([item["expression_ref"] for item in result["conclusion_candidates"]], ["expr-a"])

    def test_converse_is_not_inferred(self):
        result = self.executor.execute(make_document("converse"), task(RULE_MP))
        self.assertEqual(result["conclusion_candidates"], [])

    def test_context_mismatch_blocks_inference(self):
        result = self.executor.execute(make_document("context"), task(RULE_MP))
        self.assertEqual(result["conclusion_candidates"], [])

    def test_disputed_unknown_ambiguous_and_unresolved_inputs_are_not_coerced(self):
        cases = [
            ("disputed","RULE_PREMISE_DISPUTED"),
            ("unknown","RULE_PREMISE_STATUS_UNKNOWN"),
            ("ambiguous","RULE_EXPRESSION_AMBIGUOUS"),
            ("unresolved","RULE_EXPRESSION_NOT_RESOLVED"),
        ]
        for kind, diagnostic in cases:
            with self.subTest(kind=kind):
                result = self.executor.execute(make_document(kind), task(RULE_MP))
                self.assertEqual(result["conclusion_candidates"], [])
                self.assertIn(diagnostic, result["diagnostics"])

    def test_resource_interruption_preserves_all_input_ids_and_reports_pending_work(self):
        document = make_document("mp")
        result = self.executor.execute(document, task(RULE_MP, max_rule_applications=0))
        self.assertEqual(result["completion_status"], "INCOMPLETE")
        self.assertTrue(result["pending_work"])
        self.assertEqual(set(result["preserved_input_refs"]), {item["id"] for item in document["expressions"] + document["assertions"] + document["contexts"]})
        self.assertFalse(result["resource"]["semantic_truncation"])

    def test_inferred_candidates_are_never_chained(self):
        document = make_document("mp")
        document["expressions"].append({"id":"expr-next","op":"IMPLIES","sort":"PROP","operandRefs":["expr-b","expr-c"],"params":{},"interpretationStatus":"RESOLVED"})
        document["assertions"].append({"id":"assert-next","expressionRef":"expr-next","origin":"SOURCE_TEXT","epistemicStatus":"SOURCE_ASSERTED","commitment":"AUTHOR","evaluationContext":{"kind":"WORLD","contextRef":"ctx-world"},"lifecycleStage":"STRUCTURED"})
        self.assert_canonical(document)
        result = self.executor.execute(document, task(RULE_MP))
        self.assertEqual({item["expression_ref"] for item in result["conclusion_candidates"]}, {"expr-b"})

    def test_identical_input_is_deterministic_and_input_is_immutable(self):
        document = make_document("mp")
        original = copy.deepcopy(document)
        first = self.executor.execute(document, task(RULE_MP))
        second = self.executor.execute(document, task(RULE_MP))
        self.assertEqual(first, second)
        self.assertEqual(document, original)

    def test_unregistered_rule_is_explicitly_unsupported(self):
        result = self.executor.execute(make_document("mp"), task("benchmark-rule:not-enabled"))
        self.assertEqual(result["completion_status"], "UNSUPPORTED")
        self.assertIn("RULE_NOT_ENABLED", result["diagnostics"])


if __name__ == "__main__":
    unittest.main()
