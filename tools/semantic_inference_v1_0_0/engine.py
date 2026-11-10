"""Narrow deterministic inference executor for USG-SEM/1.0.

The executor consumes complete canonical documents. It does not parse prose,
invent rules, mutate the input document, chain inferred candidates, assess
evidence, or promote truth. Candidate conclusions remain outside assertions.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex
from tools.semantic_rule_registry_v1_0_0.validator import validate_registry
from tools.semantic_rule_semantics_v1_0_0.validator import validate_semantics

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_DIR = ROOT / "rules" / "semantic-reasoning" / "execution" / "v1.0.0"
ACTIVATION_PATH = EXECUTION_DIR / "activation.json"
ACTIVATION_SCHEMA_PATH = EXECUTION_DIR / "activation.schema.json"
TASK_SCHEMA_PATH = EXECUTION_DIR / "task.schema.json"
REGISTRY_PATH = ROOT / "rules" / "semantic-reasoning" / "v1.0.0" / "registry.json"
SEMANTICS_PATH = ROOT / "rules" / "semantic-reasoning" / "semantics" / "v1.0.0" / "contract.json"
REGISTRY_SCHEMA_PATH = ROOT / "rules" / "semantic-reasoning" / "v1.0.0" / "registry.schema.json"
SEMANTICS_SCHEMA_PATH = ROOT / "rules" / "semantic-reasoning" / "semantics" / "v1.0.0" / "contract.schema.json"

RULE_MP = "benchmark-rule:modus-ponens"
RULE_AND_LEFT = "benchmark-rule:and-elimination-left"
RULES = {RULE_MP, RULE_AND_LEFT}
OUTCOME_ORDER = {
    "INVALID_INPUT": 0, "CONFLICTING": 1, "AMBIGUOUS": 2,
    "UNRESOLVED": 3, "UNKNOWN": 4, "UNSUPPORTED": 5,
    "NOT_APPLICABLE": 6, "APPLICABLE": 7,
}


class InferenceExecutionError(ValueError):
    """Raised when task, activation, registry, or semantics is invalid."""


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _stable_id(prefix: str, value: Any) -> str:
    return prefix + _canonical_hash(value)[:24]


def _expression(index: GroundingIndex, expression_id: str) -> tuple[str, dict[str, Any] | None, tuple[str, ...]]:
    result = index.resolve_record("expression", expression_id)
    if result.status != "RESOLVED":
        return result.status, None, result.diagnostics
    node = result.value
    if node.get("interpretationStatus") == "AMBIGUOUS":
        return "AMBIGUOUS", node, ("RULE_EXPRESSION_AMBIGUOUS",)
    if node.get("interpretationStatus") != "RESOLVED":
        return "UNRESOLVED", node, ("RULE_EXPRESSION_NOT_RESOLVED",)
    if node.get("sort") != "PROP":
        return "UNSUPPORTED", node, ("RULE_EXPRESSION_SORT_UNSUPPORTED",)
    return "RESOLVED", node, ()


def _assertion_eligibility(index: GroundingIndex, assertion: dict[str, Any]) -> tuple[str, dict[str, Any] | None, tuple[str, ...]]:
    status = assertion.get("epistemicStatus")
    if status == "DISPUTED":
        return "CONFLICTING", None, ("RULE_PREMISE_DISPUTED",)
    if status == "UNKNOWN":
        return "UNKNOWN", None, ("RULE_PREMISE_STATUS_UNKNOWN",)
    if status != "SOURCE_ASSERTED":
        return "NOT_APPLICABLE", None, ("RULE_PREMISE_STATUS_NOT_ALLOWED",)

    origin = assertion.get("origin")
    allowed_origins = {"SOURCE_TEXT", "GRAMMATICAL", "BACKGROUND_INFERENCE", "IMPORTED_RESOURCE", "CURATED"}
    if origin == "UNKNOWN" or origin not in allowed_origins:
        return "UNKNOWN", None, ("RULE_PREMISE_ORIGIN_UNKNOWN",)

    expression_status, expression, expression_diagnostics = _expression(index, assertion["expressionRef"])
    if expression_status != "RESOLVED":
        return expression_status, None, expression_diagnostics

    context = index.resolve_assertion_context(assertion["id"])
    if context.status != "RESOLVED":
        return context.status, None, context.diagnostics
    context_id = context.target_id
    context_kind = context.value["context"]["kind"]

    commitment = assertion.get("commitment")
    attributed_to = assertion.get("attributedToRef")
    if commitment == "ATTRIBUTED":
        if not attributed_to:
            return "UNRESOLVED", None, ("RULE_ATTRIBUTION_REFERENCE_MISSING",)
        referent = index.resolve_record("referent", attributed_to)
        if referent.status != "RESOLVED":
            return referent.status, None, referent.diagnostics
    elif commitment not in {"AUTHOR", "NONE"}:
        return "UNSUPPORTED", None, ("RULE_COMMITMENT_UNSUPPORTED",)

    binding = {
        "context_ref": context_id,
        "context_kind": context_kind,
        "commitment": commitment,
        "attributed_to_ref": attributed_to,
    }
    return "RESOLVED", {"assertion": assertion, "expression": expression, "binding": binding}, ()


def _same_binding(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["binding"] == right["binding"]


def _child_expressions_resolved(index: GroundingIndex, node: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    operands = node.get("operandRefs")
    if not isinstance(operands, list) or len(operands) != 2 or not all(isinstance(item, str) for item in operands):
        return "INVALID_INPUT", ("RULE_BINARY_OPERAND_ARITY_INVALID",)
    for operand_id in operands:
        status, _, diagnostics = _expression(index, operand_id)
        if status != "RESOLVED":
            return status, diagnostics
    return "RESOLVED", ()


class InferenceExecutor:
    """Execute only the two separately activated, deterministic v1 rules."""

    def __init__(
        self,
        registry: dict[str, Any] | None = None,
        semantics: dict[str, Any] | None = None,
        activation: dict[str, Any] | None = None,
        activation_schema: dict[str, Any] | None = None,
        task_schema: dict[str, Any] | None = None,
    ):
        self.registry = registry if registry is not None else _load(REGISTRY_PATH)
        self.semantics = semantics if semantics is not None else _load(SEMANTICS_PATH)
        self.activation = activation if activation is not None else _load(ACTIVATION_PATH)
        self.activation_schema = activation_schema if activation_schema is not None else _load(ACTIVATION_SCHEMA_PATH)
        self.task_schema = task_schema if task_schema is not None else _load(TASK_SCHEMA_PATH)
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        errors = sorted(Draft202012Validator(self.activation_schema).iter_errors(self.activation), key=lambda e: e.json_path)
        if errors:
            raise InferenceExecutionError("activation schema: " + "; ".join(f"{e.json_path}: {e.message}" for e in errors))
        task_rule_ids = {rule["rule_id"] for rule in self.registry["rules"]}
        if not RULES.issubset(task_rule_ids):
            raise InferenceExecutionError("required reference rules are missing from the declarative registry")
        validate_registry(self.registry)
        validate_semantics(self.semantics, self.registry)
        if self.activation.get("execution_enabled") is not True:
            raise InferenceExecutionError("separate activation manifest must explicitly enable execution")
        if self.activation.get("registry_id") != self.registry["registry_id"] or self.activation.get("registry_version") != self.registry["registry_version"]:
            raise InferenceExecutionError("activation registry identity/version does not match the declarative registry")
        if self.activation.get("semantics_id") != self.semantics["semantics_id"] or self.activation.get("semantics_version") != self.semantics["semantics_version"]:
            raise InferenceExecutionError("activation semantics identity/version does not match the semantics contract")
        if self.activation.get("rule_model_version") != self.registry["rule_model_version"] or self.activation.get("usg_profile") != self.registry["usg_profile"]:
            raise InferenceExecutionError("activation profile or rule-model version does not match the registry")
        active = {
            item["rule_id"] for item in self.activation["rules"]
            if item["enabled"] is True and item["handler_status"] == "IMPLEMENTED"
        }
        if active != RULES:
            raise InferenceExecutionError("activation manifest must enable exactly the two implemented reference rules")
        if self.registry.get("execution_enabled") is not False:
            raise InferenceExecutionError("declarative registry must remain disabled and immutable")

    def execute(self, document: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        task_errors = sorted(Draft202012Validator(self.task_schema).iter_errors(task), key=lambda e: e.json_path)
        if task_errors:
            raise InferenceExecutionError("task schema: " + "; ".join(f"{e.json_path}: {e.message}" for e in task_errors))
        if document.get("profileId") != "USG-SEM/1.0":
            raise InferenceExecutionError("only complete USG-SEM/1.0 canonical documents are accepted")
        snapshot_hash = _canonical_hash(document)
        index = GroundingIndex(document)
        if index.validation_errors:
            return self._empty_result(document, snapshot_hash, "INVALID_INPUT", ["DOCUMENT_SCHEMA_INVALID"], index.validation_errors)

        requested = task["rule_ids"]
        unsupported = [rule_id for rule_id in requested if rule_id not in RULES]
        if unsupported:
            return self._empty_result(document, snapshot_hash, "UNSUPPORTED", ["RULE_NOT_ENABLED"], unsupported)

        assertions = [item for item in document.get("assertions", []) if isinstance(item, dict)]
        # The source assertion collection is immutable input. Derived candidates
        # are never appended here, preventing inferred-premise chaining.
        eligible: dict[str, tuple[str, dict[str, Any] | None, tuple[str, ...]]] = {
            item["id"]: _assertion_eligibility(index, item) for item in assertions
        }
        budget = task.get("max_rule_applications")
        used = 0
        pending: list[dict[str, Any]] = []
        decisions: list[dict[str, Any]] = []
        candidates: dict[tuple[str, str], dict[str, Any]] = {}
        derivations: list[dict[str, Any]] = []
        diagnostics: list[str] = []

        def consider(rule_id: str, premise_ids: list[str], conclusion_ref: str | None, context_ref: str | None, reason: str | None = None):
            nonlocal used
            if budget is not None and used >= budget:
                pending.append({"rule_id": rule_id, "premise_refs": premise_ids, "conclusion_expression_ref": conclusion_ref})
                return
            used += 1
            if reason:
                decisions.append({"rule_id": rule_id, "premise_refs": premise_ids, "outcome": "NOT_APPLICABLE", "diagnostics": [reason]})
                return
            key = (conclusion_ref or "", context_ref or "")
            derivation_id = _stable_id("DER-", {
                "snapshot": snapshot_hash, "rule_id": rule_id, "version": "1.0.0",
                "premise_refs": premise_ids, "conclusion_expression_ref": conclusion_ref,
                "context_ref": context_ref,
            })
            candidate_id = _stable_id("CAND-", {"expression_ref": conclusion_ref, "context_ref": context_ref})
            derivation = {
                "id": derivation_id, "method": "DETERMINISTIC_RULE",
                "rule_id": rule_id, "rule_version": "1.0.0",
                "input_refs": premise_ids, "output_refs": [candidate_id],
                "status": "DERIVED_NOT_VERIFIED",
                "truth_promotion": False,
                "provenance": {
                    "document_id": document.get("documentId"),
                    "document_sha256": snapshot_hash,
                    "registry_id": self.registry["registry_id"],
                    "registry_version": self.registry["registry_version"],
                    "semantics_id": self.semantics["semantics_id"],
                    "semantics_version": self.semantics["semantics_version"],
                    "activation_id": self.activation["activation_id"],
                    "activation_version": self.activation["activation_version"],
                    "grounding_resolver": "USG-GROUNDING/1.0.0",
                },
            }
            if key not in candidates:
                candidates[key] = {
                    "id": candidate_id, "expression_ref": conclusion_ref,
                    "context_ref": context_ref, "epistemic_effect": "DERIVED_NOT_VERIFIED",
                    "truth_promotion": False, "derivation_ids": [],
                }
            candidates[key]["derivation_ids"].append(derivation_id)
            derivations.append(derivation)
            decisions.append({"rule_id": rule_id, "premise_refs": premise_ids, "outcome": "APPLICABLE", "diagnostics": []})

        by_id = {item["id"]: item for item in assertions}
        if RULE_MP in requested:
            for conditional in assertions:
                c_status, c_data, c_diags = eligible[conditional["id"]]
                if c_status != "RESOLVED":
                    if c_status in {"CONFLICTING", "UNKNOWN", "AMBIGUOUS", "UNRESOLVED", "INVALID_INPUT"}:
                        diagnostics.extend(c_diags)
                    continue
                c_expr = c_data["expression"]
                if c_expr.get("op") != "IMPLIES":
                    continue
                child_status, child_diags = _child_expressions_resolved(index, c_expr)
                if child_status != "RESOLVED":
                    diagnostics.extend(child_diags)
                    continue
                antecedent_ref, consequent_ref = c_expr["operandRefs"]
                for antecedent in assertions:
                    if antecedent["id"] == conditional["id"]:
                        continue
                    a_status, a_data, a_diags = eligible[antecedent["id"]]
                    if a_status != "RESOLVED":
                        if antecedent.get("expressionRef") == antecedent_ref and a_status in {"CONFLICTING", "UNKNOWN", "AMBIGUOUS", "UNRESOLVED", "INVALID_INPUT"}:
                            diagnostics.extend(a_diags)
                        continue
                    if antecedent.get("expressionRef") != antecedent_ref:
                        continue
                    if not _same_binding(a_data, c_data):
                        diagnostics.append("RULE_CONTEXT_OR_ATTRIBUTION_MISMATCH")
                        consider(RULE_MP, [antecedent["id"], conditional["id"]], None, None, "RULE_CONTEXT_OR_ATTRIBUTION_MISMATCH")
                        continue
                    consider(RULE_MP, [antecedent["id"], conditional["id"], c_expr["id"]], consequent_ref, c_data["binding"]["context_ref"])

        if RULE_AND_LEFT in requested:
            for assertion in assertions:
                a_status, a_data, a_diags = eligible[assertion["id"]]
                if a_status != "RESOLVED":
                    continue
                node = a_data["expression"]
                if node.get("op") != "AND":
                    continue
                child_status, child_diags = _child_expressions_resolved(index, node)
                if child_status != "RESOLVED":
                    diagnostics.extend(child_diags)
                    continue
                consider(RULE_AND_LEFT, [assertion["id"], node["id"]], node["operandRefs"][0], a_data["binding"]["context_ref"])

        incomplete = bool(pending)
        if incomplete:
            diagnostics.append("RESOURCE_BUDGET_EXHAUSTED")
        outcome = "INCOMPLETE" if incomplete else "COMPLETE"
        return {
            "profile_id": "USG-INFERENCE/1.0.0",
            "completion_status": outcome,
            "document_id": document.get("documentId"),
            "document_sha256": snapshot_hash,
            "rule_decisions": decisions,
            "conclusion_candidates": sorted(candidates.values(), key=lambda item: item["id"]),
            "derivations": sorted(derivations, key=lambda item: item["id"]),
            "pending_work": pending,
            "diagnostics": sorted(set(diagnostics)),
            "preserved_input_refs": sorted(
                record["id"] for collection in (
                    "sources", "definitions", "referents", "mentions", "expressions",
                    "assertions", "evidence", "contexts", "expressionRelations",
                    "unresolvedItems", "derivations",
                ) for record in document.get(collection, []) if isinstance(record, dict) and isinstance(record.get("id"), str)
            ),
            "resource": {"applications_used": used, "budget": budget, "semantic_truncation": False},
            "safety": {"truth_promotion": False, "inferred_premise_chaining": False, "canonical_document_mutated": False},
        }

    def _empty_result(self, document, snapshot_hash, status, diagnostics, details=None):
        return {
            "profile_id": "USG-INFERENCE/1.0.0", "completion_status": status,
            "document_id": document.get("documentId"), "document_sha256": snapshot_hash,
            "rule_decisions": [], "conclusion_candidates": [], "derivations": [],
            "pending_work": [], "diagnostics": diagnostics, "details": details or [],
            "preserved_input_refs": sorted(
                record["id"] for collection in (
                    "sources", "definitions", "referents", "mentions", "expressions",
                    "assertions", "evidence", "contexts", "expressionRelations",
                    "unresolvedItems", "derivations",
                ) for record in document.get(collection, []) if isinstance(record, dict) and isinstance(record.get("id"), str)
            ),
            "resource": {"applications_used": 0, "budget": None, "semantic_truncation": False},
            "safety": {"truth_promotion": False, "inferred_premise_chaining": False, "canonical_document_mutated": False},
        }


def execute(document: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return InferenceExecutor().execute(document, task)
