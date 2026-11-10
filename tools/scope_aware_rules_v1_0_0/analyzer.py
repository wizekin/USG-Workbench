"""Versioned, scope-preserving inspection of NOT, IF, UNLESS, and attribution.

This package describes canonical USG-SEM/1.0 structures. It does not parse
surface text, add canonical fields, infer from absence, or promote truth.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.semantic_grounding_v1_0_0.grounding import GroundingIndex

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"
PROFILE_ID = "USG-SCOPE-AWARE-RULES/1.0.0"


class ScopeAwareRuleError(ValueError):
    """Invalid configuration or malformed scope-aware rule request."""


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw).hexdigest()


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class ScopeAwareRuleAnalyzer:
    """Deterministically inspect supported operator structures without rewriting them."""

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        self.schema = schema if schema is not None else _load_schema()
        Draft202012Validator.check_schema(self.schema)

    def analyze(self, document: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(
            Draft202012Validator(self.schema).iter_errors(document),
            key=lambda error: error.json_path,
        )
        digest = _canonical_hash(document)
        if errors:
            return self._result(
                document, digest, "INVALID_INPUT", [],
                ["DOCUMENT_SCHEMA_INVALID"],
                [{"path": error.json_path, "message": error.message} for error in errors],
            )

        index = GroundingIndex(document)
        if index.validation_errors:
            return self._result(
                document, digest, "INVALID_INPUT", [],
                ["DOCUMENT_GRAPH_INVALID"],
                list(index.validation_errors),
            )

        expressions = {item["id"]: item for item in document.get("expressions", [])}
        frames: list[dict[str, Any]] = []
        diagnostics: set[str] = set()

        # Do not flatten nested operators. Each frame points to the exact
        # canonical child expression IDs in their original order.
        for node in document.get("expressions", []):
            op = node["op"]
            operands = node.get("operandRefs", [])
            if op not in {"NOT", "IMPLIES", "COND", "ATTRIBUTE"}:
                continue

            status = node.get("interpretationStatus", "RESOLVED")
            frame = {
                "expression_ref": node["id"],
                "operator": op,
                "operand_refs": list(operands),
                "interpretation_status": status,
                "source_spans": deepcopy(node.get("annotations", {}).get("spans", [])),
                "scope_status": "STRUCTURE_PRESERVED",
                "diagnostics": [],
            }
            if status != "RESOLVED":
                frame["scope_status"] = "UNRESOLVED"
                frame["diagnostics"].append("OPERATOR_EXPRESSION_NOT_RESOLVED")
                diagnostics.add("OPERATOR_EXPRESSION_NOT_RESOLVED")
                frames.append(frame)
                continue

            if op == "NOT":
                if len(operands) != 1 or operands[0] not in expressions:
                    frame["scope_status"] = "UNSUPPORTED"
                    frame["diagnostics"].append("NOT_SCOPE_ARITY_OR_REFERENCE_UNSUPPORTED")
                    diagnostics.add("NOT_SCOPE_ARITY_OR_REFERENCE_UNSUPPORTED")
                else:
                    frame.update({
                        "polarity": "NEGATED",
                        "negated_expression_ref": operands[0],
                        "scope_boundary": node["id"],
                    })
            elif op == "IMPLIES":
                if len(operands) != 2 or any(ref not in expressions for ref in operands):
                    frame["scope_status"] = "UNSUPPORTED"
                    frame["diagnostics"].append("IF_SCOPE_ARITY_OR_REFERENCE_UNSUPPORTED")
                    diagnostics.add("IF_SCOPE_ARITY_OR_REFERENCE_UNSUPPORTED")
                else:
                    frame.update({
                        "conditional_kind": "IF",
                        "antecedent_ref": operands[0],
                        "consequent_ref": operands[1],
                        "inference_policy": "REQUIRES_SEPARATE_ENABLED_RULE_AND_MATCHED_PREMISES",
                    })
            elif op == "COND":
                # USG-SEM/1.0 intentionally leaves COND's internal parameter
                # vocabulary open. This adapter recognizes only the explicit,
                # versioned mapping documented here; all other shapes abstain.
                params = node.get("params", {})
                if (
                    params.get("conditionalKind") != "UNLESS"
                    or len(operands) != 2
                    or any(ref not in expressions for ref in operands)
                ):
                    frame["scope_status"] = "UNSUPPORTED"
                    frame["diagnostics"].append("UNLESS_REPRESENTATION_UNSUPPORTED")
                    diagnostics.add("UNLESS_REPRESENTATION_UNSUPPORTED")
                else:
                    frame.update({
                        "conditional_kind": "UNLESS",
                        "consequent_ref": operands[0],
                        "exception_ref": operands[1],
                        "equivalent_condition_ref": None,
                        "inference_policy": "CONDITIONAL_ONLY_EXCEPTION_ABSENCE_NEVER_ASSERTS_CONSEQUENT",
                    })
            elif op == "ATTRIBUTE":
                if not operands:
                    frame["scope_status"] = "UNSUPPORTED"
                    frame["diagnostics"].append("ATTRIBUTION_SCOPE_UNSUPPORTED")
                    diagnostics.add("ATTRIBUTION_SCOPE_UNSUPPORTED")
                else:
                    frame.update({
                        "attribution_scope": "EXACT_EXPRESSION_BOUNDARY",
                        "attributed_expression_refs": list(operands),
                        "commitment_transfer": "FORBIDDEN",
                    })
            frames.append(frame)

        bindings = []
        for assertion in document.get("assertions", []):
            context = assertion.get("evaluationContext", {})
            bindings.append({
                "assertion_ref": assertion["id"],
                "expression_ref": assertion["expressionRef"],
                "context_kind": context.get("kind"),
                "context_ref": context.get("contextRef"),
                "commitment": assertion.get("commitment"),
                "attributed_to_ref": assertion.get("attributedToRef"),
                "epistemic_status": assertion.get("epistemicStatus"),
                "binding_policy": "EXACT_MATCH_ONLY",
            })

        return self._result(
            document, digest, "COMPLETE", frames, sorted(diagnostics), [],
            assertion_bindings=bindings,
        )

    @staticmethod
    def _result(document, digest, status, frames, diagnostics, details, assertion_bindings=None):
        return {
            "profile_id": PROFILE_ID,
            "document_id": document.get("documentId"),
            "document_sha256": digest,
            "completion_status": status,
            "operator_frames": frames,
            "assertion_bindings": assertion_bindings or [],
            "diagnostics": diagnostics,
            "details": details,
            "safety": {
                "canonical_document_mutated": False,
                "truth_promotion": False,
                "implicit_closed_world": False,
                "exception_absence_entails_consequent": False,
                "attribution_transfer": False,
                "operator_scope_flattened": False,
                "semantic_truncation": False,
            },
        }


def analyze_scope(document: dict[str, Any]) -> dict[str, Any]:
    return ScopeAwareRuleAnalyzer().analyze(document)
