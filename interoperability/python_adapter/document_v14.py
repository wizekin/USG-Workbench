"""Loss-preserving USG-SEM/1.0 Definitions adapter for native model v1.4.0."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _load_definitions_model():
    try:
        import usg_definitions_v14 as model
        return model
    except ModuleNotFoundError as exc:
        if exc.name != "usg_definitions_v14":
            raise
    import importlib.util
    import sys
    package_dir = (Path(__file__).resolve().parents[2] /
                   "implementations" / "python-kernel" / "v1.4.0" / "usg_definitions_v14")
    spec = importlib.util.spec_from_file_location(
        "usg_definitions_v14", package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load native Definitions model")
    model = importlib.util.module_from_spec(spec)
    sys.modules["usg_definitions_v14"] = model
    spec.loader.exec_module(model)
    return model


_model = _load_definitions_model()
MODEL_VERSION = _model.MODEL_VERSION
SemanticKind = _model.SemanticKind
ConceptDefinitionV14 = _model.ConceptDefinitionV14
FrameDefinitionV14 = _model.FrameDefinitionV14
RoleDefinitionV14 = _model.RoleDefinitionV14
RelationDefinitionV14 = _model.RelationDefinitionV14
DefinitionsCatalogueV14 = _model.DefinitionsCatalogueV14

_GROUPS = ("concepts", "frames", "roles", "relations")
_COLLECTIONS = (
    "sources", "referents", "mentions", "expressions", "assertions", "evidence",
    "contexts", "expressionRelations", "unresolvedItems", "derivations",
)


@dataclass
class KernelV14Document:
    document: dict[str, Any]
    original_digest: str
    catalogue: DefinitionsCatalogueV14
    snapshots: dict[str, dict[str, Any]]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing stale Definitions merge.")
        result = copy.deepcopy(self.document)
        definitions = result.get("definitions")
        if not isinstance(definitions, dict):
            raise ContractMappingError("Canonical definitions catalogue is missing")
        groups = {
            "concepts": self.catalogue.concepts,
            "frames": self.catalogue.frames,
            "roles": self.catalogue.roles,
            "relations": self.catalogue.relations,
        }
        for group, natives in groups.items():
            records = {x["id"]: x for x in definitions.get(group, [])}
            for native in natives:
                key = native.external_id
                snapshot = self.snapshots.get(f"{group}:{key}")
                if key not in records or snapshot is None:
                    raise ContractMappingError(f"Definition {group}/{key!r} has no canonical snapshot")
                _merge_definition_edit(records[key], snapshot, native, group)
        _merge_catalogue_versions(definitions, self.document.get("definitions", {}),
                                  self.catalogue)
        if validate:
            problems = validate_contract_document(result, schema_path)
            if problems:
                raise ContractMappingError(
                    "Serialized kernel v1.4.0 document is invalid: " + "; ".join(problems[:20]))
        return result


def _ids(doc, collection):
    return {
        x["id"] for x in doc.get(collection, [])
        if isinstance(x, Mapping) and isinstance(x.get("id"), str)
    }


def _positive_version(value):
    return not isinstance(value, bool) and isinstance(value, int) and value >= 1


def _project_record(group, item):
    rid = item["id"]
    mapped = ["id"]
    known = set()
    try:
        if group == "concepts":
            kind = SemanticKind(item.get("semanticKind"))
            version = item.get("version")
            if not _positive_version(version) or not isinstance(item.get("label"), str):
                raise ValueError("required concept label/version")
            for field in ("definition", "lifecycleStage"):
                value = item.get(field)
                if value is not None and not isinstance(value, str):
                    raise ValueError(field)
            native = ConceptDefinitionV14(
                rid, item["label"], kind, version,
                item.get("definition"), item.get("lifecycleStage"),
            )
            known = {"id", "label", "semanticKind", "version", "definition", "lifecycleStage"}
        elif group == "frames":
            version = item.get("version")
            roles = item.get("roles")
            if not _positive_version(version) or not isinstance(item.get("label"), str):
                raise ValueError("required frame label/version")
            if not isinstance(roles, list) or any(not isinstance(x, str) or not x for x in roles):
                raise ValueError("roles")
            raw_kind = item.get("semanticKind")
            kind = SemanticKind(raw_kind) if raw_kind is not None else None
            native = FrameDefinitionV14(rid, item["label"], version, tuple(roles), kind)
            known = {"id", "label", "version", "roles", "semanticKind"}
        elif group == "roles":
            if not isinstance(item.get("label"), str):
                raise ValueError("required role label")
            constraints = item.get("constraints")
            if constraints is not None and not isinstance(constraints, Mapping):
                raise ValueError("constraints")
            native = RoleDefinitionV14(rid, item["label"], constraints)
            known = {"id", "label", "constraints"}
        elif group == "relations":
            if not isinstance(item.get("label"), str):
                raise ValueError("required relation label")
            properties = item.get("properties")
            if properties is not None and not isinstance(properties, Mapping):
                raise ValueError("properties")
            native = RelationDefinitionV14(rid, item["label"], properties)
            known = {"id", "label", "properties"}
        else:
            raise ValueError(f"unsupported definition group {group}")
    except (TypeError, ValueError) as exc:
        return None, mapped, [str(exc)]

    mapped.extend(sorted(key for key in known - {"id"} if key in item))
    extras = {key: copy.deepcopy(value) for key, value in item.items() if key not in known}
    if extras:
        native = _with_extras(native, extras)
    bad = sorted(extras)
    return native, mapped, bad


def _with_extras(native, extras):
    from dataclasses import replace
    return replace(native, canonical_extras=extras)


def _merge_definition_edit(record, snapshot, current, group):
    if current.external_id != snapshot.external_id:
        raise ContractMappingError(f"{group} definition identity is immutable")
    if current.canonical_extras != snapshot.canonical_extras:
        raise ContractMappingError(f"{group} canonical-only extras are immutable in this adapter")

    if group == "concepts":
        if not isinstance(current.semantic_kind, SemanticKind):
            raise ContractMappingError("concept semantic_kind must be a known SemanticKind")
        fields = (("label", "label"), ("version", "version"),
                  ("semantic_kind", "semanticKind"), ("definition", "definition"),
                  ("lifecycle_stage", "lifecycleStage"))
    elif group == "frames":
        if current.semantic_kind is not None and not isinstance(current.semantic_kind, SemanticKind):
            raise ContractMappingError("frame semantic_kind must be a known SemanticKind or None")
        if not isinstance(current.roles, tuple) or any(not isinstance(x, str) or not x for x in current.roles):
            raise ContractMappingError("frame roles must be an ordered tuple of non-empty strings")
        fields = (("label", "label"), ("version", "version"),
                  ("roles", "roles"), ("semantic_kind", "semanticKind"))
    elif group == "roles":
        fields = (("label", "label"), ("constraints", "constraints"))
    else:
        fields = (("label", "label"), ("properties", "properties"))

    for attr, field in fields:
        before, after = getattr(snapshot, attr), getattr(current, attr)
        if before != after:
            if field in ("version",) and not _positive_version(after):
                raise ContractMappingError(f"{field} must be a positive integer")
            if field in ("label", "definition", "lifecycleStage") and after is not None and not isinstance(after, str):
                raise ContractMappingError(f"{field} must be a string or None")
            if field == "semanticKind":
                if after is None:
                    record.pop(field, None)
                elif isinstance(after, SemanticKind):
                    record[field] = after.value
                else:
                    raise ContractMappingError("semanticKind must be a known SemanticKind or None")
            elif field == "roles":
                record[field] = list(after)
            elif field in ("constraints", "properties"):
                if after is None:
                    record.pop(field, None)
                elif isinstance(after, Mapping):
                    record[field] = copy.deepcopy(dict(after))
                else:
                    raise ContractMappingError(f"{field} must be a mapping or None")
            elif after is None:
                record.pop(field, None)
            else:
                record[field] = after


def _merge_catalogue_versions(target, snapshot, catalogue):
    for attr, field in (("grammar_version", "grammarVersion"),
                        ("ontology_release", "ontologyRelease")):
        before, after = snapshot.get(field), getattr(catalogue, attr)
        if before != after:
            if after is None:
                target.pop(field, None)
            elif isinstance(after, str):
                target[field] = after
            else:
                raise ContractMappingError(f"{field} must be a string or None")


def document_to_kernel_v14(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV14Document:
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))
    raw = payload.get("definitions")
    if not isinstance(raw, Mapping):
        raise ContractMappingError("definitions must be an object")

    groups = {}
    snapshots = {}
    mapping = {}
    diagnostics = []
    all_unmapped = []
    for group in _GROUPS:
        natives, entries, mapped, unmapped = [], {}, [], []
        for item in raw.get(group, []):
            native, fields, bad = _project_record(group, item)
            if native is None:
                bad = sorted(set(bad + ["required native projection unavailable"]))
                unmapped.append(item["id"])
                entries[item["id"]] = {
                    "status": "UNMAPPED", "mappedFields": fields, "unmappedFields": bad,
                    "notes": ["Complete definition remains canonical-only; no required field was guessed or coerced."],
                }
                diagnostics.append(f"{group} {item['id']} remains canonical-only: " + ", ".join(bad))
                continue
            natives.append(native)
            snapshots[f"{group}:{item['id']}"] = copy.deepcopy(native)
            bad = sorted(set(bad))
            status = "PARTIAL" if bad else "LOSSLESS"
            (unmapped if bad else mapped).append(item["id"])
            if bad:
                diagnostics.append(f"{group} {item['id']} has canonical-only fields: " + ", ".join(bad))
            entries[item["id"]] = {
                "status": status, "mappedFields": fields, "unmappedFields": bad,
                "notes": ["Unknown properties remain canonical-only."] if bad else [],
            }
        groups[group] = tuple(natives)
        mapping[group] = {
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "mapped": sorted(mapped), "unmappedRefs": sorted(unmapped), "records": entries,
        }
        all_unmapped.extend(unmapped)

    catalogue = DefinitionsCatalogueV14(
        concepts=groups["concepts"], frames=groups["frames"],
        roles=groups["roles"], relations=groups["relations"],
        grammar_version=raw.get("grammarVersion"),
        ontology_release=raw.get("ontologyRelease"),
    )
    canonical = []
    for collection in _COLLECTIONS:
        refs = sorted(_ids(payload, collection))
        canonical.extend(refs)
        mapping[collection] = {
            "status": "UNMAPPED" if refs else "LOSSLESS", "mapped": [],
            "unmappedRefs": refs,
            "notes": ["Preserved in canonical envelope; not projected by this adapter."] if refs else [],
        }
    for key in ("validation", "mapping", "extensions"):
        mapping[key] = {
            "status": "PRESERVED", "mapped": [], "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted to native kernel authority."],
        }

    all_unmapped = sorted(set(canonical + all_unmapped))
    report = {
        "sourceProfile": "USG-SEM/1.0", "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel", "targetVersion": MODEL_VERSION,
        "status": "PARTIAL" if all_unmapped else "LOSSLESS",
        "unmappedRefs": all_unmapped, "recordMapping": copy.deepcopy(mapping),
        "notes": [
            "Complete canonical document remains authoritative.",
            "Only supported Concepts, Frames, Roles, and Relations project into native v1.4.0.",
            "Unknown definition properties remain canonical-only.",
            "No ontology equivalence, frame inheritance, or relation reasoning is inferred.",
        ],
    }
    return KernelV14Document(
        payload, _digest(payload), catalogue, snapshots, mapping, report, diagnostics)


def kernel_v14_document_to_contract(imported: KernelV14Document, *, validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV14Document):
        raise TypeError("imported must be KernelV14Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
