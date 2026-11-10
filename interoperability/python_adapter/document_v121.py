"""Loss-preserving USG-SEM/1.0 UnresolvedItem adapter v1.2.1."""
from __future__ import annotations
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_model():
    try:
        import usg_unresolved_v121 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_unresolved_v121":
            raise
    import importlib.util, sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations/python-kernel/v1.2.1/usg_unresolved_v121")
    spec = importlib.util.spec_from_file_location(
        "usg_unresolved_v121", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native UnresolvedItem model v1.2.1")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_unresolved_v121"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_model()
MODEL_VERSION = _model.MODEL_VERSION
UnresolvedStatus = _model.UnresolvedStatus
ReferenceSpace = _model.ReferenceSpace
TypedReference = _model.TypedReference
NativeUnresolvedItemV121 = _model.NativeUnresolvedItemV121

_FIELDS = {"id", "status", "reason", "surfaceText", "scopeRef", "scopeLabel",
           "evidenceRefs", "candidateRefs", "nativeStatus"}
_COLLECTIONS = ("sources", "referents", "mentions", "expressions", "assertions",
                "evidence", "contexts", "expressionRelations", "unresolvedItems", "derivations")


@dataclass
class KernelV121Document:
    document: dict[str, Any]
    original_digest: str
    unresolved_items: dict[str, NativeUnresolvedItemV121]
    snapshots: dict[str, NativeUnresolvedItemV121]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate=True, schema_path=SCHEMA_PATH):
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError("Canonical document snapshot is stale; refusing UnresolvedItem merge")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("unresolvedItems", [])}
        expressions = _ids(result, "expressions")
        evidence = _ids(result, "evidence")
        for key, native in self.unresolved_items.items():
            if not isinstance(native, NativeUnresolvedItemV121) or native.external_id != key:
                raise ContractMappingError(f"Invalid native UnresolvedItem identity for {key}")
            if key not in records or key not in self.snapshots:
                raise ContractMappingError(f"UnresolvedItem {key} has no canonical snapshot")
            _merge(records[key], self.snapshots[key], native, expressions, evidence)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError("Invalid serialized USG-SEM document: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {x["id"] for x in doc.get(collection, []) if isinstance(x, Mapping) and isinstance(x.get("id"), str)}


def _project(item, expressions, evidence):
    uid = item["id"]
    mapped = ["id"]
    try:
        status = UnresolvedStatus(item.get("status"))
    except (TypeError, ValueError):
        return None, mapped, ["status"]
    if not isinstance(item.get("reason"), str):
        return None, mapped, ["reason"]
    mapped.extend(["status", "reason"])

    optional = {}
    for field, native in (("surfaceText", "surface_text"), ("scopeLabel", "scope_label"),
                          ("nativeStatus", "native_status")):
        value = item.get(field)
        if value is not None and not isinstance(value, str):
            return None, mapped, [field]
        optional[native] = value
        if field in item:
            mapped.append(field)

    scope = item.get("scopeRef")
    if scope is not None:
        if not isinstance(scope, str) or scope not in expressions:
            return None, mapped, ["scopeRef must resolve to an Expression"]
        scope = TypedReference(ReferenceSpace.EXPRESSION, scope)
        mapped.append("scopeRef")

    raw_evidence = item.get("evidenceRefs", [])
    if not isinstance(raw_evidence, list) or any(
        not isinstance(ref, str) or not ref or ref not in evidence for ref in raw_evidence
    ):
        return None, mapped, ["evidenceRefs must contain resolvable Evidence IDs"]
    evidence_refs = tuple(TypedReference(ReferenceSpace.EVIDENCE, ref) for ref in raw_evidence)
    if "evidenceRefs" in item:
        mapped.append("evidenceRefs")

    raw_candidates = item.get("candidateRefs", [])
    if not isinstance(raw_candidates, list) or any(not isinstance(ref, str) or not ref for ref in raw_candidates):
        return None, mapped, ["candidateRefs must contain non-empty opaque strings"]
    candidate_refs = tuple(raw_candidates)
    if "candidateRefs" in item:
        mapped.append("candidateRefs")

    unknown = sorted(set(item) - _FIELDS)
    native = NativeUnresolvedItemV121(
        external_id=uid, status=status, reason=item["reason"],
        scope_ref=scope, evidence_refs=evidence_refs,
        candidate_refs=candidate_refs, **optional,
    )
    return native, mapped, unknown


def _require_ref(ref, space, known, field):
    if not isinstance(ref, TypedReference) or ref.space is not space:
        raise ContractMappingError(f"{field} must be a typed {space.value} reference")
    if ref.external_id not in known:
        raise ContractMappingError(f"{field} reference {ref.external_id!r} does not resolve")


def _merge(record, snapshot, current, expressions, evidence):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("UnresolvedItem identity is immutable")
    if current.status != snapshot.status:
        if not isinstance(current.status, UnresolvedStatus):
            raise ContractMappingError("status must be UnresolvedStatus")
        record["status"] = current.status.value
    if current.reason != snapshot.reason:
        if not isinstance(current.reason, str):
            raise ContractMappingError("reason must be a string")
        record["reason"] = current.reason

    if current.scope_ref != snapshot.scope_ref:
        if current.scope_ref is None:
            record.pop("scopeRef", None)
        else:
            _require_ref(current.scope_ref, ReferenceSpace.EXPRESSION, expressions, "scopeRef")
            record["scopeRef"] = current.scope_ref.external_id

    if current.evidence_refs != snapshot.evidence_refs:
        if not isinstance(current.evidence_refs, tuple):
            raise ContractMappingError("evidence_refs must be an ordered tuple")
        for ref in current.evidence_refs:
            _require_ref(ref, ReferenceSpace.EVIDENCE, evidence, "evidenceRefs")
        record["evidenceRefs"] = [ref.external_id for ref in current.evidence_refs]

    if current.candidate_refs != snapshot.candidate_refs:
        if not isinstance(current.candidate_refs, tuple) or any(
            not isinstance(ref, str) or not ref for ref in current.candidate_refs
        ):
            raise ContractMappingError("candidate_refs must be non-empty opaque strings")
        record["candidateRefs"] = list(current.candidate_refs)

    for attr, field in (("surface_text", "surfaceText"), ("scope_label", "scopeLabel"),
                        ("native_status", "nativeStatus")):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if after is None:
                record.pop(field, None)
            elif isinstance(after, str):
                record[field] = after
            else:
                raise ContractMappingError(f"{field} must be a string or None")


def document_to_kernel_v121(document: Mapping[str, Any], *, validate=True,
                            schema_path=SCHEMA_PATH) -> KernelV121Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    expressions, evidence = _ids(payload, "expressions"), _ids(payload, "evidence")
    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []
    for item in payload.get("unresolvedItems", []):
        native, fields, unknown = _project(item, expressions, evidence)
        if native is None:
            unknown = sorted(set(unknown + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {"status": "UNMAPPED", "mappedFields": fields,
                                   "unmappedFields": unknown, "notes": ["Complete item remains canonical-only."]}
            diagnostics.append(f"unresolvedItem {item['id']} remains canonical-only: " + ", ".join(unknown))
            continue
        natives[item["id"]] = native
        snapshots[item["id"]] = native
        unknown = sorted(set(unknown))
        status = "PARTIAL" if unknown else "LOSSLESS"
        (unmapped if unknown else mapped).append(item["id"])
        entries[item["id"]] = {"status": status, "mappedFields": fields,
                               "unmappedFields": unknown,
                               "notes": ["Unknown fields remain canonical-only."] if unknown else []}

    mapping = {"unresolvedItems": {
        "status": "PARTIAL" if unmapped else "LOSSLESS",
        "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
        "notes": [
            "scopeRef resolves to a typed Expression reference.",
            "evidenceRefs resolve to typed Evidence references and preserve order/repetition.",
            "candidateRefs remain opaque because the contract does not define their target record family.",
        ],
    }}
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "unresolvedItems":
            continue
        refs = sorted(_ids(payload, collection))
        canonical.extend(refs)
        mapping[collection] = {"status": "UNMAPPED" if refs else "LOSSLESS",
                               "mapped": [], "unmappedRefs": refs,
                               "notes": ["Preserved in canonical envelope."] if refs else []}
    for key in ("validation", "mapping", "extensions"):
        mapping[key] = {"status": "PRESERVED", "mapped": [], "unmappedRefs": [],
                        "notes": ["Preserved verbatim; not promoted to native authority."]}
    unmapped_refs = sorted(set(canonical + unmapped))
    report = {
        "sourceProfile": "USG-SEM/1.0", "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel", "targetVersion": MODEL_VERSION,
        "status": "PARTIAL" if unmapped_refs else "LOSSLESS",
        "unmappedRefs": unmapped_refs, "recordMapping": copy.deepcopy(mapping),
        "notes": [
            "Only exact UnresolvedItem records with resolvable Expression scope and Evidence references project.",
            "All other record families remain canonical-only in this adapter.",
            "No candidate ranking, resolution, or status transition is performed.",
        ],
    }
    return KernelV121Document(payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v121_document_to_contract(imported: KernelV121Document, *, validate=True,
                                     schema_path=SCHEMA_PATH):
    if not isinstance(imported, KernelV121Document):
        raise TypeError("imported must be KernelV121Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
