"""Loss-preserving USG-SEM/1.0 document boundary for Python kernel 0.5.0.

Expression roots and exact supported Source records receive native projections.
All other record families remain in the canonical envelope until exact native
contracts are implemented; unsupported content is never coerced or discarded.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
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
    sources: dict[str, Any]
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

        from usg.core.ids import IdSpace
        from usg.core.records import Source

        graph_document = kernel_v05_graph_to_contract(self.expression_graph, validate=False)
        result = copy.deepcopy(self.document)

        # Serialize current native Source records. Canonical source records that
        # could not be projected remain untouched in the original envelope.
        source_by_id = {item["id"]: item for item in result.get("sources", [])}
        for source_id, source in self.sources.items():
            if not isinstance(source, Source):
                raise ContractMappingError(f"Non-Source native record for {source_id}")
            if source.ref is None or source.ref.space is not IdSpace.SOURCE:
                raise ContractMappingError(f"Native Source {source_id} has no valid SOURCE identity")
            original = source_by_id.get(source_id)
            if original is not None:
                original_anchor = original.get("anchor")
                anchor_matches = (
                    source.anchor is None and original_anchor is None
                ) or (
                    source.anchor is not None and original_anchor is not None
                    and source.anchor.document_date == original_anchor.get("documentDate")
                    and source.anchor.time_zone == original_anchor.get("timeZone")
                    and source.anchor.calendar == original_anchor.get("calendar", "gregorian")
                    and source.anchor.speech_time == original_anchor.get("speechTime")
                )
                if (
                    source.text == original.get("text")
                    and source.language == original.get("language")
                    and source.type.value == original.get("sourceType")
                    and source.trust_tier.value == original.get("trustTier")
                    and source.sensitivity.value == original.get("sensitivity")
                    and source.uri == original.get("uri")
                    and source.text_hash == original.get("textHash")
                    and anchor_matches
                ):
                    continue
            record = {
                "id": source_id, "text": source.text, "language": source.language,
                "sourceType": source.type.value, "trustTier": source.trust_tier.value,
                "sensitivity": source.sensitivity.value, "textHash": source.text_hash,
                "hashAlgorithm": "SHA-256", "encoding": "UTF-8",
                "offsetUnit": "unicode_code_point",
            }
            if source.uri is not None:
                record["uri"] = source.uri
            if source.anchor is not None:
                record["anchor"] = {
                    "documentDate": source.anchor.document_date,
                    "timeZone": source.anchor.time_zone,
                    "calendar": source.anchor.calendar,
                    "speechTime": source.anchor.speech_time,
                }
            source_by_id[source_id] = record
        source_order = list(dict.fromkeys(
            [item["id"] for item in result.get("sources", [])] + list(self.sources)
        ))
        result["sources"] = [source_by_id[key] for key in source_order if key in source_by_id]
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

    from usg.core.ids import IdSpace, Ref
    from usg.core.records import Anchor, Source
    from usg.core.values import Sensitivity, SourceType, TrustTier

    graph = contract_graph_roots_to_kernel_v05_partial(
        payload.get("expressions", []), payload.get("rootExpressionRefs", [])
    )

    # USG-SEM IDs are opaque. Assign deterministic typed IDs through this
    # explicit document-local map; never parse meaning from identifier text.
    source_ids = _record_ids(payload, "sources")
    source_ref_map = {source_id: Ref(IdSpace.SOURCE, index + 1)
                      for index, source_id in enumerate(source_ids)}
    native_sources: dict[str, Any] = {}
    source_unmapped: list[str] = []
    source_diagnostics: list[str] = []
    for item in payload.get("sources", []):
        source_id = item["id"]
        try:
            source_type = SourceType(item["sourceType"])
            trust_tier = TrustTier(item["trustTier"])
            sensitivity = Sensitivity(item["sensitivity"])
            anchor_data = item.get("anchor")
            anchor = Anchor(
                document_date=anchor_data.get("documentDate"),
                time_zone=anchor_data.get("timeZone"),
                calendar=anchor_data.get("calendar", "gregorian"),
                speech_time=anchor_data.get("speechTime"),
            ) if anchor_data is not None else None
            native_sources[source_id] = Source(
                text=item["text"], language=item["language"], type=source_type,
                trust_tier=trust_tier, sensitivity=sensitivity, anchor=anchor,
                uri=item.get("uri"), ref=source_ref_map[source_id],
                text_hash=item["textHash"],
            )
        except (KeyError, ValueError, TypeError) as exc:
            source_unmapped.append(source_id)
            source_diagnostics.append(f"source {source_id} remains canonical-only: {exc}")

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
    diagnostics = list(graph.diagnostics) + source_diagnostics
    for collection in _DOCUMENT_COLLECTIONS:
        ids = _record_ids(payload, collection)
        if collection == "sources":
            mapped = sorted(native_sources)
            unmapped_ids = sorted(source_unmapped)
            canonical_only_ids.extend(unmapped_ids)
            record_mapping[collection] = {
                "status": "LOSSLESS" if not unmapped_ids else "PARTIAL",
                "mapped": mapped,
                "unmappedRefs": unmapped_ids,
                "notes": ["Only exact SourceType/TrustTier/Sensitivity values are projected; unknown or absent enum values remain canonical-only."] if unmapped_ids else [],
            }
            continue
        canonical_only_ids.extend(ids)
        record_mapping[collection] = {
            "status": "UNMAPPED" if ids else "LOSSLESS",
            "mapped": [],
            "unmappedRefs": ids,
            "notes": [
                "Preserved in the canonical document envelope; native v0.5.0 projection is not implemented for this record family."
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
            "Expression roots and exact supported Source records are projected into native Python kernel 0.5.0 records.",
            "Referents, mentions, assertions, evidence, contexts, definitions, relations, unresolved items, derivations, validation, mapping, and extensions remain canonical-only in this step.",
            "Expression records not reachable from rootExpressionRefs remain canonical-only.",
            "OPAQUE projections preserve unknown operators but do not establish semantic interpretation or inference eligibility.",
        ],
    }
    return KernelV05Document(
        document=payload,
        original_digest=_digest(payload),
        expression_graph=graph,
        sources=native_sources,
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
