"""Loss-preserving USG-SEM/1.0 Mention adapter for native model v0.7.0.

The canonical document remains authoritative. Only exact, resolvable Mention
fields are projected; unsupported values and links remain in the envelope.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_mention_model():
    """Load v0.7.0 in isolation; older adapter workflows need no PYTHONPATH change."""
    try:
        import usg_discourse_v07 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_discourse_v07":
            raise
    import importlib.util
    import sys

    package_dir = (
        Path(__file__).resolve().parents[2]
        / "implementations" / "python-kernel" / "v0.7.0" / "usg_discourse_v07"
    )
    init_file = package_dir / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "usg_discourse_v07", init_file,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load Python Mention model from {init_file}")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_discourse_v07"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_mention_model()
MODEL_VERSION = _model.MODEL_VERSION
MentionResolutionStatus = _model.MentionResolutionStatus
NativeMentionV07 = _model.NativeMentionV07
ReferenceSpace = _model.ReferenceSpace
TypedReference = _model.TypedReference

_MENTION_FIELDS = {
    "id", "surfaceText", "resolutionStatus", "mentionType", "referentRef",
    "antecedentMentionRef", "antecedentReferentRef", "sourceSpan",
}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV07Document:
    """Canonical document plus native Mention projections and coverage."""
    document: dict[str, Any]
    original_digest: str
    mentions: dict[str, NativeMentionV07]
    mention_snapshots: dict[str, NativeMentionV07]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(
        self, *, validate: bool = True, schema_path: str | Path = SCHEMA_PATH
    ) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing to merge native "
                "Mention projections into stale document records."
            )
        result = copy.deepcopy(self.document)
        records = {item["id"]: item for item in result.get("mentions", [])}
        for external_id, native in self.mentions.items():
            if not isinstance(native, NativeMentionV07):
                raise ContractMappingError(f"Non-NativeMentionV07 record for {external_id}")
            if native.external_id != external_id:
                raise ContractMappingError(
                    f"Native Mention key {external_id!r} does not match opaque ID "
                    f"{native.external_id!r}"
                )
            if external_id not in records or external_id not in self.mention_snapshots:
                raise ContractMappingError(f"Native Mention {external_id!r} has no canonical snapshot")
            _merge_mention_edit(records[external_id], self.mention_snapshots[external_id], native)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v0.7.0 document is invalid: " + "; ".join(problems[:20])
                )
        return result


def _ids(document: Mapping[str, Any], collection: str) -> set[str]:
    return {
        item["id"] for item in document.get(collection, [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


def _project_mention(
    item: Mapping[str, Any],
    *,
    mention_ids: set[str],
    referent_ids: set[str],
    source_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[NativeMentionV07, list[str], list[str]]:
    mid = item["id"]
    mapped: list[str] = ["id", "surfaceText"]
    unmapped: list[str] = []

    status_value = item.get("resolutionStatus")
    try:
        status = MentionResolutionStatus(status_value)
        mapped.append("resolutionStatus")
    except (ValueError, TypeError):
        # The schema normally rejects this; validate=False still must not coerce it.
        status = MentionResolutionStatus.UNKNOWN
        unmapped.append("resolutionStatus")

    mention_type = item.get("mentionType")
    if mention_type is None or isinstance(mention_type, str):
        mapped.append("mentionType")
    else:
        mention_type = None
        unmapped.append("mentionType")

    def typed_link(field: str, space: ReferenceSpace, targets: set[str]):
        value = item.get(field)
        if value is None:
            mapped.append(field)
            return None
        if isinstance(value, str) and value in targets:
            mapped.append(field)
            return TypedReference(space, value)
        unmapped.append(field)
        return None

    referent_ref = typed_link("referentRef", ReferenceSpace.REFERENT, referent_ids)
    antecedent_mention_ref = typed_link(
        "antecedentMentionRef", ReferenceSpace.MENTION, mention_ids
    )
    antecedent_referent_ref = typed_link(
        "antecedentReferentRef", ReferenceSpace.REFERENT, referent_ids
    )

    source_ref = None
    source_span = None
    span = item.get("sourceSpan")
    if span is None:
        mapped.append("sourceSpan")
    elif not isinstance(span, Mapping):
        unmapped.append("sourceSpan")
    else:
        source_id = span.get("sourceRef")
        source = source_by_id.get(source_id) if isinstance(source_id, str) else None
        start, end = span.get("start"), span.get("end")
        valid_bounds = (
            isinstance(start, int) and not isinstance(start, bool)
            and isinstance(end, int) and not isinstance(end, bool)
            and 0 <= start <= end
        )
        if source is None or not isinstance(source.get("text"), str) or not valid_bounds:
            unmapped.append("sourceSpan")
        else:
            source_text = source["text"]
            if end > len(source_text):
                unmapped.append("sourceSpan")
            elif source_text[start:end] != item.get("surfaceText"):
                # Do not silently align a mention to a different substring.
                unmapped.append("sourceSpan")
            else:
                source_ref = TypedReference(ReferenceSpace.SOURCE, source_id)
                source_span = (start, end)
                mapped.append("sourceSpan")

    native = NativeMentionV07(
        external_id=mid,
        surface_text=item["surfaceText"],
        resolution_status=status,
        mention_type=mention_type,
        referent_ref=referent_ref,
        antecedent_mention_ref=antecedent_mention_ref,
        antecedent_referent_ref=antecedent_referent_ref,
        source_ref=source_ref,
        source_span=source_span,
    )
    # nativeId and any future/additional properties stay canonical-only.
    for key in sorted(set(item) - _MENTION_FIELDS):
        unmapped.append(key)
    return native, mapped, unmapped


def _merge_mention_edit(
    record: dict[str, Any], snapshot: NativeMentionV07, current: NativeMentionV07
) -> None:
    """Merge only changed, representable native fields; preserve all sidecars."""
    if current.surface_text != snapshot.surface_text:
        record["surfaceText"] = current.surface_text
    if current.resolution_status != snapshot.resolution_status:
        if not isinstance(current.resolution_status, MentionResolutionStatus):
            raise ContractMappingError("resolution_status must be a known MentionResolutionStatus")
        record["resolutionStatus"] = current.resolution_status.value
    if current.mention_type != snapshot.mention_type:
        if current.mention_type is None:
            record.pop("mentionType", None)
        elif isinstance(current.mention_type, str):
            record["mentionType"] = current.mention_type
        else:
            raise ContractMappingError("mention_type must be a string or None")

    for attr, field, expected_space in (
        ("referent_ref", "referentRef", ReferenceSpace.REFERENT),
        ("antecedent_mention_ref", "antecedentMentionRef", ReferenceSpace.MENTION),
        ("antecedent_referent_ref", "antecedentReferentRef", ReferenceSpace.REFERENT),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if after is None:
                record.pop(field, None)
            elif isinstance(after, TypedReference) and after.space is expected_space:
                record[field] = after.external_id
            else:
                raise ContractMappingError(f"{field} requires an explicit {expected_space.value} reference")

    if (current.source_ref, current.source_span) != (snapshot.source_ref, snapshot.source_span):
        if current.source_span is None:
            record.pop("sourceSpan", None)
        else:
            if current.source_ref is None or current.source_ref.space is not ReferenceSpace.SOURCE:
                raise ContractMappingError("source_span export requires an explicit SOURCE reference")
            start, end = current.source_span
            record["sourceSpan"] = {
                "sourceRef": current.source_ref.external_id,
                "start": start,
                "end": end,
                "offsetUnit": "unicode_code_point",
            }


def document_to_kernel_v07(
    document: Mapping[str, Any], *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> KernelV07Document:
    """Import USG-SEM/1.0 and project exact, resolvable Mention fields."""
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    mention_ids = _ids(payload, "mentions")
    referent_ids = _ids(payload, "referents")
    source_by_id = {
        item["id"]: item for item in payload.get("sources", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }

    native_mentions: dict[str, NativeMentionV07] = {}
    snapshots: dict[str, NativeMentionV07] = {}
    entries: dict[str, Any] = {}
    mapped_ids: list[str] = []
    unmapped_ids: list[str] = []
    diagnostics: list[str] = []

    for item in payload.get("mentions", []):
        native, mapped_fields, unsupported_fields = _project_mention(
            item, mention_ids=mention_ids, referent_ids=referent_ids,
            source_by_id=source_by_id,
        )
        native_mentions[item["id"]] = native
        snapshots[item["id"]] = native
        status = "PARTIAL" if unsupported_fields else "LOSSLESS"
        if unsupported_fields:
            unmapped_ids.append(item["id"])
            diagnostics.append(
                f"mention {item['id']} has canonical-only fields: "
                + ", ".join(unsupported_fields)
            )
        else:
            mapped_ids.append(item["id"])
        entries[item["id"]] = {
            "status": status,
            "mappedFields": mapped_fields,
            "unmappedFields": unsupported_fields,
            "notes": (
                ["Unsupported values, links, and additional fields remain in the canonical Mention record."]
                if unsupported_fields else []
            ),
        }

    record_mapping: dict[str, dict[str, Any]] = {
        "mentions": {
            "status": "PARTIAL" if unmapped_ids else "LOSSLESS",
            "mapped": sorted(mapped_ids),
            "unmappedRefs": sorted(unmapped_ids),
            "records": entries,
            "notes": [
                "Mention occurrence identity is independent of surface text and Referent identity.",
                "Links are projected only when their explicit target record exists; no coreference or antecedent inference is performed.",
            ],
        }
    }
    canonical_only_ids: list[str] = []
    for collection in _COLLECTIONS:
        if collection == "mentions":
            continue
        ids = sorted(_ids(payload, collection))
        canonical_only_ids.extend(ids)
        record_mapping[collection] = {
            "status": "UNMAPPED" if ids else "LOSSLESS",
            "mapped": [],
            "unmappedRefs": ids,
            "notes": [
                "Preserved in the canonical document envelope; this step does not project this record family."
            ] if ids else [],
        }
    definition_ids: list[str] = []
    definitions = payload.get("definitions") or {}
    for group in ("concepts", "frames", "roles", "relations"):
        definition_ids.extend(
            item["id"] for item in definitions.get(group, [])
            if isinstance(item, Mapping) and isinstance(item.get("id"), str)
        )
    canonical_only_ids.extend(definition_ids)
    record_mapping["definitions"] = {
        "status": "UNMAPPED" if definition_ids else "LOSSLESS",
        "mapped": [],
        "unmappedRefs": sorted(definition_ids),
        "notes": ["Definitions remain canonical-only in this adapter."] if definition_ids else [],
    }
    for collection in ("validation", "mapping", "extensions"):
        record_mapping[collection] = {
            "status": "PRESERVED", "mapped": [], "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted to native kernel authority."],
        }

    all_unmapped = sorted(set(canonical_only_ids + unmapped_ids))
    mapping_report = {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel",
        "targetVersion": MODEL_VERSION,
        "status": "PARTIAL" if all_unmapped else "LOSSLESS",
        "unmappedRefs": all_unmapped,
        "recordMapping": copy.deepcopy(record_mapping),
        "notes": [
            "The complete canonical document remains the authoritative envelope.",
            "Only exact Mention fields and explicitly resolvable typed links are projected into native v0.7.0.",
            "All other records and unsupported Mention fields remain canonical-only; no inference or record merging occurs.",
        ],
    }
    return KernelV07Document(
        document=payload,
        original_digest=_digest(payload),
        mentions=native_mentions,
        mention_snapshots=snapshots,
        record_mapping=record_mapping,
        mapping_report=mapping_report,
        diagnostics=diagnostics,
    )


def kernel_v07_document_to_contract(
    imported: KernelV07Document, *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> dict[str, Any]:
    """Serialize native Mention edits into the retained canonical document."""
    if not isinstance(imported, KernelV07Document):
        raise TypeError("imported must be a KernelV07Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
