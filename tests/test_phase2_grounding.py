"""Conformance tests for deterministic USG grounding services v1.0.0."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.semantic_grounding_v1_0_0 import GroundingIndex, inspect_compact_benchmark_snapshot


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def make_document():
    return {
        "profileId": "USG-SEM/1.0",
        "documentId": "grounding-fixture-001",
        "sources": [{
            "id": "src-1", "text": "Alice opens the door.", "language": "en",
            "offsetUnit": "unicode_code_point", "sourceType": "DOCUMENT",
            "trustTier": "STANDARD", "sensitivity": "PUBLIC",
        }],
        "primarySourceRef": "src-1",
        "definitions": {
            "grammarVersion": "grammar-1.0",
            "ontologyRelease": "ontology-2026.1",
            "concepts": [
                {"id": "concept-person", "label": "person", "semanticKind": "ENTITY", "version": 1},
                {"id": "concept-person", "label": "person duplicate", "semanticKind": "ENTITY", "version": 2},
            ],
            "frames": [
                {"id": "frame-open", "label": "open", "version": 2, "roles": ["AGENT", "OBJECT"]},
                {"id": "frame-open-alt", "label": "open", "version": 1, "roles": ["AGENT", "CONTAINER"]},
            ],
            "roles": [{"id": "role-agent", "label": "AGENT"}],
            "relations": [{"id": "relation-before", "label": "BEFORE"}],
        },
        "referents": [
            {"id": "ref-alice", "label": "Alice", "identity": {"status": "RESOLVED", "scope": "DOCUMENT"}},
            {"id": "ref-bob", "label": "Bob", "identity": {"status": "RESOLVED", "scope": "DOCUMENT"}},
            {"id": "ref-disputed", "label": "Unknown person", "identity": {"status": "DISPUTED", "scope": "DOCUMENT"}},
        ],
        "mentions": [
            {"id": "mention-alice", "surfaceText": "Alice", "referentRef": "ref-alice", "resolutionStatus": "RESOLVED"},
            {"id": "mention-alice-2", "surfaceText": "she", "referentRef": "ref-alice", "resolutionStatus": "LINKED"},
            {"id": "mention-ambiguous", "surfaceText": "they", "resolutionStatus": "AMBIGUOUS"},
            {"id": "mention-unknown", "surfaceText": "someone", "resolutionStatus": "UNKNOWN"},
            {"id": "mention-unresolved", "surfaceText": "he", "resolutionStatus": "UNRESOLVED"},
            {"id": "mention-disputed", "surfaceText": "the person", "referentRef": "ref-disputed", "resolutionStatus": "RESOLVED"},
        ],
        "expressions": [
            {"id": "expr-alice", "op": "REF", "sort": "TERM", "operandRefs": [], "params": {"referentRef": "ref-alice"}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-open", "op": "PREDICATE_APP", "sort": "SIT", "operandRefs": ["expr-alice"], "params": {"predicate": "OPEN"}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-direct", "op": "PREDICATE_APP", "sort": "SIT", "operandRefs": ["expr-alice"], "params": {"predicate": "DIRECT_OPEN"}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-not", "op": "NOT", "sort": "PROP", "operandRefs": ["expr-open"], "params": {}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-quant", "op": "QUANTIFIER", "sort": "PROP", "operandRefs": ["expr-not"], "params": {"quantifier": "EXISTS", "variable": "x"}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-root", "op": "AND", "sort": "PROP", "operandRefs": ["expr-direct", "expr-quant"], "params": {}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-shared-root", "op": "AND", "sort": "PROP", "operandRefs": ["expr-open", "expr-open"], "params": {}, "interpretationStatus": "RESOLVED"},
            {"id": "expr-opaque-root", "op": "OPAQUE", "sort": "PROP", "operandRefs": ["expr-open"], "params": {"sourceType": "unmapped"}, "interpretationStatus": "UNRESOLVED"},
        ],
        "rootExpressionRefs": ["expr-root", "expr-shared-root", "expr-opaque-root"],
        "assertions": [
            {"id": "assert-world", "expressionRef": "expr-open", "origin": "SOURCE_TEXT", "epistemicStatus": "SOURCE_ASSERTED", "commitment": "AUTHOR", "evaluationContext": {"kind": "WORLD", "contextRef": "ctx-world"}, "lifecycleStage": "STRUCTURED"},
            {"id": "assert-no-context-ref", "expressionRef": "expr-open", "origin": "SOURCE_TEXT", "epistemicStatus": "SOURCE_ASSERTED", "commitment": "AUTHOR", "evaluationContext": {"kind": "WORLD"}, "lifecycleStage": "STRUCTURED"},
            {"id": "assert-kind-mismatch", "expressionRef": "expr-open", "origin": "SOURCE_TEXT", "epistemicStatus": "SOURCE_ASSERTED", "commitment": "AUTHOR", "evaluationContext": {"kind": "FICTION", "contextRef": "ctx-world"}, "lifecycleStage": "STRUCTURED"},
        ],
        "evidence": [],
        "contexts": [
            {"id": "ctx-world", "kind": "WORLD"},
            {"id": "ctx-fiction", "kind": "FICTION", "parentRef": "ctx-world"},
        ],
        "expressionRelations": [],
        "unresolvedItems": [],
        "derivations": [],
        "validation": {"structuralStatus": "PASS", "checks": [], "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
        "mapping": {"sourceProfile": "fixture", "sourceVersion": "1.0", "status": "LOSSLESS", "unmappedRefs": []},
        "extensions": {},
    }


class GroundingServiceTests(unittest.TestCase):
    def setUp(self):
        self.document = make_document()
        # Duplicate concept IDs are an intentional negative fixture. Remove one
        # for ordinary tests; dedicated duplicate tests retain both.
        self.document["definitions"]["concepts"].pop()
        self.index = GroundingIndex(self.document, SCHEMA)

    def test_exact_typed_reference_resolves(self):
        result = self.index.resolve_reference("referent", "ref-alice")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.value["label"], "Alice")

    def test_wrong_record_type_is_invalid_not_coerced(self):
        result = self.index.resolve_reference("context", "ref-alice")
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIn("REFERENCE_TARGET_TYPE_MISMATCH", result.diagnostics)

    def test_missing_reference_is_unresolved(self):
        result = self.index.resolve_reference("referent", "not-present")
        self.assertEqual(result.status, "UNRESOLVED")

    def test_unsupported_record_type_is_not_guessed(self):
        result = self.index.resolve_reference("unknown-family", "x")
        self.assertEqual(result.status, "UNSUPPORTED")

    def test_concept_definition_without_version_is_unresolved(self):
        result = self.index.resolve_definition("concept", "concept-person")
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("DEFINITION_VERSION_REQUIRED", result.diagnostics)

    def test_role_record_cannot_be_given_an_invented_record_version(self):
        result = self.index.resolve_definition("role", "role-agent", version=1)
        self.assertEqual(result.status, "UNSUPPORTED")
        self.assertIn("DEFINITION_RECORD_HAS_NO_VERSION_FIELD", result.diagnostics)

    def test_same_surface_text_does_not_override_explicit_referent_identity(self):
        document = copy.deepcopy(self.document)
        document["mentions"].append({
            "id": "mention-alice-label-collision",
            "surfaceText": "Alice",
            "referentRef": "ref-bob",
            "resolutionStatus": "RESOLVED",
        })
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_mention_referent("mention-alice-label-collision")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.target_id, "ref-bob")

    def test_missing_expression_operand_is_unresolved_even_when_target_path_is_known(self):
        document = copy.deepcopy(self.document)
        root = next(item for item in document["expressions"] if item["id"] == "expr-root")
        root["operandRefs"].append("missing-expression")
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_scope("expr-root", "expr-direct")
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("EXPRESSION_OPERAND_REFERENCE_UNRESOLVED", result.diagnostics)

    def test_unknown_context_kind_remains_unknown(self):
        document = copy.deepcopy(self.document)
        document["contexts"].append({"id": "ctx-unknown", "kind": "UNKNOWN"})
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_context_path("ctx-unknown")
        self.assertEqual(result.status, "UNKNOWN")

    def test_concept_definition_requires_exact_record_version(self):
        result = self.index.resolve_definition("concept", "concept-person", version=1)
        self.assertEqual(result.status, "RESOLVED")
        wrong = self.index.resolve_definition("concept", "concept-person", version=2)
        self.assertEqual(wrong.status, "UNRESOLVED")

    def test_frame_definition_requires_exact_version(self):
        result = self.index.resolve_definition("frame", "frame-open", version=2)
        self.assertEqual(result.status, "RESOLVED")
        wrong = self.index.resolve_definition("frame", "frame-open", version=1)
        self.assertEqual(wrong.status, "UNRESOLVED")

    def test_role_definition_requires_explicit_catalogue_version(self):
        missing = self.index.resolve_definition("role", "role-agent")
        self.assertEqual(missing.status, "UNRESOLVED")
        found = self.index.resolve_definition("role", "role-agent", catalogue_scope="ONTOLOGY", catalogue_version="ontology-2026.1")
        self.assertEqual(found.status, "RESOLVED")
        mismatch = self.index.resolve_definition("role", "role-agent", catalogue_scope="ONTOLOGY", catalogue_version="ontology-old")
        self.assertEqual(mismatch.status, "UNRESOLVED")

    def test_definition_label_never_establishes_identity(self):
        unique = self.index.find_definition_candidates_by_label("concept", "person")
        self.assertEqual(unique.status, "UNRESOLVED")
        self.assertIn("DEFINITION_LABEL_IS_NOT_IDENTITY", unique.diagnostics)
        ambiguous = self.index.find_definition_candidates_by_label("frame", "open")
        self.assertEqual(ambiguous.status, "AMBIGUOUS")
        self.assertEqual(set(ambiguous.candidate_refs), {"frame-open", "frame-open-alt"})

    def test_duplicate_definition_ids_are_invalid(self):
        document = make_document()
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_record("concept", "concept-person")
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIn("DUPLICATE_RECORD_ID", result.diagnostics)

    def test_mention_to_referent_uses_explicit_link_not_surface_text(self):
        result = self.index.resolve_mention_referent("mention-alice")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.target_id, "ref-alice")
        other = self.index.resolve_mention_referent("mention-alice-2")
        self.assertEqual(other.target_id, "ref-alice")

    def test_ambiguous_mention_preserves_candidates(self):
        result = self.index.resolve_mention_referent("mention-ambiguous")
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertEqual(result.candidate_refs, ())

    def test_unknown_unresolved_and_disputed_identity_states_remain_distinct(self):
        self.assertEqual(self.index.resolve_mention_referent("mention-unknown").status, "UNKNOWN")
        self.assertEqual(self.index.resolve_mention_referent("mention-unresolved").status, "UNRESOLVED")
        self.assertEqual(self.index.resolve_mention_referent("mention-disputed").status, "CONFLICTING")

    def test_context_reference_is_exact_and_parent_path_is_preserved(self):
        result = self.index.resolve_context_path("ctx-fiction")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual([item["id"] for item in result.value["path"]], ["ctx-fiction", "ctx-world"])

    def test_assertion_context_does_not_default_missing_context_ref_to_world(self):
        result = self.index.resolve_assertion_context("assert-no-context-ref")
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertIn("ASSERTION_CONTEXT_REFERENCE_MISSING", result.diagnostics)

    def test_assertion_context_kind_mismatch_is_invalid(self):
        result = self.index.resolve_assertion_context("assert-kind-mismatch")
        self.assertEqual(result.status, "INVALID_INPUT")

    def test_context_parent_cycle_is_invalid(self):
        document = copy.deepcopy(self.document)
        document["contexts"][0]["parentRef"] = "ctx-fiction"
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_context_path("ctx-fiction")
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIn("CONTEXT_PARENT_CYCLE", result.diagnostics)

    def test_scope_path_preserves_nested_operator_and_operand_order(self):
        result = self.index.resolve_scope("expr-root", "expr-direct")
        self.assertEqual(result.status, "RESOLVED")
        self.assertEqual(result.value["path"][0]["operator"], "AND")
        self.assertEqual(result.value["path"][0]["operand_index"], 0)
        quantifier = self.index.resolve_scope("expr-root", "expr-not")
        self.assertEqual(quantifier.status, "RESOLVED")
        self.assertEqual([entry["operator"] for entry in quantifier.value["path"]], ["AND", "QUANTIFIER"])

    def test_shared_expression_with_multiple_scope_paths_is_ambiguous(self):
        result = self.index.resolve_scope("expr-shared-root", "expr-open")
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertEqual(len(result.provenance["scope_paths"]), 2)

    def test_opaque_ancestor_does_not_claim_scope_resolution(self):
        result = self.index.resolve_scope("expr-opaque-root", "expr-open")
        self.assertEqual(result.status, "UNSUPPORTED")

    def test_expression_cycle_is_invalid(self):
        document = copy.deepcopy(self.document)
        document["expressions"][0]["operandRefs"] = ["expr-root"]
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_scope("expr-root", "expr-alice")
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIn("EXPRESSION_GRAPH_CYCLE", result.diagnostics)

    def test_schema_invalid_document_cannot_be_grounded(self):
        document = copy.deepcopy(self.document)
        document["profileId"] = "WRONG"
        index = GroundingIndex(document, SCHEMA)
        result = index.resolve_reference("referent", "ref-alice")
        self.assertEqual(result.status, "INVALID_INPUT")
        self.assertIn("DOCUMENT_SCHEMA_INVALID", result.diagnostics)

    def test_compact_benchmark_adapter_never_defaults_missing_assertion_status(self):
        fixture = {
            "input_snapshot": {
                "profile_id": "USG-SEM/1.0",
                "document_id": "compact-1",
                "semantic_records": {
                    "assertions": [{"id": "assert-compact", "expression_ref": "expr-1", "context_ref": "ctx-1", "epistemic_status": "SOURCE_ASSERTED"}]
                }
            }
        }
        result = inspect_compact_benchmark_snapshot(fixture)
        self.assertEqual(result["mapping_status"], "PARTIAL")
        self.assertFalse(result["canonical_document_ready"])
        self.assertIn("semantic_records.assertions[0].epistemicStatus", result["missing_fields"])
        self.assertIn("assert-compact", result["unmapped_refs"])
        self.assertEqual(result["preserved_snapshot"], fixture["input_snapshot"])


if __name__ == "__main__":
    unittest.main()
