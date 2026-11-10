"""Loss-preserving USG-SEM/1.0 ExpressionRelation adapter for native model v1.1.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_relation_model():
    try:
        import usg_expression_relation_v11 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_expression_relation_v11":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v1.1.0" /
                   "usg_expression_relation_v11")
    spec = importlib.util.spec_from_file_location(
        "usg_expression_relation_v11", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native ExpressionRelation model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_expression_relation_v11"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_relation_model()
MODEL_VERSION = _model.MODEL_VERSION
RelationType = _model.RelationType
VerificationStatus = _model.VerificationStatus
NativeExpressionRelationV11 = _model.NativeExpressionRelationV11
ReferenceSpace = _model.ReferenceSpace
TypedReference = _model.TypedReference

_RELATION_FIELDS = {
    "id", "type", "sourceExpressionRef", "targetExpressionRef",
    "verificationStatus", "evidenceRefs", "attribution",
}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV11Document:
    document: dict[str, Any]
    original_digest: str
    expression_relations: dict[str, NativeExpressionRelationV11]
    relation_snapshots: dict[str, NativeExpressionRelationV11]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale ExpressionRelation merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("expressionRelations", [])}
        ids = {"expressions": _ids(result, "expressions"), "evidence": _ids(result, "evidence")}
        for key, native in self.expression_relations.items():
            if not isinstance(native, NativeExpressionRelationV11):
                raise ContractMappingError(f"Non-NativeExpressionRelationV11 record for {key}")
            if native.external_id != key:
                raise ContractMappingError(f"ExpressionRelation key {key!r} does not match opaque ID")
            if key not in records or key not in self.relation_snapshots:
                raise ContractMappingError(f"ExpressionRelation {key!r} has no canonical snapshot")
            _merge_relation_edit(records[key], self.relation_snapshots[key], native, ids)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v1.1.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _typed_ref(value, space, ids, field):
    if not isinstance(value, str) or value not in ids:
        raise ValueError(f"{field} reference does not resolve")
    return TypedReference(space, value)


def _project_relation(item, ids):
    rid = item["id"]
    mapped = ["id"]
    bad = []
    try:
        relation_type = RelationType(item.get("type"))
        verification = VerificationStatus(item.get("verificationStatus"))
    except (TypeError, ValueError):
        return None, mapped, ["type or verificationStatus"]

    try:
        source = _typed_ref(item.get("sourceExpressionRef"), ReferenceSpace.EXPRESSION,
                            ids["expressions"], "sourceExpressionRef")
        target = _typed_ref(item.get("targetExpressionRef"), ReferenceSpace.EXPRESSION,
                            ids["expressions"], "targetExpressionRef")
        raw_evidence = item.get("evidenceRefs", [])
        if not isinstance(raw_evidence, list):
            raise ValueError("evidenceRefs must be an array")
        evidence = tuple(_typed_ref(x, ReferenceSpace.EVIDENCE, ids["evidence"], "evidenceRefs")
                         for x in raw_evidence)
    except ValueError as exc:
        return None, mapped, [str(exc)]

    mapped.extend(["type", "sourceExpressionRef", "targetExpressionRef", "verificationStatus"])
    if "evidenceRefs" in item:
        mapped.append("evidenceRefs")
    attribution = item.get("attribution")
    if attribution is not None and not isinstance(attribution, Mapping):
        return None, mapped, ["attribution"]
    if "attribution" in item:
        mapped.append("attribution")
    bad.extend(sorted(set(item) - _RELATION_FIELDS))
    native = NativeExpressionRelationV11(
        external_id=rid, relation_type=relation_type,
        source_expression_ref=source, target_expression_ref=target,
        verification_status=verification, evidence_refs=evidence,
        attribution=attribution,
    )
    return native, mapped, bad


def _require_ref(ref, space, ids, field):
    if not isinstance(ref, TypedReference) or ref.space is not space:
        raise ContractMappingError(f"{field} must be an explicit {space.value} reference")
    if ref.external_id not in ids:
        raise ContractMappingError(f"{field} reference {ref.external_id!r} does not resolve")


def _merge_relation_edit(record, snapshot, current, ids):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("ExpressionRelation identity is immutable")
    if not isinstance(current.relation_type, RelationType):
        raise ContractMappingError("type must be a known RelationType")
    if not isinstance(current.verification_status, VerificationStatus):
        raise ContractMappingError("verificationStatus must be a known VerificationStatus")

    for attr, field in (
        ("source_expression_ref", "sourceExpressionRef"),
        ("target_expression_ref", "targetExpressionRef"),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            _require_ref(after, ReferenceSpace.EXPRESSION, ids["expressions"], field)
            record[field] = after.external_id

    if current.relation_type != snapshot.relation_type:
        record["type"] = current.relation_type.value
    if current.verification_status != snapshot.verification_status:
        record["verificationStatus"] = current.verification_status.value

    if current.evidence_refs != snapshot.evidence_refs:
        if not isinstance(current.evidence_refs, tuple):
            raise ContractMappingError("evidence_refs must be an ordered tuple")
        for ref in current.evidence_refs:
            _require_ref(ref, ReferenceSpace.EVIDENCE, ids["evidence"], "evidenceRefs")
        record["evidenceRefs"] = [ref.external_id for ref in current.evidence_refs]

    if current.attribution != snapshot.attribution:
        if current.attribution is None:
            record.pop("attribution", None)
        elif isinstance(current.attribution, Mapping) and all(
            isinstance(key, str) for key in current.attribution
        ):
            record["attribution"] = copy.deepcopy(dict(current.attribution))
        else:
            raise ContractMappingError("attribution must be a string-keyed mapping or None")


def document_to_kernel_v11(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV11Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    ids = {"expressions": _ids(payload, "expressions"), "evidence": _ids(payload, "evidence")}
    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []

    for item in payload.get("expressionRelations", []):
        native, fields, bad = _project_relation(item, ids)
        if native is None:
            bad = sorted(set(bad + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {
                "status": "UNMAPPED", "mappedFields": fields, "unmappedFields": bad,
                "notes": ["Complete ExpressionRelation remains canonical-only; no required field was guessed or coerced."],
            }
            diagnostics.append(f"expressionRelation {item['id']} remains canonical-only: " + ", ".join(bad))
            continue
        natives[item["id"]] = native
        snapshots[item["id"]] = native
        bad = sorted(set(bad))
        status = "PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad:
            diagnostics.append(f"expressionRelation {item['id']} has canonical-only fields: " + ", ".join(bad))
        entries[item["id"]] = {
            "status": status, "mappedFields": fields, "unmappedFields": bad,
            "notes": ["Unsupported fields remain canonical-only."] if bad else [],
        }

    mapping = {
        "expressionRelations": {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
            "notes": [
                "ExpressionRelation source and target references are directed.",
                "Evidence references are typed, ordered, and may repeat.",
                "Verification status is explicit and does not trigger relation reasoning.",
            ],
        }
    }
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "expressionRelations":
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
            "Only exact, resolvable ExpressionRelation records project into native v1.1.0.",
            "All non-ExpressionRelation record families remain canonical-only in this adapter.",
            "No relation verification, entailment, causality, contradiction, or coreference is inferred.",
        ],
    }
    return KernelV11Document(
        payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v11_document_to_contract(imported: KernelV11Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV11Document):
        raise TypeError("imported must be KernelV11Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
