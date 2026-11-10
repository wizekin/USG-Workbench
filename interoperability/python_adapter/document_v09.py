"""Loss-preserving USG-SEM/1.0 Evidence adapter for native model v0.9.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_evidence_model():
    try:
        import usg_evidence_v09 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_evidence_v09":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v0.9.0" / "usg_evidence_v09")
    spec = importlib.util.spec_from_file_location(
        "usg_evidence_v09", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native Evidence model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_evidence_v09"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_evidence_model()
MODEL_VERSION = _model.MODEL_VERSION
AlignmentStatus = _model.AlignmentStatus
SemanticSupportStatus = _model.SemanticSupportStatus
EvidenceSpan = _model.EvidenceSpan
NativeEvidenceV09 = _model.NativeEvidenceV09
ReferenceSpace = _model.ReferenceSpace
TypedReference = _model.TypedReference

_EVIDENCE_FIELDS = {
    "id", "sourceRef", "span", "quote", "alignmentStatus",
    "semanticSupportStatus", "supportingRuleRefs", "nativeVerificationMeaning",
}
_SPAN_FIELDS = {"sourceRef", "start", "end", "offsetUnit"}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions",
    "evidence", "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV09Document:
    document: dict[str, Any]
    original_digest: str
    evidence: dict[str, NativeEvidenceV09]
    evidence_snapshots: dict[str, NativeEvidenceV09]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale native Evidence merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("evidence", [])}
        source_ids = _ids(result, "sources")
        for key, native in self.evidence.items():
            if not isinstance(native, NativeEvidenceV09):
                raise ContractMappingError(f"Non-NativeEvidenceV09 record for {key}")
            if native.external_id != key:
                raise ContractMappingError(f"Native Evidence key {key!r} does not match opaque ID")
            if key not in records or key not in self.evidence_snapshots:
                raise ContractMappingError(f"Native Evidence {key!r} has no canonical snapshot")
            _merge_evidence_edit(records[key], self.evidence_snapshots[key], native, source_ids)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v0.9.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _enum(cls, value):
    try:
        return cls(value)
    except (ValueError, TypeError):
        return None


def _project_evidence(item, source_ids):
    eid = item["id"]
    mapped = ["id"]
    bad = []

    source_ref = item.get("sourceRef")
    if not isinstance(source_ref, str) or source_ref not in source_ids:
        return None, mapped, ["sourceRef"]

    span = item.get("span")
    if not isinstance(span, Mapping):
        return None, mapped, ["span"]
    span_source = span.get("sourceRef")
    if span_source != source_ref:
        return None, mapped, ["span.sourceRef"]
    start, end, unit = span.get("start"), span.get("end"), span.get("offsetUnit")
    try:
        native_span = EvidenceSpan(
            TypedReference(ReferenceSpace.SOURCE, source_ref), start, end, unit)
    except (TypeError, ValueError):
        return None, mapped, ["span.start", "span.end", "span.offsetUnit"]
    mapped.extend(["sourceRef", "span.sourceRef", "span.start", "span.end", "span.offsetUnit"])
    bad.extend("span." + key for key in sorted(set(span) - _SPAN_FIELDS))

    quote = item.get("quote")
    if not isinstance(quote, str):
        return None, mapped, bad + ["quote"]
    mapped.append("quote")

    alignment = _enum(AlignmentStatus, item.get("alignmentStatus"))
    support = _enum(SemanticSupportStatus, item.get("semanticSupportStatus"))
    if alignment is None or support is None:
        missing = []
        if alignment is None:
            missing.append("alignmentStatus")
        if support is None:
            missing.append("semanticSupportStatus")
        return None, mapped, bad + missing
    mapped.extend(["alignmentStatus", "semanticSupportStatus"])

    raw_rules = item.get("supportingRuleRefs", [])
    if isinstance(raw_rules, list) and all(isinstance(x, str) and x for x in raw_rules):
        rules = tuple(raw_rules)
        mapped.append("supportingRuleRefs")
    else:
        rules = ()
        bad.append("supportingRuleRefs")

    native_meaning = item.get("nativeVerificationMeaning")
    if native_meaning is None or isinstance(native_meaning, str):
        mapped.append("nativeVerificationMeaning")
    else:
        native_meaning = None
        bad.append("nativeVerificationMeaning")

    bad.extend(sorted(set(item) - _EVIDENCE_FIELDS))
    native = NativeEvidenceV09(
        external_id=eid,
        source_ref=TypedReference(ReferenceSpace.SOURCE, source_ref),
        span=native_span,
        quote=quote,
        alignment_status=alignment,
        semantic_support_status=support,
        supporting_rule_refs=rules,
        native_verification_meaning=native_meaning,
    )
    return native, mapped, bad


def _require_source(ref, source_ids):
    if not isinstance(ref, TypedReference) or ref.space is not ReferenceSpace.SOURCE:
        raise ContractMappingError("Reference must explicitly target SOURCE")
    if ref.external_id not in source_ids:
        raise ContractMappingError(
            f"SOURCE reference {ref.external_id!r} does not resolve in canonical document")


def _merge_evidence_edit(record, snapshot, current, source_ids):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("Evidence identity is immutable")
    if not isinstance(current.span, EvidenceSpan) or current.span.source_ref != current.source_ref:
        raise ContractMappingError("Evidence span Source must match Evidence source_ref")

    if current.source_ref != snapshot.source_ref:
        _require_source(current.source_ref, source_ids)
        record["sourceRef"] = current.source_ref.external_id

    if current.span != snapshot.span:
        _require_source(current.span.source_ref, source_ids)
        if current.span.source_ref != current.source_ref:
            raise ContractMappingError("Evidence span Source must match Evidence source_ref")
        record["span"] = {
            "sourceRef": current.span.source_ref.external_id,
            "start": current.span.start,
            "end": current.span.end,
            "offsetUnit": current.span.offset_unit,
        }

    if current.quote != snapshot.quote:
        if not isinstance(current.quote, str):
            raise ContractMappingError("quote must be a string")
        record["quote"] = current.quote

    for attr, field, cls in (
        ("alignment_status", "alignmentStatus", AlignmentStatus),
        ("semantic_support_status", "semanticSupportStatus", SemanticSupportStatus),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if not isinstance(after, cls):
                raise ContractMappingError(f"{field} must be a known {cls.__name__}")
            record[field] = after.value

    if current.supporting_rule_refs != snapshot.supporting_rule_refs:
        if not isinstance(current.supporting_rule_refs, tuple):
            raise ContractMappingError("supporting_rule_refs must be an ordered tuple")
        if any(not isinstance(x, str) or not x for x in current.supporting_rule_refs):
            raise ContractMappingError("supporting_rule_refs must contain non-empty strings")
        record["supportingRuleRefs"] = list(current.supporting_rule_refs)

    if current.native_verification_meaning != snapshot.native_verification_meaning:
        if current.native_verification_meaning is None:
            record.pop("nativeVerificationMeaning", None)
        elif isinstance(current.native_verification_meaning, str):
            record["nativeVerificationMeaning"] = current.native_verification_meaning
        else:
            raise ContractMappingError("native_verification_meaning must be string or None")


def document_to_kernel_v09(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV09Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    source_ids = _ids(payload, "sources")
    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []

    for item in payload.get("evidence", []):
        native, fields, bad = _project_evidence(item, source_ids)
        if native is None:
            bad = sorted(set(bad + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {
                "status": "UNMAPPED", "mappedFields": fields,
                "unmappedFields": bad,
                "notes": ["Complete Evidence remains canonical-only; no required field was guessed or coerced."],
            }
            diagnostics.append(f"evidence {item['id']} remains canonical-only: " + ", ".join(bad))
            continue

        natives[item["id"]] = native
        snapshots[item["id"]] = native
        bad = sorted(set(bad))
        status = "PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad:
            diagnostics.append(f"evidence {item['id']} has canonical-only fields: " + ", ".join(bad))
        entries[item["id"]] = {
            "status": status, "mappedFields": fields, "unmappedFields": bad,
            "notes": ["Unsupported fields remain canonical-only."] if bad else [],
        }

    mapping = {
        "evidence": {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
            "notes": [
                "Evidence identity is its opaque Evidence ID.",
                "Source-span alignment and semantic-support status are independent.",
                "EXACT alignment does not establish entailment, corroboration, or truth.",
            ],
        }
    }
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "evidence":
            continue
        ids = sorted(_ids(payload, collection))
        canonical.extend(ids)
        mapping[collection] = {
            "status": "UNMAPPED" if ids else "LOSSLESS",
            "mapped": [], "unmappedRefs": ids,
            "notes": ["Preserved in canonical envelope; not projected by this adapter."] if ids else [],
        }
    defs = payload.get("definitions") or {}
    definition_ids = sorted({
        item["id"]
        for group in ("concepts", "frames", "roles", "relations")
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
            "Only exact, resolvable Evidence fields project into native v0.9.0.",
            "All non-Evidence record families remain canonical-only in this adapter.",
            "No source alignment, entailment, truth, or semantic-support status is inferred.",
        ],
    }
    return KernelV09Document(
        payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v09_document_to_contract(imported: KernelV09Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV09Document):
        raise TypeError("imported must be KernelV09Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
