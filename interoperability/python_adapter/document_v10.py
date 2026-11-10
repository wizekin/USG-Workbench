"""Loss-preserving USG-SEM/1.0 Context adapter for native model v1.0.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_context_model():
    try:
        import usg_context_v10 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_context_v10":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v1.0.0" / "usg_context_v10")
    spec = importlib.util.spec_from_file_location(
        "usg_context_v10", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native Context model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_context_v10"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_context_model()
MODEL_VERSION = _model.MODEL_VERSION
ContextKind = _model.ContextKind
NativeContextV10 = _model.NativeContextV10
ReferenceSpace = _model.ReferenceSpace
TypedReference = _model.TypedReference

_CONTEXT_FIELDS = {"id", "kind", "parentRef", "sourceRef", "agentRef", "name", "metadata"}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV10Document:
    document: dict[str, Any]
    original_digest: str
    contexts: dict[str, NativeContextV10]
    context_snapshots: dict[str, NativeContextV10]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale native Context merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("contexts", [])}
        ids = {collection: _ids(result, collection) for collection in
               ("contexts", "sources", "referents")}
        for key, native in self.contexts.items():
            if not isinstance(native, NativeContextV10):
                raise ContractMappingError(f"Non-NativeContextV10 record for {key}")
            if native.external_id != key:
                raise ContractMappingError(f"Native Context key {key!r} does not match opaque ID")
            if key not in records or key not in self.context_snapshots:
                raise ContractMappingError(f"Native Context {key!r} has no canonical snapshot")
            _merge_context_edit(records[key], self.context_snapshots[key], native, ids)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v1.0.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _typed_optional(value, space, ids, field):
    if value is None:
        return None
    if not isinstance(value, str) or value not in ids:
        raise ValueError(f"{field} reference does not resolve")
    return TypedReference(space, value)


def _project_context(item, ids):
    cid = item["id"]
    mapped = ["id"]
    bad = []

    try:
        kind = ContextKind(item.get("kind"))
    except (TypeError, ValueError):
        return None, mapped, ["kind"]

    try:
        parent = _typed_optional(item.get("parentRef"), ReferenceSpace.CONTEXT,
                                 ids["contexts"], "parentRef")
        source = _typed_optional(item.get("sourceRef"), ReferenceSpace.SOURCE,
                                 ids["sources"], "sourceRef")
        agent = _typed_optional(item.get("agentRef"), ReferenceSpace.REFERENT,
                                 ids["referents"], "agentRef")
    except ValueError as exc:
        return None, mapped, [str(exc)]

    mapped.append("kind")
    for field, value in (("parentRef", parent), ("sourceRef", source), ("agentRef", agent)):
        if value is not None:
            mapped.append(field)

    name = item.get("name")
    if name is not None and not isinstance(name, str):
        return None, mapped, ["name"]
    if "name" in item:
        mapped.append("name")

    metadata = item.get("metadata")
    if metadata is not None and not isinstance(metadata, Mapping):
        return None, mapped, ["metadata"]
    if metadata is not None:
        mapped.append("metadata")
    elif "metadata" in item:
        mapped.append("metadata")

    bad.extend(sorted(set(item) - _CONTEXT_FIELDS))
    native = NativeContextV10(
        external_id=cid, kind=kind, parent_ref=parent, source_ref=source,
        agent_ref=agent, name=name, metadata=metadata,
    )
    return native, mapped, bad


def _require_ref(ref, space, ids, field):
    if not isinstance(ref, TypedReference) or ref.space is not space:
        raise ContractMappingError(f"{field} must be an explicit {space.value} reference")
    if ref.external_id not in ids:
        raise ContractMappingError(f"{field} reference {ref.external_id!r} does not resolve")


def _merge_context_edit(record, snapshot, current, ids):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("Context identity is immutable")
    if not isinstance(current.kind, ContextKind):
        raise ContractMappingError("kind must be a known ContextKind")

    fields = (
        ("parent_ref", "parentRef", ReferenceSpace.CONTEXT, "contexts"),
        ("source_ref", "sourceRef", ReferenceSpace.SOURCE, "sources"),
        ("agent_ref", "agentRef", ReferenceSpace.REFERENT, "referents"),
    )
    for attr, field, space, collection in fields:
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if after is None:
                record.pop(field, None)
            else:
                _require_ref(after, space, ids[collection], field)
                record[field] = after.external_id

    if current.kind != snapshot.kind:
        record["kind"] = current.kind.value
    if current.name != snapshot.name:
        if current.name is None:
            record.pop("name", None)
        elif isinstance(current.name, str):
            record["name"] = current.name
        else:
            raise ContractMappingError("name must be a string or None")
    if current.metadata != snapshot.metadata:
        if current.metadata is None:
            record.pop("metadata", None)
        elif isinstance(current.metadata, Mapping) and all(
            isinstance(key, str) for key in current.metadata
        ):
            record["metadata"] = copy.deepcopy(dict(current.metadata))
        else:
            raise ContractMappingError("metadata must be a string-keyed mapping or None")


def document_to_kernel_v10(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV10Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    ids = {collection: _ids(payload, collection) for collection in
           ("contexts", "sources", "referents")}
    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []

    for item in payload.get("contexts", []):
        native, fields, bad = _project_context(item, ids)
        if native is None:
            bad = sorted(set(bad + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {
                "status": "UNMAPPED", "mappedFields": fields, "unmappedFields": bad,
                "notes": ["Complete Context remains canonical-only; no required field was guessed or coerced."],
            }
            diagnostics.append(f"context {item['id']} remains canonical-only: " + ", ".join(bad))
            continue
        natives[item["id"]] = native
        snapshots[item["id"]] = native
        bad = sorted(set(bad))
        status = "PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad:
            diagnostics.append(f"context {item['id']} has canonical-only fields: " + ", ".join(bad))
        entries[item["id"]] = {
            "status": status, "mappedFields": fields, "unmappedFields": bad,
            "notes": ["Unsupported fields remain canonical-only."] if bad else [],
        }

    mapping = {
        "contexts": {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
            "notes": [
                "Context identity is its opaque Context ID.",
                "Parent, Source, and agent references use distinct typed spaces.",
                "Context kind does not establish truth or authorize scope propagation.",
            ],
        }
    }
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "contexts":
            continue
        refs = sorted(_ids(payload, collection))
        canonical.extend(refs)
        mapping[collection] = {
            "status": "UNMAPPED" if refs else "LOSSLESS", "mapped": [],
            "unmappedRefs": refs,
            "notes": ["Preserved in canonical envelope; not projected by this adapter."] if refs else [],
        }
    defs = payload.get("definitions") or {}
    definition_ids = sorted({
        item["id"] for group in ("concepts", "frames", "roles", "relations")
        for item in defs.get(group, [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    })
    canonical.extend(definition_ids)
    mapping["definitions"] = {
        "status": "UNMAPPED" if definition_ids else "LOSSLESS",
        "mapped": [], "unmappedRefs": definition_ids,
        "notes": ["Definitions remain canonical-only."] if definition_ids else [],
    }
    for key in ("validation", "mapping", "extensions"):
        mapping[key] = {
            "status": "PRESERVED", "mapped": [], "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted to native kernel authority."],
        }

    all_unmapped = sorted(set(canonical + unmapped))
    report = {
        "sourceProfile": "USG-SEM/1.0", "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel", "targetVersion": MODEL_VERSION,
        "status": "PARTIAL" if all_unmapped else "LOSSLESS",
        "unmappedRefs": all_unmapped, "recordMapping": copy.deepcopy(mapping),
        "notes": [
            "Complete canonical document remains authoritative.",
            "Only exact, resolvable Context records project into native v1.0.0.",
            "All non-Context record families remain canonical-only in this adapter.",
            "No context inheritance, truth, attitude, or scope propagation is inferred.",
        ],
    }
    return KernelV10Document(
        payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v10_document_to_contract(imported: KernelV10Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV10Document):
        raise TypeError("imported must be KernelV10Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
