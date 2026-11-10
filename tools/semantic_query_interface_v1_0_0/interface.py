"""Exact-reference query orchestration and deterministic structured explanations."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_inference_v1_0_0.engine import InferenceExecutor
from tools.semantic_evidence_assessment_v1_0_0.assessor import EvidenceAssessmentEngine

ROOT = Path(__file__).resolve().parents[2]
QUERY_DIR = ROOT / "rules" / "semantic-reasoning" / "query" / "v1.0.0"


class QueryInterfaceError(ValueError):
    """Raised when the query contract itself is invalid."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


class QueryInterface:
    def __init__(self, query_schema=None, result_schema=None, inference_executor=None, evidence_assessor=None):
        self.query_schema = query_schema if query_schema is not None else _load(QUERY_DIR / "query.schema.json")
        self.result_schema = result_schema if result_schema is not None else _load(QUERY_DIR / "result.schema.json")
        self.inference_executor = inference_executor if inference_executor is not None else InferenceExecutor()
        self.evidence_assessor = evidence_assessor if evidence_assessor is not None else EvidenceAssessmentEngine()

    def run(self, document: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
        errors = list(Draft202012Validator(self.query_schema).iter_errors(query))
        if errors:
            raise QueryInterfaceError("query schema invalid: " + "; ".join(e.message for e in errors))
        snapshot = _hash(document)
        index = GroundingIndex(document)
        if index.validation_errors:
            return self._early(query, document, snapshot, "INVALID_INPUT", "UNSUPPORTED",
                               ["DOCUMENT_SCHEMA_INVALID"], ["Canonical document failed USG-SEM/1.0 validation."])

        goal = query["goal"]
        expression_result = index.resolve_record("expression", goal["expression_ref"])
        if expression_result.status != "RESOLVED":
            status = "UNRESOLVED" if expression_result.status == "UNRESOLVED" else "INVALID_INPUT"
            return self._early(query, document, snapshot, status, status,
                               list(expression_result.diagnostics), [])
        expression = expression_result.value
        if expression.get("interpretationStatus") == "AMBIGUOUS":
            return self._early(query, document, snapshot, "AMBIGUOUS", "AMBIGUOUS", ["QUERY_GOAL_AMBIGUOUS"], [])
        if expression.get("interpretationStatus") != "RESOLVED":
            return self._early(query, document, snapshot, "UNRESOLVED", "UNRESOLVED", ["QUERY_GOAL_NOT_RESOLVED"], [])
        if expression.get("sort") != "PROP":
            return self._early(query, document, snapshot, "UNSUPPORTED", "UNSUPPORTED", ["QUERY_GOAL_SORT_UNSUPPORTED"], [])

        context_result = index.resolve_record("context", goal["context_ref"])
        if context_result.status != "RESOLVED":
            status = "UNRESOLVED" if context_result.status == "UNRESOLVED" else "INVALID_INPUT"
            return self._early(query, document, snapshot, status, status, list(context_result.diagnostics), [])
        if context_result.value.get("kind") != goal["context_kind"]:
            return self._early(query, document, snapshot, "INVALID_INPUT", "UNSUPPORTED", ["QUERY_CONTEXT_KIND_MISMATCH"], [])

        if goal["commitment"] == "ATTRIBUTED":
            referent = index.resolve_record("referent", goal["attributed_to_ref"])
            if referent.status != "RESOLVED":
                status = "UNRESOLVED" if referent.status == "UNRESOLVED" else "INVALID_INPUT"
                return self._early(query, document, snapshot, status, status, list(referent.diagnostics), [])

        assertions = {item["id"]: item for item in document.get("assertions", [])}
        def binding_matches(assertion):
            context = assertion.get("evaluationContext", {})
            return (
                context.get("contextRef") == goal["context_ref"]
                and context.get("kind") == goal["context_kind"]
                and assertion.get("commitment") == goal["commitment"]
                and assertion.get("attributedToRef") == goal.get("attributed_to_ref")
            )

        scope_assertions = [item for item in assertions.values() if binding_matches(item)]
        goal_assertions = [item for item in scope_assertions if item.get("expressionRef") == goal["expression_ref"]]
        inference = self.inference_executor.execute(document, query["inference_task"])
        if inference["completion_status"] == "INVALID_INPUT":
            return self._early(query, document, snapshot, "INVALID_INPUT", "UNSUPPORTED",
                               inference.get("diagnostics", []), [])

        scope_ids = sorted(item["id"] for item in scope_assertions)
        premise_ids = set()
        matching_derivations = []
        candidates_by_id = {item["id"]: item for item in inference.get("conclusion_candidates", [])}
        matching_candidates = {}
        for derivation in inference.get("derivations", []):
            candidate_refs = derivation.get("output_refs", [])
            matching_premises = [ref for ref in derivation.get("input_refs", []) if ref in assertions]
            if not matching_premises:
                continue
            if not all(binding_matches(assertions[ref]) for ref in matching_premises):
                continue
            for candidate_ref in candidate_refs:
                candidate = candidates_by_id.get(candidate_ref)
                if candidate and candidate.get("expression_ref") == goal["expression_ref"] and candidate.get("context_ref") == goal["context_ref"]:
                    matching_derivations.append(derivation)
                    premise_ids.update(matching_premises)
                    matching_candidates[candidate_ref] = candidate

        evidence_assertion_ids = sorted(set(scope_ids) | premise_ids)
        evidence_refs = sorted({
            evidence_ref for assertion_id in evidence_assertion_ids
            for evidence_ref in assertions[assertion_id].get("evidenceRefs", [])
        })
        relation_ids = sorted(
            item["id"] for item in document.get("expressionRelations", [])
            if item.get("sourceExpressionRef") == goal["expression_ref"]
            or item.get("targetExpressionRef") == goal["expression_ref"]
        )
        evidence_task = {
            "task_id": query["query_id"] + ":evidence",
            "assertion_refs": evidence_assertion_ids,
            "evidence_refs": evidence_refs,
            "relation_refs": relation_ids,
            "source_independence_policy": {"policy_id": "USG-EVIDENCE-ASSESSMENT", "version": "1.0.0"},
            "conflict_policy": "EXACT_COMPLEMENT_SAME_SCOPE",
        }
        evidence_result = self.evidence_assessor.assess(document, evidence_task)
        goal_ids = {item["id"] for item in goal_assertions}
        conflicts = [
            item for item in evidence_result["conflicts"]
            if goal_ids.intersection(item["assertion_refs"])
        ]
        relation_claims = evidence_result["relation_claims"]
        diagnostics = list(inference.get("diagnostics", [])) + list(evidence_result.get("diagnostics", []))
        statuses = {item.get("epistemicStatus") for item in goal_assertions}
        if conflicts:
            goal_status = "CONFLICTING"
        elif "DISPUTED" in statuses:
            goal_status = "DISPUTED"
        elif "SOURCE_ASSERTED" in statuses:
            goal_status = "SOURCE_ASSERTED_NOT_VERIFIED"
        elif matching_candidates:
            goal_status = "DERIVED_NOT_VERIFIED"
        elif "UNKNOWN" in statuses:
            goal_status = "UNKNOWN"
        elif completion == "UNSUPPORTED":
            goal_status = "UNSUPPORTED"
        else:
            goal_status = "NOT_ESTABLISHED"

        completion = inference.get("completion_status", "COMPLETE")
        if completion not in {"COMPLETE", "INCOMPLETE", "UNSUPPORTED"}:
            completion = "UNSUPPORTED"
        unresolved = []
        if not goal_assertions and not matching_candidates:
            unresolved.append({"code":"NO_EXACT_ASSERTION_OR_DERIVATION_MATCH","meaning":"No exact result is established; absence is not negation under the open-world policy."})
        for item in goal_assertions:
            if item.get("epistemicStatus") == "UNKNOWN":
                unresolved.append({"code":"GOAL_ASSERTION_UNKNOWN","assertion_ref":item["id"]})
        for item in evidence_result["alignment_assessments"]:
            if item["computed_alignment_status"] in {"UNRESOLVED","UNVERIFIED","MISMATCH"}:
                unresolved.append({"code":"EVIDENCE_ALIGNMENT_"+item["computed_alignment_status"],"evidence_ref":item["evidence_ref"]})
        unsupported = []
        if completion == "UNSUPPORTED":
            unsupported.append({"code":"INFERENCE_RULE_UNSUPPORTED","diagnostics":inference.get("diagnostics", [])})
        if inference.get("completion_status") == "INCOMPLETE":
            unresolved.append({"code":"INFERENCE_INCOMPLETE","pending_work":inference.get("pending_work", [])})

        explanation = [
            {"step":1,"code":"GOAL_GROUNDED","status":"RESOLVED","input_refs":[goal["expression_ref"],goal["context_ref"]],"output_refs":[goal["expression_ref"]]},
            {"step":2,"code":"EXACT_SOURCE_ASSERTION_MATCH","status":"MATCHED" if goal_assertions else "NO_MATCH","input_refs":[goal["expression_ref"]],"output_refs":sorted(goal_ids)},
            {"step":3,"code":"DETERMINISTIC_INFERENCE","status":inference.get("completion_status"),"input_refs":sorted(premise_ids),"output_refs":sorted(matching_candidates)},
            {"step":4,"code":"EVIDENCE_AND_CONFLICT_ASSESSMENT","status":"COMPLETE","input_refs":evidence_assertion_ids,"output_refs":[item["evidence_ref"] for item in evidence_result["alignment_assessments"]]},
            {"step":5,"code":"QUERY_CONCLUSION","status":goal_status,"input_refs":sorted(goal_ids | premise_ids),"output_refs":sorted(matching_candidates)},
        ]
        result = {
            "profile_id":"USG-QUERY/1.0.0","query_id":query["query_id"],
            "document_id":document.get("documentId"),"document_sha256":snapshot,
            "completion_status":completion,"goal_status":goal_status,
            "goal":goal,
            "source_assertions":[{"assertion_ref":item["id"],"epistemic_status":item.get("epistemicStatus"),"origin":item.get("origin"),"evidence_refs":item.get("evidenceRefs",[])} for item in goal_assertions],
            "scope_assertions":[{"assertion_ref":item["id"],"expression_ref":item.get("expressionRef"),"epistemic_status":item.get("epistemicStatus"),"origin":item.get("origin")} for item in scope_assertions],
            "inference_candidates":sorted(matching_candidates.values(),key=lambda item:item["id"]),
            "derivations":sorted(matching_derivations,key=lambda item:item["id"]),
            "evidence_assessment":evidence_result,"conflicts":conflicts,
            "relation_claims":relation_claims,"unresolved_questions":unresolved,
            "unsupported_portions":unsupported,"explanation":explanation,
            "diagnostics":sorted(set(diagnostics)),
            "safety":{"truth_promotion":False,"absence_means_false":False,"free_text_inference":False,
                      "inferred_premise_chaining":False,"canonical_document_mutated":False},
        }
        errors = list(Draft202012Validator(self.result_schema).iter_errors(result))
        if errors:
            raise QueryInterfaceError("query result schema invalid: " + "; ".join(e.message for e in errors))
        return result

    def _early(self, query, document, snapshot, completion, goal_status, diagnostics, details):
        result = {
            "profile_id":"USG-QUERY/1.0.0","query_id":query["query_id"],
            "document_id":document.get("documentId") if isinstance(document,dict) else None,
            "document_sha256":snapshot,"completion_status":completion,"goal_status":goal_status,
            "goal":query["goal"],"source_assertions":[],"scope_assertions":[],
            "inference_candidates":[],"derivations":[],"evidence_assessment":None,
            "conflicts":[],"relation_claims":[],"unresolved_questions":[{"code":"GOAL_RESOLUTION_DETAIL","detail":item} for item in details],
            "unsupported_portions":[],"explanation":[{"step":1,"code":"GOAL_RESOLUTION","status":completion,"input_refs":[query["goal"]["expression_ref"]],"output_refs":[]}],
            "diagnostics":sorted(set(diagnostics)),
            "safety":{"truth_promotion":False,"absence_means_false":False,"free_text_inference":False,
                      "inferred_premise_chaining":False,"canonical_document_mutated":False},
        }
        errors=list(Draft202012Validator(self.result_schema).iter_errors(result))
        if errors:
            raise QueryInterfaceError("early query result schema invalid: "+ "; ".join(e.message for e in errors))
        return result


def run_query(document: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    return QueryInterface().run(document, query)
