"""Loss-preserving USG-SEM/1.0 UnresolvedItem adapter for native model v1.2.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_unresolved_model():
    try:
        import usg_unresolved_v12 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_unresolved_v12":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v1.2.0" / "usg_unresolved_v12")
    spec = importlib.util.spec_from_file_location(
        "usg_unresolved_v12", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native UnresolvedItem model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_unresolved_v12"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_unresolved_model()
MODEL_VERSION = _model.MODEL_VERSION
UnresolvedStatus = _model.UnresolvedStatus
NativeUnresolvedItemV12 = _model.NativeUnresolvedItemV12

_ITEM_FIELDS = {
    "id", "status", "reason", "surfaceText", "scopeRef", "scopeLabel",
    "evidenceRefs", "candidateRefs", "nativeStatus",
}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV12Document:
    document: dict[str, Any]
    original_digest: str
    unresolved_items: dict[str, NativeUnresolvedItemV12]
    item_snapshots: dict[str, NativeUnresolvedItemV12]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale UnresolvedItem merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("unresolvedItems", [])}
        evidence_ids = _ids(result, "evidence")
        for key, native in self.unresolved_items.items():
            if not isinstance(native, NativeUnresolvedItemV12):
                raise ContractMappingError(f"Non-NativeUnresolvedItemV12 record for {key}")
            if native.external_id != key:
                raise ContractMappingError(f"UnresolvedItem key {key!r} does not match opaque ID")
            if key not in records or key not in self.item_snapshots:
                raise ContractMappingError(f"UnresolvedItem {key!r} has no canonical snapshot")
            _merge_item_edit(records[key], self.item_snapshots[key], native, evidence_ids)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v1.2.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _project_item(item, evidence_ids):
    iid = item["id"]
    mapped = ["id"]
    bad = []
    try:
        status = UnresolvedStatus(item.get("status"))
    except (TypeError, ValueError):
        return None, mapped, ["status"]

    reason = item.get("reason")
    if not isinstance(reason, str):
        return None, mapped, ["reason"]
    mapped.extend(["status", "reason"])

    optional = {}
    for field, native_field in (
        ("surfaceText", "surface_text"), ("scopeRef", "scope_ref"),
        ("scopeLabel", "scope_label"), ("nativeStatus", "native_status"),
    ):
        value = item.get(field)
        if value is not None and not isinstance(value, str):
            return None, mapped, [field]
        optional[native_field] = value
        if field in item:
            mapped.append(field)

    raw_evidence = item.get("evidenceRefs", [])
    if not isinstance(raw_evidence, list) or any(
        not isinstance(ref, str) or not ref or ref not in evidence_ids
        for ref in raw_evidence
    ):
        return None, mapped, ["evidenceRefs must contain resolvable Evidence IDs"]
    evidence_refs = tuple(raw_evidence)
    if "evidenceRefs" in item:
        mapped.append("evidenceRefs")

    raw_candidates = item.get("candidateRefs", [])
    if not isinstance(raw_candidates, list) or any(
        not isinstance(ref, str) or not ref for ref in raw_candidates
    ):
        return None, mapped, ["candidateRefs must contain non-empty opaque strings"]
    candidate_refs = tuple(raw_candidates)
    if "candidateRefs" in item:
        mapped.append("candidateRefs")

    bad.extend(sorted(set(item) - _ITEM_FIELDS))
    native = NativeUnresolvedItemV12(
        external_id=iid, status=status, reason=reason,
        evidence_refs=evidence_refs, candidate_refs=candidate_refs, **optional,
    )
    return native, mapped, bad


def _merge_item_edit(record, snapshot, current, evidence_ids):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("UnresolvedItem identity is immutable")
    if not isinstance(current.status, UnresolvedStatus):
        raise ContractMappingError("status must be a known UnresolvedStatus")
    if not isinstance(current.reason, str):
        raise ContractMappingError("reason must be a string")

    if current.status != snapshot.status:
        record["status"] = current.status.value
    if current.reason != snapshot.reason:
        record["reason"] = current.reason

    for attr, field in (
        ("surface_text", "surfaceText"), ("scope_ref", "scopeRef"),
        ("scope_label", "scopeLabel"), ("native_status", "nativeStatus"),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if after is None:
                record.pop(field, None)
            elif isinstance(after, str):
                record[field] = after
            else:
                raise ContractMappingError(f"{field} must be a string or None")

    if current.evidence_refs != snapshot.evidence_refs:
        if not isinstance(current.evidence_refs, tuple):
            raise ContractMappingError("evidence_refs must be an ordered tuple")
        if any(not isinstance(ref, str) or not ref or ref not in evidence_ids
               for ref in current.evidence_refs):
            raise ContractMappingError("evidence_refs must contain resolvable Evidence IDs")
        record["evidenceRefs"] = list(current.evidence_refs)

    if current.candidate_refs != snapshot.candidate_refs:
        if not isinstance(current.candidate_refs, tuple):
            raise ContractMappingError("candidate_refs must be an ordered tuple")
        if any(not isinstance(ref, str) or not ref for ref in current.candidate_refs):
            raise ContractMappingError("candidate_refs must contain non-empty opaque strings")
        record["candidateRefs"] = list(current.candidate_refs)


def document_to_kernel_v12(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV12Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    evidence_ids = _ids(payload, "evidence")
    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []

    for item in payload.get("unresolvedItems", []):
        native, fields, bad = _project_item(item, evidence_ids)
        if native is None:
            bad = sorted(set(bad + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {
                "status": "UNMAPPED", "mappedFields": fields, "unmappedFields": bad,
                "notes": ["Complete UnresolvedItem remains canonical-only; no required field was guessed or coerced."],
            }
            diagnostics.append(f"unresolvedItem {item['id']} remains canonical-only: " + ", ".join(bad))
            continue
        natives[item["id"]] = native
        snapshots[item["id"]] = native
        bad = sorted(set(bad))
        status = "PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad:
            diagnostics.append(f"unresolvedItem {item['id']} has canonical-only fields: " + ", ".join(bad))
        entries[item["id"]] = {
            "status": status, "mappedFields": fields, "unmappedFields": bad,
            "notes": ["Unsupported fields remain canonical-only."] if bad else [],
        }

    mapping = {
        "unresolvedItems": {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
            "notes": [
                "Scope and candidate references remain opaque where the contract does not define their target spaces.",
                "Evidence references resolve against the canonical Evidence collection.",
                "Unresolved status does not infer a semantic interpretation.",
            ],
        }
    }
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "unresolvedItems":
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
            "Only exact UnresolvedItem records project into native v1.2.0.",
            "All non-UnresolvedItem record families remain canonical-only in this adapter.",
            "No scope resolution, candidate ranking, or semantic status transition is inferred.",
        ],
    }
    return KernelV12Document(
        payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v12_document_to_contract(imported: KernelV12Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV12Document):
        raise TypeError("imported must be KernelV12Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
