"""Loss-preserving USG-SEM/1.0 Referent adapter for identity model v0.6.0.

Only fields represented exactly by NativeReferentV06 are projected. The full
canonical document remains authoritative for unsupported fields and every
other record family. Native edits are merged into Referent records only.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError
from usg_identity_v06 import (
    MODEL_VERSION,
    IdentityScope,
    IdentityStatus,
    IntroductionContext,
    IntroductionKind,
    NativeReferentV06,
    ReferenceSpace,
    ReferentIdentity,
    TypedReference,
)

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"

_SEMANTIC_KINDS = {
    "ENTITY", "EVENT", "PROCESS", "STATE", "PROPERTY", "VALUE", "QUANTITY",
    "RELATION", "ROLE", "FRAME", "PROPOSITION", "CONSTRAINT", "TIME",
    "FUNCTION", "EXPRESSION",
}
_NUMBERS = {"SINGULAR", "PLURAL", "MASS", "UNSPECIFIED"}
_GENERICITIES = {"SPECIFIC", "GENERIC"}
_SUPPORTED_INTRODUCTIONS = {item.value for item in IntroductionKind}
_SUPPORTED_IDENTITY_STATUSES = {item.value for item in IdentityStatus}
_SUPPORTED_IDENTITY_SCOPES = {item.value for item in IdentityScope}

_REFERENT_FIELDS = {
    "id", "label", "semanticKind", "conceptRefs", "aliases", "number",
    "genericity", "introducedIn", "identity", "sourceRef", "sourceSpan",
}
_IDENTITY_FIELDS = {"status", "scope", "equivalenceRefs", "basis"}
_INTRODUCTION_FIELDS = {"kind", "contextRef"}


@dataclass
class KernelV06Document:
    """Canonical document plus exact native Referent projections and coverage."""

    document: dict[str, Any]
    original_digest: str
    referents: dict[str, NativeReferentV06]
    referent_snapshots: dict[str, NativeReferentV06]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(
        self, *, validate: bool = True, schema_path: str | Path = SCHEMA_PATH
    ) -> dict[str, Any]:
        """Merge native Referent edits into the untouched canonical envelope."""
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing to merge native "
                "Referent projections into stale document records."
            )

        result = copy.deepcopy(self.document)
        records = {item["id"]: item for item in result.get("referents", [])}
        for external_id, native in self.referents.items():
            if not isinstance(native, NativeReferentV06):
                raise ContractMappingError(f"Non-NativeReferentV06 record for {external_id}")
            if native.external_id != external_id:
                raise ContractMappingError(
                    f"Native Referent key {external_id!r} does not match opaque external ID "
                    f"{native.external_id!r}"
                )
            if external_id not in records or external_id not in self.referent_snapshots:
                raise ContractMappingError(f"Native Referent {external_id!r} has no canonical snapshot")
            _merge_referent_edit(
                records[external_id], self.referent_snapshots[external_id], native
            )

        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v0.6.0 document is invalid: " + "; ".join(problems[:20])
                )
        return result


def _enum_value(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _record_ids(document: Mapping[str, Any], collection: str) -> set[str]:
    return {
        item["id"] for item in document.get(collection, [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


def _definition_ids(document: Mapping[str, Any], collection: str) -> set[str]:
    definitions = document.get("definitions") or {}
    return {
        item["id"] for item in definitions.get(collection, [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


def _project_referent(
    item: Mapping[str, Any],
    *,
    referent_ids: set[str],
    concept_ids: set[str],
    source_by_id: Mapping[str, Mapping[str, Any]],
    expression_ids: set[str],
) -> tuple[NativeReferentV06, list[str], list[str]]:
    """Return native projection, exact mapped field paths, and unsupported paths."""
    rid = item["id"]
    mapped = ["id", "label"]
    unsupported: list[str] = []
    semantic_kind = item.get("semanticKind")
    if semantic_kind is not None and not _enum_value(semantic_kind, _SEMANTIC_KINDS):
        unsupported.append("semanticKind")
        semantic_kind = None
    else:
        mapped.append("semanticKind")

    concept_refs: tuple[TypedReference, ...] = ()
    raw_concepts = item.get("conceptRefs", [])
    if all(ref in concept_ids for ref in raw_concepts):
        concept_refs = tuple(TypedReference(ReferenceSpace.CONCEPT, ref) for ref in raw_concepts)
        mapped.append("conceptRefs")
    else:
        unsupported.append("conceptRefs")

    aliases = tuple(item.get("aliases", []))
    mapped.append("aliases")

    identity_data = item.get("identity") or {}
    identity_status = None
    if "status" not in identity_data:
        mapped.append("identity.status")
    elif _enum_value(identity_data["status"], _SUPPORTED_IDENTITY_STATUSES):
        identity_status = IdentityStatus(identity_data["status"])
        mapped.append("identity.status")
    else:
        unsupported.append("identity.status")

    identity_scope = None
    if "scope" not in identity_data:
        mapped.append("identity.scope")
    elif _enum_value(identity_data["scope"], _SUPPORTED_IDENTITY_SCOPES):
        identity_scope = IdentityScope(identity_data["scope"])
        mapped.append("identity.scope")
    else:
        unsupported.append("identity.scope")

    equivalence_refs: tuple[TypedReference, ...] = ()
    raw_equivalence = identity_data.get("equivalenceRefs", [])
    if all(ref in referent_ids for ref in raw_equivalence):
        equivalence_refs = tuple(
            TypedReference(ReferenceSpace.REFERENT, ref) for ref in raw_equivalence
        )
        mapped.append("identity.equivalenceRefs")
    else:
        unsupported.append("identity.equivalenceRefs")

    basis = identity_data.get("basis")
    if basis is None or isinstance(basis, str):
        mapped.append("identity.basis")
    else:
        unsupported.append("identity.basis")
        basis = None

    for key in sorted(set(identity_data) - _IDENTITY_FIELDS):
        unsupported.append(f"identity.{key}")

    identity = ReferentIdentity(
        status=identity_status,
        scope=identity_scope,
        equivalence_refs=equivalence_refs,
        basis=basis,
    )

    introduction_data = item.get("introducedIn") or {}
    intro_kind_value = introduction_data.get("kind", "WORLD")
    introduced_in = IntroductionContext()
    if _enum_value(intro_kind_value, _SUPPORTED_INTRODUCTIONS):
        intro_kind = IntroductionKind(intro_kind_value)
        context_ref_value = introduction_data.get("contextRef")
        if intro_kind is IntroductionKind.WORLD:
            if context_ref_value is None:
                introduced_in = IntroductionContext(IntroductionKind.WORLD)
                mapped.extend(["introducedIn.kind", "introducedIn.contextRef"])
            else:
                unsupported.extend(["introducedIn.kind", "introducedIn.contextRef"])
        elif context_ref_value in expression_ids:
            introduced_in = IntroductionContext(
                intro_kind, TypedReference(ReferenceSpace.NODE, context_ref_value)
            )
            mapped.extend(["introducedIn.kind", "introducedIn.contextRef"])
        else:
            unsupported.extend(["introducedIn.kind", "introducedIn.contextRef"])
    else:
        unsupported.append("introducedIn.kind")
        if "contextRef" in introduction_data:
            unsupported.append("introducedIn.contextRef")

    for key in sorted(set(introduction_data) - _INTRODUCTION_FIELDS):
        unsupported.append(f"introducedIn.{key}")

    number = item.get("number")
    if number is None or _enum_value(number, _NUMBERS):
        mapped.append("number")
    else:
        unsupported.append("number")
        number = None

    genericity = item.get("genericity")
    if genericity is None or _enum_value(genericity, _GENERICITIES):
        mapped.append("genericity")
    else:
        unsupported.append("genericity")
        genericity = None

    source_ref_value = item.get("sourceRef")
    source_ref = None
    if source_ref_value is None:
        mapped.append("sourceRef")
    elif source_ref_value in source_by_id:
        source_ref = TypedReference(ReferenceSpace.SOURCE, source_ref_value)
        mapped.append("sourceRef")
    else:
        unsupported.append("sourceRef")

    source_span_value = item.get("sourceSpan")
    source_span = None
    if source_span_value is None:
        mapped.append("sourceSpan")
    else:
        span_source = source_span_value.get("sourceRef")
        source = source_by_id.get(span_source)
        valid_span = (
            source is not None
            and span_source == source_ref_value
            and source_span_value.get("offsetUnit") == "unicode_code_point"
            and isinstance(source_span_value.get("start"), int)
            and not isinstance(source_span_value.get("start"), bool)
            and isinstance(source_span_value.get("end"), int)
            and not isinstance(source_span_value.get("end"), bool)
            and 0 <= source_span_value["start"] <= source_span_value["end"] <= len(source["text"])
        )
        if valid_span:
            source_span = (source_span_value["start"], source_span_value["end"])
            mapped.append("sourceSpan")
        else:
            unsupported.append("sourceSpan")

    for key in sorted(set(item) - _REFERENT_FIELDS):
        unsupported.append(key)

    native = NativeReferentV06(
        external_id=rid,
        label=item["label"],
        semantic_kind=semantic_kind,
        concept_refs=concept_refs,
        aliases=aliases,
        identity=identity,
        introduced_in=introduced_in,
        number=number,
        genericity=genericity,
        source_ref=source_ref,
        source_span=source_span,
    )
    return native, sorted(set(mapped)), sorted(set(unsupported))


def _merge_referent_edit(
    record: dict[str, Any],
    snapshot: NativeReferentV06,
    current: NativeReferentV06,
) -> None:
    """Update only native fields that changed; preserve all canonical sidecars."""
    if current.label != snapshot.label:
        record["label"] = current.label
    if current.semantic_kind != snapshot.semantic_kind:
        if current.semantic_kind is None:
            record.pop("semanticKind", None)
        else:
            if not _enum_value(current.semantic_kind, _SEMANTIC_KINDS):
                raise ContractMappingError("semantic_kind is not a USG-SEM semanticKind enum")
            record["semanticKind"] = current.semantic_kind
    if current.concept_refs != snapshot.concept_refs:
        record["conceptRefs"] = [ref.external_id for ref in current.concept_refs]
    if current.aliases != snapshot.aliases:
        record["aliases"] = list(current.aliases)
    if current.number != snapshot.number:
        if current.number is None:
            record.pop("number", None)
        elif _enum_value(current.number, _NUMBERS):
            record["number"] = current.number
        else:
            raise ContractMappingError("number is not a USG-SEM number enum")
    if current.genericity != snapshot.genericity:
        if current.genericity is None:
            record.pop("genericity", None)
        elif _enum_value(current.genericity, _GENERICITIES):
            record["genericity"] = current.genericity
        else:
            raise ContractMappingError("genericity is not a USG-SEM genericity enum")

    if current.identity.status != snapshot.identity.status:
        _set_optional(record.setdefault("identity", {}), "status",
                      current.identity.status.value if current.identity.status else None)
    if current.identity.scope != snapshot.identity.scope:
        _set_optional(record.setdefault("identity", {}), "scope",
                      current.identity.scope.value if current.identity.scope else None)
    if current.identity.equivalence_refs != snapshot.identity.equivalence_refs:
        record.setdefault("identity", {})["equivalenceRefs"] = [
            ref.external_id for ref in current.identity.equivalence_refs
        ]
    if current.identity.basis != snapshot.identity.basis:
        _set_optional(record.setdefault("identity", {}), "basis", current.identity.basis)
    if "identity" in record and not record["identity"]:
        record.pop("identity")

    if current.introduced_in != snapshot.introduced_in:
        if current.introduced_in.kind is IntroductionKind.WORLD:
            record["introducedIn"] = {"kind": "WORLD"}
        else:
            context_ref = current.introduced_in.context_ref
            if context_ref is None or context_ref.space is not ReferenceSpace.NODE:
                raise ContractMappingError(
                    "Non-WORLD introduction context export requires an explicitly mapped NODE ref"
                )
            record["introducedIn"] = {
                "kind": current.introduced_in.kind.value,
                "contextRef": context_ref.external_id,
            }

    if current.source_ref != snapshot.source_ref:
        _set_optional(record, "sourceRef",
                      current.source_ref.external_id if current.source_ref else None)
        if current.source_span is not None:
            span = record.get("sourceSpan")
            if span is not None:
                span["sourceRef"] = current.source_ref.external_id if current.source_ref else None
    if current.source_span != snapshot.source_span:
        if current.source_span is None:
            record.pop("sourceSpan", None)
        else:
            if current.source_ref is None or current.source_ref.space is not ReferenceSpace.SOURCE:
                raise ContractMappingError("source_span export requires an explicit SOURCE reference")
            record["sourceSpan"] = {
                "sourceRef": current.source_ref.external_id,
                "start": current.source_span[0],
                "end": current.source_span[1],
                "offsetUnit": "unicode_code_point",
            }


def _set_optional(target: dict[str, Any], key: str, value: Any) -> None:
    if value is None:
        target.pop(key, None)
    else:
        target[key] = value


def document_to_kernel_v06(
    document: Mapping[str, Any], *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> KernelV06Document:
    """Import USG-SEM/1.0 with native v0.6.0 Referent identity projections."""
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    referent_ids = _record_ids(payload, "referents")
    concept_ids = _definition_ids(payload, "concepts")
    source_by_id = {item["id"]: item for item in payload.get("sources", [])}
    expression_ids = _record_ids(payload, "expressions")

    native_referents: dict[str, NativeReferentV06] = {}
    snapshots: dict[str, NativeReferentV06] = {}
    mapped_ids: list[str] = []
    unmapped_ids: list[str] = []
    diagnostics: list[str] = []
    referent_entries: dict[str, Any] = {}

    for item in payload.get("referents", []):
        native, mapped_fields, unsupported_fields = _project_referent(
            item, referent_ids=referent_ids, concept_ids=concept_ids,
            source_by_id=source_by_id, expression_ids=expression_ids,
        )
        native_referents[item["id"]] = native
        snapshots[item["id"]] = native
        status = "LOSSLESS" if not unsupported_fields else "PARTIAL"
        if unsupported_fields:
            unmapped_ids.append(item["id"])
            diagnostics.append(
                f"referent {item['id']} has canonical-only fields: "
                + ", ".join(unsupported_fields)
            )
        else:
            mapped_ids.append(item["id"])
        referent_entries[item["id"]] = {
            "status": status,
            "mappedFields": mapped_fields,
            "unmappedFields": unsupported_fields,
            "notes": (
                ["Unsupported fields remain in the canonical Referent record and are not projected."]
                if unsupported_fields else []
            ),
        }

    record_mapping: dict[str, dict[str, Any]] = {
        "referents": {
            "status": "LOSSLESS" if not unmapped_ids else "PARTIAL",
            "mapped": sorted(mapped_ids),
            "unmappedRefs": sorted(unmapped_ids),
            "records": referent_entries,
            "notes": [
                "Per-record and per-field coverage is reported; partial native projections never imply full Referent equivalence."
            ],
        }
    }

    canonical_collections = (
        "sources", "mentions", "expressions", "assertions", "evidence", "contexts",
        "expressionRelations", "unresolvedItems", "derivations",
    )
    canonical_only_ids: list[str] = []
    for collection in canonical_collections:
        ids = sorted(_record_ids(payload, collection))
        canonical_only_ids.extend(ids)
        record_mapping[collection] = {
            "status": "UNMAPPED" if ids else "LOSSLESS",
            "mapped": [],
            "unmappedRefs": ids,
            "notes": [
                "Preserved in the canonical document envelope; this step does not project this record family."
            ] if ids else [],
        }
    definition_ids = sorted(
        _definition_ids(payload, "concepts") | _definition_ids(payload, "frames")
        | _definition_ids(payload, "roles") | _definition_ids(payload, "relations")
    )
    canonical_only_ids.extend(definition_ids)
    record_mapping["definitions"] = {
        "status": "UNMAPPED" if definition_ids else "LOSSLESS",
        "mapped": [],
        "unmappedRefs": definition_ids,
        "notes": [
            "Definitions remain canonical-only; conceptRefs are typed links, not native Concept definition projections."
        ] if definition_ids else [],
    }
    for collection in ("validation", "mapping", "extensions"):
        record_mapping[collection] = {
            "status": "PRESERVED", "mapped": [], "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted to kernel authority."],
        }

    all_unmapped = sorted(set(canonical_only_ids + unmapped_ids))
    overall_partial = bool(all_unmapped)
    mapping_report = {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel",
        "targetVersion": MODEL_VERSION,
        "status": "PARTIAL" if overall_partial else "LOSSLESS",
        "unmappedRefs": all_unmapped,
        "recordMapping": copy.deepcopy(record_mapping),
        "notes": [
            "The complete canonical document remains the authoritative envelope.",
            "Referent identity records are projected into the separate v0.6.0 identity model only for exact supported fields.",
            "Unsupported Referent fields and all other record families remain canonical-only; no Mention, antecedent, or coreference inference is performed.",
        ],
    }
    return KernelV06Document(
        document=payload,
        original_digest=_digest(payload),
        referents=native_referents,
        referent_snapshots=snapshots,
        record_mapping=record_mapping,
        mapping_report=mapping_report,
        diagnostics=diagnostics,
    )


def kernel_v06_document_to_contract(
    imported: KernelV06Document, *, validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> dict[str, Any]:
    """Serialize current native Referents into the retained canonical document."""
    if not isinstance(imported, KernelV06Document):
        raise TypeError("imported must be a KernelV06Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
