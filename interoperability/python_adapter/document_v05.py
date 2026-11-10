"""Document-level USG-SEM/1.0 boundary for Python kernel 0.5.0.

Only the expression graph is projected into native v0.5.0 Nodes. The complete
document envelope and every non-expression record family remain canonical and
are carried through export. No source/assertion/document-record equivalence is
inferred from the graph adapter.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _canonical_bytes, _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError
from .kernel_v05 import (
    KernelV05Graph,
    contract_graph_roots_to_kernel_v05_partial,
    kernel_v05_graph_to_contract,
)

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"

_DOCUMENT_COLLECTIONS = (
    "sources", "referents", "mentions", "assertions", "evidence", "contexts",
    "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV05Document:
    """Whole canonical document plus native expression graph and coverage report."""

    document: dict[str, Any]
    original_digest: str
    expression_graph: KernelV05Graph
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    @property
    def expression_roots(self) -> dict[str, Any]:
        return self.expression_graph.roots

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        """Serialize current native Nodes into the full canonical document.

        The canonical envelope is immutable during this operation. Expression
        records are freshly serialized from current native Nodes; all unrelated
        document records and unsupported/unreachable expressions are retained.
        """
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing to merge native "
                "projections into stale document records."
            )

        graph_document = kernel_v05_graph_to_contract(self.expression_graph, validate=False)
        result = copy.deepcopy(self.document)
        original_by_id = {item["id"]: item for item in result.get("expressions", [])}
        serialized_by_id = {item["id"]: item for item in graph_document["expressions"]}
        # The graph serializer emits the current native graph and preserves
        # original canonical-only expression records. Merge by opaque ID only.
        original_by_id.update(serialized_by_id)
        ordered_ids = list(dict.fromkeys(
            [item["id"] for item in result.get("expressions", [])] +
            [item["id"] for item in graph_document["expressions"]]
        ))
        result["expressions"] = [original_by_id[key] for key in ordered_ids]
        result["rootExpressionRefs"] = list(graph_document["rootExpressionRefs"])
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v0.5.0 document is invalid: " + "; ".join(problems[:20])
                )
        return result


def _record_ids(document: Mapping[str, Any], collection: str) -> list[str]:
    if collection == "definitions":
        records = []
        definitions = document.get("definitions") or {}
        for key in ("concepts", "frames", "roles", "relations"):
            records.extend(definitions.get(key, []))
    else:
        records = document.get(collection, [])
    return sorted(item["id"] for item in records if isinstance(item, Mapping) and isinstance(item.get("id"), str))


def document_to_kernel_v05(
    document: Mapping[str, Any], *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> KernelV05Document:
    """Import a complete USG-SEM/1.0 document with native v0.5.0 graph projection."""
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    try:
        import usg
        version = getattr(usg, "__version__", None)
    except Exception as exc:
        raise ContractMappingError("Python kernel package is not importable") from exc
    if version != "0.5.0":
        raise ContractMappingError(
            f"Document v0.5 adapter requires isolated usg 0.5.0 import path; found {version!r}"
        )

    graph = contract_graph_roots_to_kernel_v05_partial(
        payload.get("expressions", []), payload.get("rootExpressionRefs", [])
    )
    expression_ids = _record_ids(payload, "expressions")
    native_ids = set(graph.node_identity_refs.values())
    native_ids.update(graph.partial_refs)
    failed_reachable = set(graph.failed_roots)
    # Unknown operators become explicit OPAQUE nodes; they are native
    # preservation projections but remain PARTIAL, as indicated by partial_refs.
    expression_unmapped = sorted(set(expression_ids) - native_ids)
    expression_partial = sorted(set(graph.partial_refs) | failed_reachable)
    expression_status = "LOSSLESS" if not expression_unmapped and not expression_partial else "PARTIAL"

    record_mapping: dict[str, dict[str, Any]] = {
        "expressions": {
            "status": expression_status,
            "mapped": sorted(native_ids - set(graph.failed_roots)),
            "unmappedRefs": expression_unmapped,
            "partialRefs": expression_partial,
            "notes": list(graph.diagnostics),
        }
    }
    canonical_only_ids: list[str] = []
    diagnostics = list(graph.diagnostics)
    for collection in _DOCUMENT_COLLECTIONS:
        ids = _record_ids(payload, collection)
        canonical_only_ids.extend(ids)
        record_mapping[collection] = {
            "status": "UNMAPPED" if ids else "LOSSLESS",
            "mapped": [],
            "unmappedRefs": ids,
            "notes": [
                "Preserved in the canonical document envelope; kernel v0.5.0 document-record projection is not implemented in Step 5D."
            ] if ids else [],
        }
    definition_ids = _record_ids(payload, "definitions")
    canonical_only_ids.extend(definition_ids)
    record_mapping["definitions"] = {
        "status": "UNMAPPED" if definition_ids else "LOSSLESS",
        "mapped": [],
        "unmappedRefs": definition_ids,
        "notes": [
            "Definitions remain canonical; no exact v0.5.0 Concept/FrameDef/RoleDef/RelationDef document adapter is claimed."
        ] if definition_ids else [],
    }
    for collection in ("validation", "mapping", "extensions"):
        record_mapping[collection] = {
            "status": "PRESERVED", "mapped": [], "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted to kernel authority."],
        }

    unmapped = sorted(set(expression_unmapped + expression_partial + canonical_only_ids))
    partial = bool(unmapped) or graph.mapping_report["status"] == "PARTIAL"
    mapping_report = {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel",
        "targetVersion": "0.5.0",
        "status": "PARTIAL" if partial else "LOSSLESS",
        "unmappedRefs": unmapped,
        "recordMapping": copy.deepcopy(record_mapping),
        "notes": [
            "The complete canonical document is retained as the authoritative document envelope.",
            "Only expression roots are projected into native Python kernel 0.5.0 Nodes in Step 5D.",
            "Sources, referents, mentions, assertions, evidence, contexts, definitions, relations, unresolved items, derivations, validation, mapping, and extensions are not silently dropped or reinterpreted.",
            "Expression records not reachable from rootExpressionRefs remain canonical-only.",
            "OPAQUE projections preserve unknown operators but do not establish semantic interpretation or inference eligibility.",
        ],
    }
    return KernelV05Document(
        document=payload,
        original_digest=_digest(payload),
        expression_graph=graph,
        record_mapping=record_mapping,
        mapping_report=mapping_report,
        diagnostics=diagnostics,
    )


def kernel_v05_document_to_contract(
    imported: KernelV05Document, *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> dict[str, Any]:
    """Public reverse boundary for a whole v0.5.0-imported USG-SEM document."""
    if not isinstance(imported, KernelV05Document):
        raise TypeError("imported must be a KernelV05Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
