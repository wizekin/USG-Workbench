"""Document-level conditions, exceptions, and exact-scope conflict services."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from tools.scope_aware_rules_v1_0_0 import ScopeAwareRuleAnalyzer
from tools.semantic_evidence_assessment_v1_0_0.assessor import EvidenceAssessmentEngine

PROFILE_ID = "USG-DOCUMENT-ANALYSIS/1.0.0"


class DocumentAnalysisError(ValueError):
    """Raised when a document-analysis task cannot be executed safely."""


class DocumentAnalysisService:
    """Build lossless condition maps and exact-scope contradiction reports."""

    def __init__(self, scope_analyzer=None, evidence_assessor=None):
        self.scope_analyzer = scope_analyzer or ScopeAwareRuleAnalyzer()
        self.evidence_assessor = evidence_assessor or EvidenceAssessmentEngine()

    def conditions(self, document: dict[str, Any]) -> dict[str, Any]:
        scope = self.scope_analyzer.analyze(document)
        if scope["completion_status"] != "COMPLETE":
            return {
                "profile_id": PROFILE_ID,
                "document_id": document.get("documentId"),
                "document_sha256": scope["document_sha256"],
                "completion_status": scope["completion_status"],
                "conditions": [],
                "exceptions": [],
                "negations": [],
                "assertion_bindings": [],
                "diagnostics": scope["diagnostics"],
                "details": scope["details"],
                "safety": self._safety(),
            }

        assertions_by_expression: dict[str, list[str]] = {}
        for binding in scope["assertion_bindings"]:
            assertions_by_expression.setdefault(binding["expression_ref"], []).append(binding["assertion_ref"])

        conditions = []
        exceptions = []
        negations = []
        for frame in scope["operator_frames"]:
            common = {
                "operator_expression_ref": frame["expression_ref"],
                "operator": frame["operator"],
                "scope_status": frame["scope_status"],
                "source_spans": deepcopy(frame["source_spans"]),
                "linked_assertion_refs": sorted(assertions_by_expression.get(frame["expression_ref"], [])),
            }
            if frame["scope_status"] != "STRUCTURE_PRESERVED":
                conditions.append({**common, "status": "UNRESOLVED_OR_UNSUPPORTED", "diagnostics": list(frame["diagnostics"])})
                continue
            if frame.get("conditional_kind") == "IF":
                conditions.append({
                    **common,
                    "kind": "IF",
                    "antecedent_ref": frame["antecedent_ref"],
                    "consequent_ref": frame["consequent_ref"],
                    "status": "CONDITIONAL_STRUCTURE_ONLY",
                    "antecedent_assertion_refs": sorted(assertions_by_expression.get(frame["antecedent_ref"], [])),
                    "consequent_assertion_refs": sorted(assertions_by_expression.get(frame["consequent_ref"], [])),
                })
            elif frame.get("conditional_kind") == "UNLESS":
                item = {
                    **common,
                    "kind": "UNLESS",
                    "consequent_ref": frame["consequent_ref"],
                    "exception_ref": frame["exception_ref"],
                    "status": "CONDITIONAL_STRUCTURE_ONLY",
                    "consequent_assertion_refs": sorted(assertions_by_expression.get(frame["consequent_ref"], [])),
                    "exception_assertion_refs": sorted(assertions_by_expression.get(frame["exception_ref"], [])),
                    "absence_policy": "EXCEPTION_ABSENCE_DOES_NOT_ASSERT_CONSEQUENT",
                }
                conditions.append(item)
                exceptions.append({
                    "operator_expression_ref": frame["expression_ref"],
                    "exception_ref": frame["exception_ref"],
                    "consequent_ref": frame["consequent_ref"],
                    "status": "EXPLICIT_EXCEPTION_LINK",
                    "exception_assertion_refs": item["exception_assertion_refs"],
                })
            elif frame["operator"] == "NOT":
                negations.append({
                    **common,
                    "negated_expression_ref": frame["negated_expression_ref"],
                    "status": "NEGATION_SCOPE_PRESERVED",
                })
        return {
            "profile_id": PROFILE_ID,
            "document_id": scope["document_id"],
            "document_sha256": scope["document_sha256"],
            "completion_status": "COMPLETE",
            "conditions": conditions,
            "exceptions": exceptions,
            "negations": negations,
            "assertion_bindings": deepcopy(scope["assertion_bindings"]),
            "diagnostics": list(scope["diagnostics"]),
            "details": [],
            "safety": self._safety(),
        }

    def contradictions(self, document: dict[str, Any]) -> dict[str, Any]:
        # The evidence assessor owns the exact complement/scope policy. Reuse
        # that tested implementation rather than create a competing matcher.
        task = {
            "task_id": str(document.get("documentId", "document")) + ":phase3-contradictions",
            "assertion_refs": [item["id"] for item in document.get("assertions", [])],
            "evidence_refs": [item["id"] for item in document.get("evidence", [])],
            "relation_refs": [item["id"] for item in document.get("expressionRelations", [])],
            "source_independence_policy": {
                "policy_id": "USG-EVIDENCE-ASSESSMENT",
                "version": "1.0.0",
            },
            "conflict_policy": "EXACT_COMPLEMENT_SAME_SCOPE",
        }
        assessed = self.evidence_assessor.assess(document, task)
        return {
            "profile_id": PROFILE_ID,
            "document_id": assessed["document_id"],
            "document_sha256": assessed["document_sha256"],
            "completion_status": assessed["completion_status"],
            "conflicts": deepcopy(assessed["conflicts"]),
            "evidence_axes": {
                "alignment_assessments": deepcopy(assessed["alignment_assessments"]),
                "semantic_support_assessments": deepcopy(assessed["semantic_support_assessments"]),
                "relation_claims": deepcopy(assessed["relation_claims"]),
                "corroboration_assessments": deepcopy(assessed["corroboration_assessments"]),
                "external_verification": deepcopy(assessed["external_verification"]),
            },
            "diagnostics": list(assessed["diagnostics"]),
            "preserved_input_refs": list(assessed["preserved_input_refs"]),
            "safety": {
                **self._safety(),
                "conflict_winner_selection": False,
                "recency_tiebreak": False,
                "frequency_tiebreak": False,
                "confidence_tiebreak": False,
            },
        }

    def analyze(self, document: dict[str, Any]) -> dict[str, Any]:
        conditions = self.conditions(document)
        contradictions = self.contradictions(document)
        if conditions["document_sha256"] != contradictions["document_sha256"]:
            raise DocumentAnalysisError("analysis snapshot digest mismatch")
        statuses = {conditions["completion_status"], contradictions["completion_status"]}
        completion = "COMPLETE" if statuses == {"COMPLETE"} else (
            "INVALID_INPUT" if "INVALID_INPUT" in statuses else "INCOMPLETE"
        )
        return {
            "profile_id": PROFILE_ID,
            "document_id": document.get("documentId"),
            "document_sha256": conditions["document_sha256"],
            "completion_status": completion,
            "conditions": conditions,
            "contradictions": contradictions,
            "safety": self._safety(),
        }

    @staticmethod
    def _safety():
        return {
            "canonical_document_mutated": False,
            "truth_promotion": False,
            "implicit_closed_world": False,
            "exception_absence_entails_consequent": False,
            "conflict_winner_selection": False,
            "cross_context_conflict": False,
            "cross_attribution_conflict": False,
            "evidence_axes_collapsed": False,
            "semantic_truncation": False,
        }


def extract_conditions(document: dict[str, Any]) -> dict[str, Any]:
    return DocumentAnalysisService().conditions(document)


def inspect_contradictions(document: dict[str, Any]) -> dict[str, Any]:
    return DocumentAnalysisService().contradictions(document)


def analyze_document(document: dict[str, Any]) -> dict[str, Any]:
    return DocumentAnalysisService().analyze(document)
