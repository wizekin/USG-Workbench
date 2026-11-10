"""Deterministic grounding services for USG-SEM/1.0.

This module resolves explicit typed references and scope paths only. It does
not infer coreference, select definitions by labels, execute rules, or promote
assertions. All outputs are deterministic for the same document snapshot.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Optional

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = ROOT / "specifications" / "usg-sem-1.0.schema.json"

_RECORD_COLLECTIONS = {
    "source": ("sources",),
    "referent": ("referents",),
    "mention": ("mentions",),
    "expression": ("expressions",),
    "assertion": ("assertions",),
    "evidence": ("evidence",),
    "context": ("contexts",),
    "expression_relation": ("expressionRelations",),
    "unresolved_item": ("unresolvedItems",),
    "derivation": ("derivations",),
    "concept": ("definitions", "concepts"),
    "frame": ("definitions", "frames"),
    "role": ("definitions", "roles"),
    "relation": ("definitions", "relations"),
}

_DEFINITION_TYPES = {"concept", "frame", "role", "relation"}


@dataclass(frozen=True)
class ResolutionResult:
    status: str
    target_type: str
    target_id: Optional[str] = None
    value: Any = None
    candidate_refs: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    provenance: Optional[dict[str, Any]] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "value": deepcopy(self.value),
            "candidate_refs": list(self.candidate_refs),
            "diagnostics": list(self.diagnostics),
            "provenance": deepcopy(self.provenance or {}),
        }


def _nested(document: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = document
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


class GroundingIndex:
    """Immutable-snapshot indexes for deterministic typed reference grounding."""

    def __init__(self, document: dict[str, Any], schema: Optional[dict[str, Any]] = None):
        self.document = deepcopy(document)
        if schema is None:
            with DEFAULT_SCHEMA.open("r", encoding="utf-8") as stream:
                schema = json.load(stream)
        self.schema = schema
        errors = sorted(
            Draft202012Validator(schema).iter_errors(self.document),
            key=lambda error: error.json_path,
        )
        self.validation_errors = tuple(
            f"{error.json_path}: {error.message}" for error in errors
        )
        self._indexes: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for record_type, path in _RECORD_COLLECTIONS.items():
            records = _nested(self.document, path)
            if not isinstance(records, list):
                records = []
            index: dict[str, list[dict[str, Any]]] = {}
            for record in records:
                if isinstance(record, dict) and isinstance(record.get("id"), str):
                    index.setdefault(record["id"], []).append(record)
            self._indexes[record_type] = index

    @property
    def document_id(self) -> Optional[str]:
        value = self.document.get("documentId")
        return value if isinstance(value, str) else None

    def _result(
        self,
        status: str,
        target_type: str,
        target_id: Optional[str] = None,
        value: Any = None,
        candidates: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
        extra_provenance: Optional[dict[str, Any]] = None,
    ) -> ResolutionResult:
        provenance = {
            "profile_id": self.document.get("profileId"),
            "document_id": self.document_id,
            "resolver": "USG-GROUNDING/1.0.0",
            "snapshot_identity": self.document_id,
        }
        if extra_provenance:
            provenance.update(extra_provenance)
        return ResolutionResult(
            status=status,
            target_type=target_type,
            target_id=target_id,
            value=deepcopy(value),
            candidate_refs=candidates,
            diagnostics=diagnostics,
            provenance=provenance,
        )

    def _other_type_matches(self, record_type: str, record_id: str) -> list[str]:
        return sorted(
            kind for kind, index in self._indexes.items()
            if kind != record_type and record_id in index
        )

    def resolve_record(self, record_type: str, record_id: str) -> ResolutionResult:
        """Resolve an exact typed record ID; never search by label or coerce type."""
        if self.validation_errors:
            return self._result(
                "INVALID_INPUT", record_type, record_id,
                diagnostics=("DOCUMENT_SCHEMA_INVALID",),
                extra_provenance={"schema_errors": list(self.validation_errors)},
            )
        if record_type not in _RECORD_COLLECTIONS:
            return self._result("UNSUPPORTED", record_type, record_id, diagnostics=("RECORD_TYPE_UNSUPPORTED",))
        if not isinstance(record_id, str) or not record_id:
            return self._result("INVALID_INPUT", record_type, diagnostics=("REFERENCE_ID_INVALID",))
        matches = self._indexes[record_type].get(record_id, [])
        if len(matches) > 1:
            return self._result("INVALID_INPUT", record_type, record_id, candidates=(record_id,), diagnostics=("DUPLICATE_RECORD_ID",))
        if not matches:
            other_types = self._other_type_matches(record_type, record_id)
            if other_types:
                return self._result(
                    "INVALID_INPUT", record_type, record_id,
                    diagnostics=("REFERENCE_TARGET_TYPE_MISMATCH",),
                    extra_provenance={"found_under_record_types": other_types},
                )
            return self._result("UNRESOLVED", record_type, record_id, diagnostics=("REFERENCE_NOT_FOUND",))
        path = _RECORD_COLLECTIONS[record_type]
        return self._result(
            "RESOLVED", record_type, record_id, matches[0],
            extra_provenance={"collection_path": list(path)},
        )

    def resolve_reference(self, expected_type: str, reference_id: str) -> ResolutionResult:
        """Explicitly typed reference API; expected_type is mandatory."""
        return self.resolve_record(expected_type, reference_id)

    def resolve_definition(
        self,
        definition_type: str,
        definition_id: str,
        version: Optional[int] = None,
        catalogue_scope: Optional[str] = None,
        catalogue_version: Optional[str] = None,
    ) -> ResolutionResult:
        """Resolve definition identity/version exactly.

        Concept and frame definitions carry record-level positive integer versions.
        Role and relation definitions do not; those require an explicit matching
        catalogue version (ONTOLOGY or GRAMMAR) when versioned grounding is required.
        """
        if definition_type not in _DEFINITION_TYPES:
            return self._result("UNSUPPORTED", definition_type, definition_id, diagnostics=("DEFINITION_TYPE_UNSUPPORTED",))
        base = self.resolve_record(definition_type, definition_id)
        if base.status != "RESOLVED":
            return base
        record = base.value
        if definition_type in {"concept", "frame"}:
            if version is None or isinstance(version, bool) or not isinstance(version, int) or version < 1:
                return self._result("UNRESOLVED", definition_type, definition_id, candidates=(definition_id,), diagnostics=("DEFINITION_VERSION_REQUIRED",))
            if record.get("version") != version:
                return self._result(
                    "UNRESOLVED", definition_type, definition_id,
                    candidates=(definition_id,), diagnostics=("DEFINITION_VERSION_NOT_FOUND",),
                    extra_provenance={"requested_version": version, "available_version": record.get("version")},
                )
            if catalogue_scope is not None:
                catalogue = self.document.get("definitions", {})
                field = {"ONTOLOGY": "ontologyRelease", "GRAMMAR": "grammarVersion"}.get(catalogue_scope)
                if field is None:
                    return self._result("INVALID_INPUT", definition_type, definition_id, diagnostics=("CATALOGUE_SCOPE_INVALID",))
                if not catalogue_version or catalogue.get(field) != catalogue_version:
                    return self._result(
                        "UNRESOLVED", definition_type, definition_id,
                        candidates=(definition_id,), diagnostics=("CATALOGUE_VERSION_NOT_FOUND",),
                        extra_provenance={"catalogue_scope": catalogue_scope, "requested_catalogue_version": catalogue_version},
                    )
            return self._result(
                "RESOLVED", definition_type, definition_id, record,
                extra_provenance={"record_version": version, "catalogue_scope": catalogue_scope, "catalogue_version": catalogue_version},
            )

        if version is not None:
            return self._result(
                "UNSUPPORTED", definition_type, definition_id,
                candidates=(definition_id,), diagnostics=("DEFINITION_RECORD_HAS_NO_VERSION_FIELD",),
            )
        if catalogue_scope not in {"ONTOLOGY", "GRAMMAR"} or not catalogue_version:
            return self._result(
                "UNRESOLVED", definition_type, definition_id,
                candidates=(definition_id,), diagnostics=("DEFINITION_CATALOGUE_VERSION_REQUIRED",),
            )
        catalogue = self.document.get("definitions", {})
        field = "ontologyRelease" if catalogue_scope == "ONTOLOGY" else "grammarVersion"
        if catalogue.get(field) != catalogue_version:
            return self._result(
                "UNRESOLVED", definition_type, definition_id,
                candidates=(definition_id,), diagnostics=("CATALOGUE_VERSION_NOT_FOUND",),
                extra_provenance={"catalogue_scope": catalogue_scope, "requested_catalogue_version": catalogue_version},
            )
        return self._result(
            "RESOLVED", definition_type, definition_id, record,
            extra_provenance={"catalogue_scope": catalogue_scope, "catalogue_version": catalogue_version, "record_level_version": None},
        )

    def find_definition_candidates_by_label(self, definition_type: str, label: str) -> ResolutionResult:
        """Return label candidates for inspection; a label can never resolve identity."""
        if definition_type not in _DEFINITION_TYPES:
            return self._result("UNSUPPORTED", definition_type, diagnostics=("DEFINITION_TYPE_UNSUPPORTED",))
        if not isinstance(label, str) or not label:
            return self._result("INVALID_INPUT", definition_type, diagnostics=("DEFINITION_LABEL_INVALID",))
        records = _nested(self.document, _RECORD_COLLECTIONS[definition_type]) or []
        candidates = tuple(
            record["id"] for record in records
            if isinstance(record, dict) and record.get("label") == label and isinstance(record.get("id"), str)
        )
        if not candidates:
            return self._result("UNRESOLVED", definition_type, diagnostics=("DEFINITION_LABEL_NOT_FOUND",))
        if len(candidates) > 1:
            return self._result("AMBIGUOUS", definition_type, candidates=candidates, diagnostics=("AMBIGUOUS_DEFINITION",))
        return self._result(
            "UNRESOLVED", definition_type, candidates=candidates,
            diagnostics=("DEFINITION_LABEL_IS_NOT_IDENTITY",),
        )

    def resolve_mention_referent(self, mention_id: str) -> ResolutionResult:
        mention_result = self.resolve_record("mention", mention_id)
        if mention_result.status != "RESOLVED":
            return mention_result
        mention = mention_result.value
        state = mention.get("resolutionStatus")
        if state == "UNKNOWN":
            return self._result("UNKNOWN", "referent", diagnostics=("MENTION_RESOLUTION_UNKNOWN",), extra_provenance={"mention_id": mention_id})
        if state == "AMBIGUOUS":
            unresolved = self._find_unresolved_item_for_scope(mention_id)
            candidates = tuple(unresolved.get("candidateRefs", [])) if unresolved else ()
            return self._result("AMBIGUOUS", "referent", candidates=candidates, diagnostics=("MENTION_RESOLUTION_AMBIGUOUS",), extra_provenance={"mention_id": mention_id})
        if state == "UNRESOLVED":
            return self._result("UNRESOLVED", "referent", diagnostics=("MENTION_REFERENT_UNRESOLVED",), extra_provenance={"mention_id": mention_id})
        if state not in {"LINKED", "RESOLVED"}:
            return self._result("UNSUPPORTED", "referent", diagnostics=("MENTION_RESOLUTION_STATUS_UNSUPPORTED",))
        referent_id = mention.get("referentRef")
        if not referent_id:
            return self._result("UNRESOLVED", "referent", diagnostics=("MENTION_REFERENT_LINK_MISSING",), extra_provenance={"mention_id": mention_id})
        referent_result = self.resolve_record("referent", referent_id)
        if referent_result.status != "RESOLVED":
            return referent_result
        identity = referent_result.value.get("identity") or {}
        identity_status = identity.get("status")
        mapped = {
            "AMBIGUOUS": "AMBIGUOUS",
            "UNRESOLVED": "UNRESOLVED",
            "DISPUTED": "CONFLICTING",
            "UNKNOWN": "UNKNOWN",
            "PROVISIONAL": "UNRESOLVED",
        }
        if identity_status in mapped:
            return self._result(
                mapped[identity_status], "referent", referent_id,
                referent_result.value, candidates=(referent_id,),
                diagnostics=(f"REFERENT_IDENTITY_{identity_status}",),
                extra_provenance={"mention_id": mention_id},
            )
        return self._result(
            "RESOLVED", "referent", referent_id, referent_result.value,
            extra_provenance={"mention_id": mention_id, "mention_resolution_status": state},
        )

    def _find_unresolved_item_for_scope(self, scope_id: str) -> Optional[dict[str, Any]]:
        items = (self.document.get("unresolvedItems") or [])
        matches = [item for item in items if item.get("scopeRef") == scope_id or item.get("id") == scope_id]
        return matches[0] if len(matches) == 1 else None

    def resolve_assertion_context(self, assertion_id: str) -> ResolutionResult:
        assertion_result = self.resolve_record("assertion", assertion_id)
        if assertion_result.status != "RESOLVED":
            return assertion_result
        evaluation = assertion_result.value.get("evaluationContext") or {}
        kind = evaluation.get("kind")
        if kind == "UNKNOWN":
            return self._result("UNKNOWN", "context", diagnostics=("ASSERTION_CONTEXT_UNKNOWN",), extra_provenance={"assertion_id": assertion_id})
        context_id = evaluation.get("contextRef")
        if not context_id:
            return self._result(
                "UNRESOLVED", "context", diagnostics=("ASSERTION_CONTEXT_REFERENCE_MISSING",),
                extra_provenance={"assertion_id": assertion_id, "declared_context_kind": kind},
            )
        context_result = self.resolve_context_path(context_id)
        if context_result.status != "RESOLVED":
            return context_result
        if context_result.value["context"]["kind"] != kind:
            return self._result(
                "INVALID_INPUT", "context", context_id,
                diagnostics=("ASSERTION_CONTEXT_KIND_MISMATCH",),
                extra_provenance={"assertion_id": assertion_id, "declared_context_kind": kind},
            )
        return self._result(
            "RESOLVED", "context", context_id, context_result.value,
            extra_provenance={"assertion_id": assertion_id},
        )

    def resolve_context_path(self, context_id: str) -> ResolutionResult:
        if self.validation_errors:
            return self._result("INVALID_INPUT", "context", context_id, diagnostics=("DOCUMENT_SCHEMA_INVALID",))
        path: list[dict[str, Any]] = []
        visited: set[str] = set()
        current = context_id
        while current:
            if current in visited:
                return self._result("INVALID_INPUT", "context", context_id, diagnostics=("CONTEXT_PARENT_CYCLE",), extra_provenance={"visited": list(path)})
            visited.add(current)
            result = self.resolve_record("context", current)
            if result.status != "RESOLVED":
                return self._result(result.status, "context", context_id, candidates=result.candidate_refs, diagnostics=result.diagnostics, extra_provenance={"context_path": path})
            context = result.value
            path.append({"id": context["id"], "kind": context["kind"], "parentRef": context.get("parentRef")})
            if context["kind"] == "UNKNOWN":
                return self._result("UNKNOWN", "context", context_id, {"path": path}, diagnostics=("CONTEXT_KIND_UNKNOWN",))
            current = context.get("parentRef")
        return self._result("RESOLVED", "context", context_id, {"context": path[0], "path": path})

    def resolve_scope(self, root_expression_id: str, target_expression_id: str) -> ResolutionResult:
        """Return every exact ordered operand path from root to target.

        A shared subexpression with multiple parent paths is AMBIGUOUS unless
        the caller supplies a narrower root. Opaque nodes are not traversed.
        """
        if self.validation_errors:
            return self._result("INVALID_INPUT", "expression_scope", target_expression_id, diagnostics=("DOCUMENT_SCHEMA_INVALID",))
        root_result = self.resolve_record("expression", root_expression_id)
        if root_result.status != "RESOLVED":
            return root_result
        target_result = self.resolve_record("expression", target_expression_id)
        if target_result.status != "RESOLVED":
            return target_result

        paths: list[list[dict[str, Any]]] = []
        cycle: list[str] = []
        dangling: list[str] = []
        blocked: list[str] = []
        stack: list[str] = []

        def walk(current_id: str, current_path: list[dict[str, Any]]) -> None:
            if current_id in stack:
                cycle.append(current_id)
                return
            node_result = self.resolve_record("expression", current_id)
            if node_result.status != "RESOLVED":
                dangling.append(current_id)
                return
            node = node_result.value
            if current_id == target_expression_id:
                paths.append(deepcopy(current_path))
                return
            if node.get("op") == "OPAQUE":
                blocked.append(current_id)
                return
            stack.append(current_id)
            operands = node.get("operandRefs", [])
            for index, child_id in enumerate(operands):
                child_result = self.resolve_record("expression", child_id)
                if child_result.status != "RESOLVED":
                    dangling.append(child_id)
                    continue
                child = child_result.value
                entry = {
                    "parent_expression_id": current_id,
                    "operator": node["op"],
                    "operand_index": index,
                    "operand_count": len(operands),
                    "child_expression_id": child_id,
                    "operator_params": deepcopy(node.get("params", {})),
                }
                if child_id == target_expression_id:
                    paths.append(current_path + [entry])
                else:
                    walk(child_id, current_path + [entry])
            stack.pop()

        walk(root_expression_id, [])
        if cycle:
            return self._result("INVALID_INPUT", "expression_scope", target_expression_id, diagnostics=("EXPRESSION_GRAPH_CYCLE",), extra_provenance={"cycle_refs": sorted(set(cycle))})
        if len(paths) > 1:
            return self._result("AMBIGUOUS", "expression_scope", target_expression_id, candidates=tuple([root_expression_id, target_expression_id]), diagnostics=("EXPRESSION_SCOPE_MULTIPLE_PATHS",), extra_provenance={"scope_paths": paths})
        if blocked and not paths:
            return self._result("UNSUPPORTED", "expression_scope", target_expression_id, diagnostics=("OPAQUE_SCOPE_PATH_UNSUPPORTED",), extra_provenance={"opaque_refs": sorted(set(blocked))})
        if dangling and not paths:
            return self._result("UNRESOLVED", "expression_scope", target_expression_id, diagnostics=("EXPRESSION_OPERAND_REFERENCE_UNRESOLVED",), extra_provenance={"missing_refs": sorted(set(dangling))})
        if not paths:
            return self._result("UNRESOLVED", "expression_scope", target_expression_id, diagnostics=("EXPRESSION_NOT_IN_ROOT_SCOPE",), extra_provenance={"root_expression_id": root_expression_id})
        return self._result(
            "RESOLVED", "expression_scope", target_expression_id,
            {"root_expression_id": root_expression_id, "target_expression_id": target_expression_id, "path": paths[0]},
            extra_provenance={"root_expression_id": root_expression_id, "path_count": 1},
        )


def inspect_compact_benchmark_snapshot(fixture: dict[str, Any]) -> dict[str, Any]:
    """Safely preflight Step 2.2 compact snapshots without fabricating USG fields.

    This is intentionally a preservation/report adapter, not a conversion into
    a canonical USG document. Missing canonical assertion fields are reported
    rather than defaulted to SOURCE_ASSERTED or another value.
    """
    snapshot = fixture.get("input_snapshot") if isinstance(fixture, dict) else None
    if not isinstance(snapshot, dict):
        return {
            "mapping_status": "UNMAPPED",
            "canonical_document_ready": False,
            "preserved_snapshot": deepcopy(snapshot),
            "unmapped_refs": [],
            "missing_fields": ["input_snapshot"],
            "diagnostics": ["BENCHMARK_SNAPSHOT_INVALID"],
        }
    missing_fields: list[str] = []
    unmapped_refs: list[str] = []
    semantic = snapshot.get("semantic_records") or {}
    for record_type, records in semantic.items():
        if not isinstance(records, list):
            continue
        required = {
            "assertions": {"id", "expressionRef", "origin", "epistemicStatus", "commitment", "evaluationContext", "lifecycleStage"},
            "expressions": {"id", "op", "sort", "operandRefs", "params"},
            "mentions": {"id", "surfaceText", "resolutionStatus"},
            "referents": {"id", "label"},
            "contexts": {"id", "kind"},
        }.get(record_type, {"id"})
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                missing_fields.append(f"semantic_records.{record_type}[{index}]:object")
                continue
            record_id = record.get("id")
            if isinstance(record_id, str):
                unmapped_refs.append(record_id)
            absent = sorted(required - set(record))
            missing_fields.extend(f"semantic_records.{record_type}[{index}].{field}" for field in absent)
    missing_fields = sorted(set(missing_fields))
    return {
        "mapping_status": "LOSSLESS" if not missing_fields else "PARTIAL",
        "canonical_document_ready": not missing_fields,
        "preserved_snapshot": deepcopy(snapshot),
        "unmapped_refs": sorted(set(unmapped_refs)) if missing_fields else [],
        "missing_fields": missing_fields,
        "diagnostics": [] if not missing_fields else ["COMPACT_FIXTURE_MISSING_CANONICAL_FIELDS"],
    }


__all__ = ["ResolutionResult", "GroundingIndex", "inspect_compact_benchmark_snapshot"]
