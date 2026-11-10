"""Composed USG-SEM/1.0 document adapter across Python kernel generations v0.5–v1.4."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .document import _digest, validate_contract_document
from .usg_sem_1 import ContractMappingError

MODEL_VERSION = "1.5.1"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"

_ADAPTERS = {
    "sources_expressions": {
        "module": ".document_v05",
        "import_name": "document_to_kernel_v05",
        "collections": ("sources", "expressions", "rootExpressionRefs"),
        "groups": ("sources", "expressions"),
    },
    "referents": {
        "module": ".document_v06", "import_name": "document_to_kernel_v06",
        "collections": ("referents",), "groups": ("referents",),
    },
    "mentions": {
        "module": ".document_v07", "import_name": "document_to_kernel_v07",
        "collections": ("mentions",), "groups": ("mentions",),
    },
    "assertions": {
        "module": ".document_v08", "import_name": "document_to_kernel_v08",
        "collections": ("assertions",), "groups": ("assertions",),
    },
    "evidence": {
        "module": ".document_v09", "import_name": "document_to_kernel_v09",
        "collections": ("evidence",), "groups": ("evidence",),
    },
    "contexts": {
        "module": ".document_v10", "import_name": "document_to_kernel_v10",
        "collections": ("contexts",), "groups": ("contexts",),
    },
    "expressionRelations": {
        "module": ".document_v11", "import_name": "document_to_kernel_v11",
        "collections": ("expressionRelations",), "groups": ("expressionRelations",),
    },
    "unresolvedItems": {
        "module": ".document_v121", "import_name": "document_to_kernel_v121",
        "collections": ("unresolvedItems",), "groups": ("unresolvedItems",),
    },
    "derivations": {
        "module": ".document_v13", "import_name": "document_to_kernel_v13",
        "collections": ("derivations",), "groups": ("derivations",),
    },
    "definitions": {
        "module": ".document_v14", "import_name": "document_to_kernel_v14",
        "collections": ("definitions",),
        "groups": ("concepts", "frames", "roles", "relations"),
    },
}


@dataclass
class KernelV15Document:
    """One canonical snapshot composed with all family-specific native adapters."""
    document: dict[str, Any]
    original_digest: str
    adapters: dict[str, Any]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: list[str]

    def export_contract_document(self, *, validate: bool = True,
                                 schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Canonical document snapshot was modified; refusing composed native merge.")

        result = copy.deepcopy(self.document)
        for key, spec in _ADAPTERS.items():
            subdocument = self.adapters[key]
            projected = subdocument.export_contract_document(validate=False)
            for collection in spec["collections"]:
                if collection not in projected:
                    raise ContractMappingError(
                        f"Adapter {key} did not return required collection {collection}")
                result[collection] = copy.deepcopy(projected[collection])

        if validate:
            problems = validate_contract_document(result, schema_path)
            problems.extend(_validate_cross_family_spans(result))
            if problems:
                raise ContractMappingError(
                    "Composed USG-SEM/1.0 document is invalid: " + "; ".join(problems[:30]))
        return result


def _validate_cross_family_spans(document: Mapping[str, Any]) -> list[str]:
    """Check source-linked spans after every family has been composed."""
    sources = {
        item["id"]: item for item in document.get("sources", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    errors: list[str] = []

    def check_span(owner: Mapping[str, Any], span: Any, field: str,
                   expected_text: str | None = None) -> None:
        if span is None:
            return
        if not isinstance(span, Mapping):
            errors.append(f"{field} is not an object")
            return
        source_ref = span.get("sourceRef")
        source = sources.get(source_ref)
        if source is None:
            errors.append(f"{field} has dangling sourceRef {source_ref!r}")
            return
        source_text = source.get("text")
        start, end = span.get("start"), span.get("end")
        if not isinstance(source_text, str):
            errors.append(f"{field} source has no text")
            return
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or start < 0 or end < start or end > len(source_text)):
            errors.append(f"{field} is outside Unicode code-point source bounds")
            return
        if span.get("offsetUnit") != "unicode_code_point":
            errors.append(f"{field} does not use Unicode code-point offsets")
            return
        if expected_text is not None and source_text[start:end] != expected_text:
            errors.append(f"{field} does not align with its exact source text")

    for referent in document.get("referents", []):
        check_span(referent, referent.get("sourceSpan"), f"referent {referent.get('id')} sourceSpan")
    for mention in document.get("mentions", []):
        check_span(mention, mention.get("sourceSpan"),
                   f"mention {mention.get('id')} sourceSpan", mention.get("surfaceText"))
    for evidence in document.get("evidence", []):
        span = evidence.get("span")
        if isinstance(span, Mapping) and span.get("sourceRef") != evidence.get("sourceRef"):
            errors.append(f"evidence {evidence.get('id')} span/sourceRef mismatch")
        expected = evidence.get("quote") if evidence.get("alignmentStatus") == "EXACT" else None
        check_span(evidence, span, f"evidence {evidence.get('id')} span", expected)
    return errors


def document_to_kernel_v15(document: Mapping[str, Any], *, validate: bool = True,
                           schema_path: str | Path = SCHEMA_PATH) -> KernelV15Document:
    """Project every supported USG-SEM/1.0 record family through its exact adapter."""
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    from importlib import import_module
    adapters: dict[str, Any] = {}
    for key, spec in _ADAPTERS.items():
        module = import_module(spec["module"], __package__)
        importer = getattr(module, spec["import_name"])
        adapters[key] = importer(payload, validate=False, schema_path=schema_path)

    record_mapping: dict[str, dict[str, Any]] = {}
    diagnostics: list[str] = []
    unmapped: set[str] = set()
    partial = False
    for key, spec in _ADAPTERS.items():
        subdocument = adapters[key]
        diagnostics.extend(subdocument.diagnostics)
        for group in spec["groups"]:
            item = copy.deepcopy(subdocument.record_mapping.get(group, {
                "status": "UNMAPPED", "mapped": [], "unmappedRefs": [],
                "notes": ["No family-specific mapping report was produced."],
            }))
            record_mapping[group] = item
            if item.get("status") not in ("LOSSLESS", "PRESERVED"):
                partial = True
            unmapped.update(item.get("unmappedRefs", []))
            unmapped.update(item.get("partialRefs", []))

    status = "PARTIAL" if partial else "LOSSLESS"
    family_reports = {
        key: copy.deepcopy(adapters[key].mapping_report)
        for key in _ADAPTERS
    }
    report = {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel-composed",
        "targetVersion": MODEL_VERSION,
        "status": status,
        "unmappedRefs": sorted(unmapped),
        "recordMapping": copy.deepcopy(record_mapping),
        "familyReports": family_reports,
        "notes": [
            "Each canonical record family is projected by its independently versioned exact adapter.",
            "Sources and expression graphs use the v0.5.0 adapter; later record families use their own versioned adapters, including typed UnresolvedItem v1.2.1.",
            "Every sub-adapter shares the same immutable canonical snapshot.",
            "Export merges only the record collections owned by each sub-adapter.",
            "Unknown, unsupported, and dangling fields remain in the canonical envelope.",
            "Validation, mapping metadata, and extensions remain canonical and are not promoted to semantic authority.",
            "A PARTIAL report means one or more native projections are incomplete; it does not mean the canonical envelope was lost.",
        ],
    }
    return KernelV15Document(
        document=payload,
        original_digest=_digest(payload),
        adapters=adapters,
        record_mapping=record_mapping,
        mapping_report=report,
        diagnostics=diagnostics,
    )


def kernel_v15_document_to_contract(imported: KernelV15Document, *,
                                    validate: bool = True,
                                    schema_path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    if not isinstance(imported, KernelV15Document):
        raise TypeError("imported must be KernelV15Document")
    return imported.export_contract_document(validate=validate, schema_path=schema_path)
