"""Conservative deterministic evidence and conflict assessment.

This module checks source-span alignment and exact represented-scope conflicts.
It preserves declared support/relation/verification labels as declarations;
it never promotes them to established support, corroboration, verification,
or objective truth.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "rules" / "semantic-reasoning" / "evidence" / "v1.0.0"
POLICY_PATH = POLICY_DIR / "policy.json"
POLICY_SCHEMA_PATH = POLICY_DIR / "policy.schema.json"
TASK_SCHEMA_PATH = POLICY_DIR / "task.schema.json"
RESULT_SCHEMA_PATH = POLICY_DIR / "result.schema.json"
DOCUMENT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"

class EvidenceAssessmentError(ValueError):
    """Raised when task or policy configuration is invalid."""


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def _preserved_refs(document: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    for collection in ("sources", "referents", "mentions", "expressions", "assertions", "evidence", "contexts", "expressionRelations", "unresolvedItems", "derivations"):
        records = document.get(collection, [])
        if isinstance(records, list):
            refs.update(item["id"] for item in records if isinstance(item, dict) and isinstance(item.get("id"), str))
    definitions = document.get("definitions", {})
    if isinstance(definitions, dict):
        for collection in ("concepts", "frames", "roles", "relations"):
            records = definitions.get(collection, [])
            if isinstance(records, list):
                refs.update(item["id"] for item in records if isinstance(item, dict) and isinstance(item.get("id"), str))
    return sorted(refs)


def _declared_support(status: str) -> tuple[str, str]:
    mapping = {
        "NOT_ESTABLISHED": ("NOT_ESTABLISHED", "No semantic support conclusion is established."),
        "PROPOSED": ("PROPOSED_UNVERIFIED", "The source document declares a proposal; it is not independently assessed."),
        "RULE_SUPPORTED": ("DECLARED_RULE_SUPPORTED_UNVERIFIED", "A support label is declared but the assessor does not treat the label as proof."),
        "CORROBORATED": ("DECLARED_CORROBORATED_UNVERIFIED", "A corroboration label is declared but source independence is not established here."),
        "DISPUTED": ("DISPUTED_DECLARED", "The evidence record explicitly declares dispute."),
        "UNKNOWN": ("UNKNOWN", "The evidence support status is explicitly unknown."),
    }
    return mapping.get(status, ("UNKNOWN", "Unrecognized declared support status."))


class EvidenceAssessmentEngine:
    def __init__(self, policy=None, policy_schema=None, task_schema=None, result_schema=None, document_schema=None):
        self.policy = policy if policy is not None else _load(POLICY_PATH)
        self.policy_schema = policy_schema if policy_schema is not None else _load(POLICY_SCHEMA_PATH)
        self.task_schema = task_schema if task_schema is not None else _load(TASK_SCHEMA_PATH)
        self.result_schema = result_schema if result_schema is not None else _load(RESULT_SCHEMA_PATH)
        self.document_schema = document_schema if document_schema is not None else _load(DOCUMENT_SCHEMA_PATH)
        errors = list(Draft202012Validator(self.policy_schema).iter_errors(self.policy))
        if errors:
            raise EvidenceAssessmentError("policy schema invalid: " + "; ".join(e.message for e in errors))
        invariants = self.policy["invariants"]
        if any(value is not False for key, value in invariants.items() if key != "human_review_gate"):
            raise EvidenceAssessmentError("evidence policy safety invariants must remain false")
        if invariants["human_review_gate"] is not False:
            raise EvidenceAssessmentError("human review gate is not part of the policy")

    def assess(self, document: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        task_errors = list(Draft202012Validator(self.task_schema).iter_errors(task))
        if task_errors:
            raise EvidenceAssessmentError("task schema invalid: " + "; ".join(e.message for e in task_errors))
        snapshot_hash = _hash(document)
        doc_errors = list(Draft202012Validator(self.document_schema).iter_errors(document))
        if doc_errors:
            result = self._empty(document, snapshot_hash, "INVALID_INPUT", ["DOCUMENT_SCHEMA_INVALID"])
            result["details"] = [f"{e.json_path}: {e.message}" for e in doc_errors]
            return self._validate_result(result)

        sources = {item["id"]: item for item in document.get("sources", [])}
        expressions = {item["id"]: item for item in document.get("expressions", [])}
        assertions = {item["id"]: item for item in document.get("assertions", [])}
        evidence = {item["id"]: item for item in document.get("evidence", [])}
        relations = {item["id"]: item for item in document.get("expressionRelations", [])}

        assertion_ids = task.get("assertion_refs", list(assertions))
        evidence_ids = task.get("evidence_refs", list(evidence))
        relation_ids = task.get("relation_refs", list(relations))
        diagnostics: list[str] = []
        for kind, ids, index in (("assertion", assertion_ids, assertions), ("evidence", evidence_ids, evidence), ("relation", relation_ids, relations)):
            missing = [item for item in ids if item not in index]
            if missing:
                diagnostics.append(f"{kind.upper()}_REFERENCE_UNRESOLVED")

        alignment = []
        support = []
        for evidence_id in evidence_ids:
            item = evidence.get(evidence_id)
            if item is None:
                continue
            source = sources.get(item.get("sourceRef"))
            if source is None:
                computed = "UNRESOLVED"
                reason = "SOURCE_REFERENCE_NOT_FOUND"
                source_integrity = "UNKNOWN"
            else:
                source_integrity = "NOT_HASHED"
                declared_hash = source.get("textHash")
                if declared_hash:
                    actual_hash = sha256(source["text"].encode("utf-8")).hexdigest()
                    source_integrity = "HASH_MATCH" if actual_hash.lower() == declared_hash.lower() else "HASH_MISMATCH"
                span = item.get("span", {})
                if span.get("sourceRef") != item.get("sourceRef"):
                    computed, reason = "MISMATCH", "EVIDENCE_AND_SPAN_SOURCE_MISMATCH"
                elif source_integrity == "HASH_MISMATCH":
                    computed, reason = "UNVERIFIED", "SOURCE_TEXT_HASH_MISMATCH"
                elif not isinstance(span.get("start"), int) or not isinstance(span.get("end"), int) or span["start"] < 0 or span["end"] <= span["start"] or span["end"] > len(source["text"]):
                    computed, reason = "MISMATCH", "SOURCE_SPAN_OUT_OF_RANGE"
                elif source["text"][span["start"]:span["end"]] == item.get("quote"):
                    computed, reason = "EXACT", "QUOTE_MATCHES_EXACT_UNICODE_CODE_POINT_SPAN"
                else:
                    computed, reason = "MISMATCH", "QUOTE_DOES_NOT_MATCH_DECLARED_SPAN"
            alignment.append({
                "evidence_ref": evidence_id, "source_ref": item.get("sourceRef"),
                "declared_alignment_status": item.get("alignmentStatus"),
                "computed_alignment_status": computed, "source_integrity": source_integrity,
                "diagnostic": reason,
            })
            assessed, explanation = _declared_support(item.get("semanticSupportStatus", "UNKNOWN"))
            support.append({
                "evidence_ref": evidence_id, "source_ref": item.get("sourceRef"),
                "declared_semantic_support_status": item.get("semanticSupportStatus"),
                "assessed_status": assessed, "explanation": explanation,
                "alignment_is_not_support": True,
            })

        relation_claims = []
        for relation_id in relation_ids:
            item = relations.get(relation_id)
            if item is None:
                continue
            declared = item.get("verificationStatus")
            if declared == "DISPUTED":
                assessment = "DISPUTED_DECLARED"
            elif declared == "UNKNOWN":
                assessment = "UNKNOWN"
            else:
                assessment = "UNVERIFIED_RELATION_CLAIM"
            relation_claims.append({
                "relation_ref": relation_id, "relation_type": item.get("type"),
                "source_expression_ref": item.get("sourceExpressionRef"),
                "target_expression_ref": item.get("targetExpressionRef"),
                "declared_verification_status": declared,
                "assessed_status": assessment,
                "relation_label_is_not_proof": True,
            })

        conflicts = self._conflicts(assertion_ids, assertions, expressions, {item["id"]: item for item in document.get("contexts", [])}, {item["id"]: item for item in document.get("referents", [])})
        corroboration = self._corroboration(assertion_ids, assertions, evidence, sources, set(evidence_ids))
        external = [{
            "subject_ref": item["subject_ref"], "verifier_id": item["verifier_id"],
            "procedure_id": item["procedure_id"], "procedure_version": item["procedure_version"],
            "declared_result": item["declared_result"], "record_ref": item["record_ref"],
            "assessed_status": "DECLARED_UNVERIFIED",
            "reason": "No trusted verifier registry or independently executed verification procedure is bound to this task.",
        } for item in task.get("external_verification_declarations", [])]

        result = {
            "profile_id": "USG-EVIDENCE-ASSESSMENT/1.0.0", "completion_status": "COMPLETE",
            "document_id": document.get("documentId"), "document_sha256": snapshot_hash,
            "policy_id": self.policy["policy_id"], "policy_version": self.policy["policy_version"],
            "alignment_assessments": alignment, "semantic_support_assessments": support,
            "relation_claims": relation_claims, "conflicts": conflicts,
            "corroboration_assessments": corroboration, "external_verification": external,
            "diagnostics": sorted(set(diagnostics)), "preserved_input_refs": _preserved_refs(document),
            "safety": {"truth_promotion": False, "semantic_support_from_alignment": False,
                       "corroboration_without_independence": False, "conflict_winner_selection": False,
                       "canonical_document_mutated": False},
        }
        return self._validate_result(result)

    def _conflicts(self, assertion_ids, assertions, expressions, contexts, referents):
        selected = [assertions[item] for item in assertion_ids if item in assertions]
        eligible = [item for item in selected if item.get("epistemicStatus") in {"SOURCE_ASSERTED", "DISPUTED"}]
        negatives = {}
        for expression in expressions.values():
            if expression.get("op") == "NOT" and expression.get("sort") == "PROP" and expression.get("interpretationStatus") == "RESOLVED":
                operands = expression.get("operandRefs", [])
                if len(operands) == 1:
                    negatives.setdefault(operands[0], []).append(expression["id"])
        pairs = []
        seen = set()
        for positive in eligible:
            positive_id = positive.get("expressionRef")
            positive_expression = expressions.get(positive_id)
            if not positive_expression or positive_expression.get("sort") != "PROP" or positive_expression.get("interpretationStatus") != "RESOLVED":
                continue
            negative_ids = negatives.get(positive_id, [])
            for negative in eligible:
                if negative.get("expressionRef") not in negative_ids or positive["id"] == negative["id"]:
                    continue
                left, right = sorted([positive["id"], negative["id"]])
                pair = (left, right)
                if pair in seen:
                    continue
                seen.add(pair)
                pctx, nctx = positive.get("evaluationContext", {}), negative.get("evaluationContext", {})
                same_context = contexts.get(pctx.get("contextRef"))
                same_scope = (
                    same_context is not None
                    and same_context.get("kind") == pctx.get("kind")
                    and pctx.get("kind") == nctx.get("kind")
                    and pctx.get("contextRef") == nctx.get("contextRef")
                    and isinstance(pctx.get("contextRef"), str)
                    and positive.get("commitment") == negative.get("commitment")
                    and positive.get("attributedToRef") == negative.get("attributedToRef")
                    and (positive.get("commitment") != "ATTRIBUTED" or positive.get("attributedToRef") in referents)
                )
                if same_scope:
                    pairs.append({
                        "assertion_refs": [left, right], "status": "CONFLICTING",
                        "basis": "EXACT_DIRECT_NOT_COMPLEMENT_SAME_CONTEXT_AND_ATTRIBUTION",
                        "winner_selection": "FORBIDDEN",
                    })
        return sorted(pairs, key=lambda item: item["assertion_refs"])

    def _corroboration(self, assertion_ids, assertions, evidence, sources, selected_evidence_ids):
        results = []
        for assertion_id in assertion_ids:
            assertion = assertions.get(assertion_id)
            if assertion is None:
                continue
            linked = [evidence[ref] for ref in assertion.get("evidenceRefs", []) if ref in evidence and ref in selected_evidence_ids]
            source_refs = sorted({item.get("sourceRef") for item in linked if isinstance(item.get("sourceRef"), str)})
            if len(source_refs) <= 1:
                diversity = "SINGLE_SOURCE_RECORD" if source_refs else "NO_LINKED_EVIDENCE"
                independence = "NOT_ESTABLISHED"
            else:
                diversity = "MULTIPLE_SOURCE_RECORDS"
                signatures = []
                for ref in source_refs:
                    source = sources.get(ref, {})
                    signature = source.get("textHash") or source.get("uri")
                    if signature:
                        signatures.append(signature)
                independence = "SHARED_OR_POSSIBLY_SHARED_LINEAGE" if len(signatures) != len(set(signatures)) else "NOT_ESTABLISHED"
            results.append({
                "assertion_ref": assertion_id, "source_refs": source_refs,
                "source_diversity": diversity, "source_independence": independence,
                "corroboration_status": "NOT_ESTABLISHED",
                "reason": "Distinct source records or URIs do not by themselves establish independent origin.",
            })
        return results

    def _empty(self, document, snapshot_hash, status, diagnostics):
        return {
            "profile_id": "USG-EVIDENCE-ASSESSMENT/1.0.0", "completion_status": status,
            "document_id": document.get("documentId") if isinstance(document, dict) else None,
            "document_sha256": snapshot_hash, "policy_id": self.policy["policy_id"],
            "policy_version": self.policy["policy_version"], "alignment_assessments": [],
            "semantic_support_assessments": [], "relation_claims": [], "conflicts": [],
            "corroboration_assessments": [], "external_verification": [],
            "diagnostics": diagnostics, "preserved_input_refs": _preserved_refs(document) if isinstance(document, dict) else [],
            "safety": {"truth_promotion": False, "semantic_support_from_alignment": False,
                       "corroboration_without_independence": False, "conflict_winner_selection": False,
                       "canonical_document_mutated": False},
        }

    def _validate_result(self, result):
        errors = list(Draft202012Validator(self.result_schema).iter_errors(result))
        if errors:
            raise EvidenceAssessmentError("result schema invalid: " + "; ".join(e.message for e in errors))
        return result


def assess(document: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return EvidenceAssessmentEngine().assess(document, task)
