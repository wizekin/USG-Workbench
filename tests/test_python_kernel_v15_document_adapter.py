from __future__ import annotations

import hashlib
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _version in ("v0.8.0", "v0.9.0", "v1.0.0", "v1.1.0", "v1.2.0", "v1.3.0", "v1.4.0"):
    sys.path.insert(0, str(ROOT / "implementations/python-kernel" / _version))
sys.path.insert(0, str(ROOT / "implementations/python-kernel/v0.5.0"))

from interoperability.python_adapter.document_v15 import (
    document_to_kernel_v15, kernel_v15_document_to_contract,
)
from interoperability.python_adapter.usg_sem_1 import ContractMappingError
from usg_context_v10 import ContextKind
from usg_expression_relation_v11 import RelationType, VerificationStatus
from usg_unresolved_v12 import UnresolvedStatus
from usg_derivation_v13 import DerivationStatus
from usg_definitions_v14 import SemanticKind
from usg_assertion_v08 import EpistemicStatus
from usg_evidence_v09 import SemanticSupportStatus


class CompleteDocumentAdapterV15Tests(unittest.TestCase):
    def make_document(self):
        source_text = "Alice needs the tool."
        return {
            "profileId": "USG-SEM/1.0",
            "documentId": "phase1:complete-document",
            "sources": [{
                "id": "s:1", "text": source_text, "language": "en",
                "sourceType": "SENTENCE", "trustTier": "STANDARD",
                "sensitivity": "INTERNAL",
                "textHash": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
                "offsetUnit": "unicode_code_point",
            }],
            "primarySourceRef": "s:1",
            "definitions": {
                "grammarVersion": "grammar-1", "ontologyRelease": "ontology-1",
                "concepts": [{
                    "id": "d:concept", "label": "CUSTOMER", "semanticKind": "ENTITY",
                    "version": 1, "definition": "A customer",
                }],
                "frames": [{
                    "id": "d:frame", "label": "NEED", "version": 1,
                    "semanticKind": "STATE", "roles": ["AGENT", "THEME"],
                }],
                "roles": [{"id": "d:role", "label": "AGENT", "constraints": {"kind": "ENTITY"}}],
                "relations": [{"id": "d:relation", "label": "RELATED_TO", "properties": {"symmetric": False}}],
            },
            "referents": [{
                "id": "r:1", "label": "Alice", "semanticKind": "ENTITY",
                "aliases": ["A."], "conceptRefs": ["d:concept"],
                "number": "SINGULAR", "genericity": "SPECIFIC",
                "introducedIn": {"kind": "WORLD"},
                "identity": {
                    "status": "AMBIGUOUS", "scope": "WORKSPACE",
                    "equivalenceRefs": [], "basis": "source mention",
                },
                "sourceRef": "s:1",
                "sourceSpan": {
                    "sourceRef": "s:1", "start": 0, "end": 5,
                    "offsetUnit": "unicode_code_point",
                },
            }],
            "mentions": [{
                "id": "m:1", "surfaceText": "Alice", "resolutionStatus": "LINKED",
                "mentionType": "PROPER_NOUN", "referentRef": "r:1",
                "sourceSpan": {
                    "sourceRef": "s:1", "start": 0, "end": 5,
                    "offsetUnit": "unicode_code_point",
                },
            }],
            "expressions": [
                {"id": "x:alice", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "r:1"}},
                {"id": "x:tool", "op": "REF", "sort": "TERM",
                 "operandRefs": [], "params": {"ref": "tool:1"}},
                {"id": "x:predicate", "op": "PREDICATE_APP", "sort": "SIT",
                 "operandRefs": ["x:alice", "x:tool"],
                 "params": {"predicate": "NEEDS", "roles": ["AGENT", "THEME"]},
                 "semanticKind": "STATE", "interpretationStatus": "RESOLVED"},
                {"id": "x:root", "op": "HOLDS", "sort": "PROP",
                 "operandRefs": ["x:predicate"], "params": {}},
            ],
            "rootExpressionRefs": ["x:root"],
            "assertions": [{
                "id": "a:1", "expressionRef": "x:root", "origin": "SOURCE_TEXT",
                "epistemicStatus": "SOURCE_ASSERTED", "commitment": "ATTRIBUTED",
                "attributedToRef": "r:1",
                "evaluationContext": {"kind": "WORLD", "contextRef": "c:1", "name": "ordinary world"},
                "lifecycleStage": "DISCOVERED", "sourceRef": "s:1",
                "evidenceRefs": ["e:1"], "definitionRef": "d:concept",
            }],
            "evidence": [{
                "id": "e:1", "sourceRef": "s:1",
                "span": {"sourceRef": "s:1", "start": 0, "end": 5,
                         "offsetUnit": "unicode_code_point"},
                "quote": "Alice", "alignmentStatus": "EXACT",
                "semanticSupportStatus": "NOT_ESTABLISHED",
                "supportingRuleRefs": ["rule:2", "rule:1", "rule:2"],
            }],
            "contexts": [{
                "id": "c:1", "kind": "WORLD", "sourceRef": "s:1",
                "agentRef": "r:1", "name": "ordinary world",
            }],
            "expressionRelations": [{
                "id": "rel:1", "type": "SUPPORTS",
                "sourceExpressionRef": "x:root", "targetExpressionRef": "x:root",
                "verificationStatus": "NOT_INDEPENDENTLY_VERIFIED", "evidenceRefs": ["e:1"],
            }],
            "unresolvedItems": [{
                "id": "u:1", "status": "UNRESOLVED", "reason": "Tool referent not resolved",
                "surfaceText": "the tool", "scopeRef": "opaque:scope",
                "scopeLabel": "local clause", "evidenceRefs": ["e:1"],
                "candidateRefs": ["candidate:1"],
            }],
            "derivations": [{
                "id": "d:1", "method": "MODEL_PROPOSAL", "component": "composer",
                "ruleIds": ["rule:1"], "inputRefs": ["x:root"],
                "outputRefs": ["a:1"], "model": {"provider": "local", "name": "test-model"},
                "timestamp": "2026-11-10T06:00:00Z", "status": "PROPOSED",
                "diagnostics": ["candidate proposal"],
            }],
            "validation": {"structuralStatus": "NOT_CHECKED", "checks": [],
                           "validator": "fixture", "contractVersion": "USG-SEM/1.0"},
            "mapping": {"sourceProfile": "fixture", "sourceVersion": "1",
                        "status": "LOSSLESS", "unmappedRefs": []},
            "extensions": {"org.usg.phase1": {"mustSurvive": [1, 2, 3]}},
        }

    def test_every_record_family_receives_its_own_native_adapter(self):
        imported = document_to_kernel_v15(self.make_document(), validate=False)
        self.assertEqual(set(imported.adapters), {
            "sources_expressions", "referents", "mentions", "assertions", "evidence",
            "contexts", "expressionRelations", "unresolvedItems", "derivations", "definitions",
        })
        self.assertIn("r:1", imported.adapters["referents"].referents)
        self.assertIn("m:1", imported.adapters["mentions"].mentions)
        self.assertIn("a:1", imported.adapters["assertions"].assertions)
        self.assertIn("e:1", imported.adapters["evidence"].evidence)
        self.assertIn("c:1", imported.adapters["contexts"].contexts)
        self.assertIn("rel:1", imported.adapters["expressionRelations"].expression_relations)
        self.assertIn("u:1", imported.adapters["unresolvedItems"].unresolved_items)
        self.assertIn("d:1", imported.adapters["derivations"].derivations)
        self.assertEqual(imported.adapters["definitions"].catalogue.concepts[0].semantic_kind,
                         SemanticKind.ENTITY)

    def test_complete_document_round_trip_preserves_all_collections_and_sidecars(self):
        doc = self.make_document()
        imported = document_to_kernel_v15(doc, validate=False)
        out = kernel_v15_document_to_contract(imported, validate=False)
        for collection in (
            "sources", "definitions", "referents", "mentions", "expressions",
            "rootExpressionRefs", "assertions", "evidence", "contexts",
            "expressionRelations", "unresolvedItems", "derivations",
            "validation", "mapping", "extensions",
        ):
            with self.subTest(collection=collection):
                self.assertEqual(out[collection], doc[collection])

    def test_native_edits_from_all_families_compose_without_overwriting_each_other(self):
        doc = self.make_document()
        imported = document_to_kernel_v15(doc, validate=False)
        imported.adapters["referents"].referents["r:1"] = replace(
            imported.adapters["referents"].referents["r:1"], label="ALICE")
        imported.adapters["mentions"].mentions["m:1"] = replace(
            imported.adapters["mentions"].mentions["m:1"], surface_text="ALICE")
        imported.adapters["assertions"].assertions["a:1"] = replace(
            imported.adapters["assertions"].assertions["a:1"],
            epistemic_status=EpistemicStatus.DISPUTED)
        imported.adapters["evidence"].evidence["e:1"] = replace(
            imported.adapters["evidence"].evidence["e:1"],
            semantic_support_status=SemanticSupportStatus.UNKNOWN)
        imported.adapters["contexts"].contexts["c:1"] = replace(
            imported.adapters["contexts"].contexts["c:1"], kind=ContextKind.HYPOTHETICAL)
        imported.adapters["expressionRelations"].expression_relations["rel:1"] = replace(
            imported.adapters["expressionRelations"].expression_relations["rel:1"],
            relation_type=RelationType.ATTACKS,
            verification_status=VerificationStatus.DISPUTED)
        imported.adapters["unresolvedItems"].unresolved_items["u:1"] = replace(
            imported.adapters["unresolvedItems"].unresolved_items["u:1"],
            status=UnresolvedStatus.AMBIGUOUS)
        imported.adapters["derivations"].derivations["d:1"] = replace(
            imported.adapters["derivations"].derivations["d:1"],
            status=DerivationStatus.INCOMPLETE)
        imported.adapters["definitions"].catalogue = replace(
            imported.adapters["definitions"].catalogue,
            concepts=(replace(imported.adapters["definitions"].catalogue.concepts[0],
                              label="CLIENT"),),
        )
        out = kernel_v15_document_to_contract(imported, validate=False)
        self.assertEqual(out["sources"][0]["text"], "Alice needs a tool.")
        self.assertEqual(out["referents"][0]["label"], "ALICE")
        self.assertEqual(out["mentions"][0]["surfaceText"], "ALICE")
        self.assertEqual(out["assertions"][0]["epistemicStatus"], "DISPUTED")
        self.assertEqual(out["evidence"][0]["semanticSupportStatus"], "UNKNOWN")
        self.assertEqual(out["contexts"][0]["kind"], "HYPOTHETICAL")
        self.assertEqual(out["expressionRelations"][0]["type"], "ATTACKS")
        self.assertEqual(out["expressionRelations"][0]["verificationStatus"], "DISPUTED")
        self.assertEqual(out["unresolvedItems"][0]["status"], "AMBIGUOUS")
        self.assertEqual(out["derivations"][0]["status"], "INCOMPLETE")
        self.assertEqual(out["definitions"]["concepts"][0]["label"], "CLIENT")
        self.assertEqual(out["extensions"], doc["extensions"])

    def test_unknown_and_canonical_only_records_survive_composition(self):
        doc = self.make_document()
        doc["contexts"].append({"id": "c:future", "kind": "FUTURE_KIND", "name": "keep"})
        doc["expressionRelations"].append({
            "id": "rel:future", "type": "FUTURE_RELATION",
            "sourceExpressionRef": "x:root", "targetExpressionRef": "x:root",
            "verificationStatus": "UNKNOWN",
        })
        doc["unresolvedItems"][0]["futureField"] = {"keep": True}
        imported = document_to_kernel_v15(doc, validate=False)
        out = kernel_v15_document_to_contract(imported, validate=False)
        self.assertEqual(out["contexts"], doc["contexts"])
        self.assertEqual(out["expressionRelations"], doc["expressionRelations"])
        self.assertEqual(out["unresolvedItems"], doc["unresolvedItems"])
        self.assertEqual(imported.mapping_report["status"], "PARTIAL")

    def test_stale_top_level_snapshot_is_rejected(self):
        imported = document_to_kernel_v15(self.make_document(), validate=False)
        imported.document["mapping"]["status"] = "PARTIAL"
        with self.assertRaises(ContractMappingError):
            kernel_v15_document_to_contract(imported, validate=False)

    def test_cross_family_span_validation_runs_after_composition(self):
        doc = self.make_document()
        doc["mentions"][0]["surfaceText"] = "Alicia"
        imported = document_to_kernel_v15(doc, validate=False)
        with self.assertRaises(ContractMappingError):
            kernel_v15_document_to_contract(imported, validate=True)

    def test_mapping_report_aggregates_native_family_coverage(self):
        imported = document_to_kernel_v15(self.make_document(), validate=False)
        self.assertIn("sources", imported.record_mapping)
        self.assertIn("expressions", imported.record_mapping)
        self.assertIn("concepts", imported.record_mapping)
        self.assertIn("frames", imported.record_mapping)
        self.assertEqual(imported.mapping_report["targetVersion"], "1.5.0")
        self.assertIn("familyReports", imported.mapping_report)

    def test_wrong_profile_and_non_mapping_input_are_rejected(self):
        doc = self.make_document()
        doc["profileId"] = "USG-SEM/2.0"
        with self.assertRaises(ContractMappingError):
            document_to_kernel_v15(doc, validate=False)
        with self.assertRaises(TypeError):
            document_to_kernel_v15([], validate=False)


if __name__ == "__main__":
    unittest.main()
