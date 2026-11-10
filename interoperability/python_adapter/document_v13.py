"""Loss-preserving USG-SEM/1.0 Derivation adapter for native model v1.3.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_derivation_model():
    try:
        import usg_derivation_v13 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_derivation_v13":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v1.3.0" / "usg_derivation_v13")
    spec = importlib.util.spec_from_file_location(
        "usg_derivation_v13", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native Derivation model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_derivation_v13"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_derivation_model()
MODEL_VERSION = _model.MODEL_VERSION
DerivationMethod = _model.DerivationMethod
DerivationStatus = _model.DerivationStatus
DerivationModelInfo = _model.DerivationModelInfo
NativeDerivationV13 = _model.NativeDerivationV13

_DERIVATION_FIELDS = {
    "id", "method", "component", "ruleIds", "inputRefs", "outputRefs",
    "model", "timestamp", "status", "diagnostics",
}
_MODEL_FIELDS = {"provider", "name", "revision"}
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV13Document:
    document: dict[str, Any]
    original_digest: str
    derivations: dict[str, NativeDerivationV13]
    derivation_snapshots: dict[str, NativeDerivationV13]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale Derivation merge.")
        result = copy.deepcopy(self.document)
        records = {x["id"]: x for x in result.get("derivations", [])}
        for key, native in self.derivations.items():
            if not isinstance(native, NativeDerivationV13):
                raise ContractMappingError(f"Non-NativeDerivationV13 record for {key}")
            if native.external_id != key:
                raise ContractMappingError(f"Derivation key {key!r} does not match opaque ID")
            if key not in records or key not in self.derivation_snapshots:
                raise ContractMappingError(f"Derivation {key!r} has no canonical snapshot")
            _merge_derivation_edit(records[key], self.derivation_snapshots[key], native)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v1.3.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _string_tuple(value, field, *, default=()):
    if value is None:
        value = default
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(f"{field} must be an array of non-empty strings")
    return tuple(value)


def _project_derivation(item):
    did = item["id"]
    mapped = ["id"]
    try:
        method = DerivationMethod(item.get("method"))
        status = DerivationStatus(item.get("status"))
    except (TypeError, ValueError):
        return None, mapped, ["method or status"]

    try:
        inputs = _string_tuple(item.get("inputRefs"), "inputRefs")
        outputs = _string_tuple(item.get("outputRefs"), "outputRefs")
        rules = _string_tuple(item.get("ruleIds", []), "ruleIds")
        diagnostics = _string_tuple(item.get("diagnostics", []), "diagnostics")
    except ValueError as exc:
        return None, mapped, [str(exc)]

    mapped.extend(["method", "inputRefs", "outputRefs", "status"])
    for field in ("ruleIds", "diagnostics"):
        if field in item:
            mapped.append(field)

    component = item.get("component")
    timestamp = item.get("timestamp")
    if component is not None and not isinstance(component, str):
        return None, mapped, ["component"]
    if timestamp is not None and not isinstance(timestamp, str):
        return None, mapped, ["timestamp"]
    if "component" in item:
        mapped.append("component")
    if "timestamp" in item:
        mapped.append("timestamp")

    raw_model = item.get("model")
    model = None
    if raw_model is not None:
        if not isinstance(raw_model, Mapping):
            return None, mapped, ["model"]
        known = {key: raw_model.get(key) for key in _MODEL_FIELDS}
        if any(value is not None and not isinstance(value, str) for value in known.values()):
            return None, mapped, ["model.provider/name/revision"]
        extra = {key: copy.deepcopy(value) for key, value in raw_model.items()
                 if key not in _MODEL_FIELDS}
        model = DerivationModelInfo(
            provider=known["provider"], name=known["name"],
            revision=known["revision"], metadata=extra or None,
        )
        mapped.append("model")
    elif "model" in item:
        mapped.append("model")

    bad = sorted(set(item) - _DERIVATION_FIELDS)
    native = NativeDerivationV13(
        external_id=did, method=method, input_refs=inputs, output_refs=outputs,
        status=status, component=component, rule_ids=rules, model=model,
        timestamp=timestamp, diagnostics=diagnostics,
    )
    return native, mapped, bad


def _merge_derivation_edit(record, snapshot, current):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError("Derivation identity is immutable")
    if not isinstance(current.method, DerivationMethod):
        raise ContractMappingError("method must be a known DerivationMethod")
    if not isinstance(current.status, DerivationStatus):
        raise ContractMappingError("status must be a known DerivationStatus")

    for attr, field in (
        ("method", "method"), ("status", "status"),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            record[field] = after.value

    for attr, field in (
        ("component", "component"), ("timestamp", "timestamp"),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if after is None:
                record.pop(field, None)
            elif isinstance(after, str):
                record[field] = after
            else:
                raise ContractMappingError(f"{field} must be a string or None")

    for attr, field in (
        ("input_refs", "inputRefs"), ("output_refs", "outputRefs"),
        ("rule_ids", "ruleIds"), ("diagnostics", "diagnostics"),
    ):
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if not isinstance(after, tuple) or any(not isinstance(x, str) or not x for x in after):
                raise ContractMappingError(f"{field} must be an ordered tuple of non-empty strings")
            record[field] = list(after)

    if current.model != snapshot.model:
        if current.model is None:
            record.pop("model", None)
        elif isinstance(current.model, DerivationModelInfo):
            raw = copy.deepcopy(record.get("model", {}))
            if not isinstance(raw, dict):
                raw = {}
            for field in ("provider", "name", "revision"):
                value = getattr(current.model, field)
                if value is None:
                    raw.pop(field, None)
                elif isinstance(value, str):
                    raw[field] = value
                else:
                    raise ContractMappingError(f"model.{field} must be a string or None")
            if current.model.metadata is not None:
                if not isinstance(current.model.metadata, Mapping) or any(
                    not isinstance(key, str) for key in current.model.metadata
                ):
                    raise ContractMappingError("model metadata must be a string-keyed mapping")
                for key, value in current.model.metadata.items():
                    if key in _MODEL_FIELDS:
                        raise ContractMappingError(f"model metadata cannot override {key}")
                    raw[key] = copy.deepcopy(value)
            record["model"] = raw
        else:
            raise ContractMappingError("model must be DerivationModelInfo or None")


def document_to_kernel_v13(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV13Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    natives, snapshots, entries = {}, {}, {}
    mapped, unmapped, diagnostics = [], [], []

    for item in payload.get("derivations", []):
        native, fields, bad = _project_derivation(item)
        if native is None:
            bad = sorted(set(bad + ["required native projection unavailable"]))
            unmapped.append(item["id"])
            entries[item["id"]] = {
                "status": "UNMAPPED", "mappedFields": fields, "unmappedFields": bad,
                "notes": ["Complete Derivation remains canonical-only; no required field was guessed or coerced."],
            }
            diagnostics.append(f"derivation {item['id']} remains canonical-only: " + ", ".join(bad))
            continue
        natives[item["id"]] = native
        snapshots[item["id"]] = native
        bad = sorted(set(bad))
        state = "PARTIAL" if bad else "LOSSLESS"
        (unmapped if bad else mapped).append(item["id"])
        if bad:
            diagnostics.append(f"derivation {item['id']} has canonical-only fields: " + ", ".join(bad))
        entries[item["id"]] = {
            "status": state, "mappedFields": fields, "unmappedFields": bad,
            "notes": ["Unsupported fields remain canonical-only."] if bad else [],
        }

    mapping = {
        "derivations": {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
            "notes": [
                "Input/output/rule references remain opaque because they may target heterogeneous record families.",
                "Derivation method and status are preserved independently.",
                "Provenance does not certify truth, entailment, or correctness.",
            ],
        }
    }
    canonical = []
    for collection in _COLLECTIONS:
        if collection == "derivations":
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
            "Only exact Derivation records project into native v1.3.0.",
            "All non-Derivation record families remain canonical-only in this adapter.",
            "No inference, verification, or truth evaluation is performed.",
        ],
    }
    return KernelV13Document(
        payload, _digest(payload), natives, snapshots, mapping, report, diagnostics)


def kernel_v13_document_to_contract(imported: KernelV13Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV13Document):
        raise TypeError("imported must be KernelV13Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
