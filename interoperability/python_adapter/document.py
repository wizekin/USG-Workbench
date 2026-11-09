"""Document-level USG-SEM/1.0 import boundary for Python kernel 0.4.0.

The complete canonical document is retained as the authoritative interchange
payload. Exact Python projections are created only where kernel 0.4.0 has a
faithful native record/constructor. Other document collections remain intact
and are enumerated in the target mapping report; they are never dropped.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .usg_sem_1 import ContractMappingError, contract_graph_roots_to_semir, mapping_report_for_python


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specifications" / "usg-sem-1.0.schema.json"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class ImportedDocument:
    """Loss-preserving document snapshot plus exact native Python projections."""

    document: dict[str, Any]
    original_digest: str
    id_map: dict[str, dict[str, Any]]
    sources: dict[str, Any]
    expression_roots: dict[str, Any]
    assertions: dict[str, Any]
    record_mapping: dict[str, dict[str, Any]]
    mapping_report: dict[str, Any]
    diagnostics: tuple[str, ...]

    def export_contract_document(self) -> dict[str, Any]:
        """Return the exact original contract document, refusing stale snapshots."""
        if _digest(self.document) != self.original_digest:
            raise ContractMappingError(
                "Imported canonical document was modified; refusing to export a stale snapshot. "
                "Use a versioned document-edit operation rather than silently merging projections."
            )
        return copy.deepcopy(self.document)


_ID_SPACES = {
    "sources": "SOURCE",
    "referents": "REFERENT",
    "expressions": "NODE",
    "assertions": "ASSERTION",
    "evidence": "EVIDENCE",
    "definitions.concepts": "CONCEPT",
    "definitions.frames": "FRAME",
    "definitions.roles": "ROLE",
    "definitions.relations": "RELATION",
    "derivations": "CERTIFICATE",
}


def _make_id_map(document: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    from usg.core.ids import IdSpace, Ref

    result: dict[str, dict[str, Any]] = {}
    for collection, space_name in _ID_SPACES.items():
        if collection.startswith("definitions."):
            _, key = collection.split(".", 1)
            records = (document.get("definitions") or {}).get(key, [])
        else:
            records = document.get(collection, [])
        ids = sorted({item["id"] for item in records if isinstance(item, dict) and isinstance(item.get("id"), str)})
        space = IdSpace(space_name)
        result[collection] = {opaque_id: Ref(space, index) for index, opaque_id in enumerate(ids, 1)}
    return result


def _source_projection(record: Mapping[str, Any], ref: Any):
    from usg.core.records import Anchor, Source
    from usg.core.values import Sensitivity, SourceType, TrustTier

    # UNKNOWN is meaningful in USG-SEM but has no exact enum equivalent in kernel 0.4.0.
    required = ("sourceType", "trustTier", "sensitivity")
    if any(record.get(key) not in (set(SourceType.__members__) if key == "sourceType" else
                                   set(TrustTier.__members__) if key == "trustTier" else
                                   set(Sensitivity.__members__)) for key in required):
        raise ContractMappingError(f"Source {record.get('id')} has an enum not represented by Python 0.4.0")
    if record.get("offsetUnit") != "unicode_code_point":
        raise ContractMappingError(f"Source {record.get('id')} does not use Unicode code-point offsets")
    if record.get("encoding") not in (None, "UTF-8"):
        raise ContractMappingError(f"Source {record.get('id')} uses unsupported encoding {record.get('encoding')!r}")
    if record.get("hashAlgorithm") not in (None, "SHA-256"):
        raise ContractMappingError(f"Source {record.get('id')} uses unsupported hash algorithm")
    anchor_data = record.get("anchor")
    anchor = None
    if anchor_data is not None:
        allowed = {"documentDate", "timeZone", "calendar", "speechTime"}
        if set(anchor_data) - allowed:
            raise ContractMappingError(f"Source {record.get('id')} anchor has unsupported fields")
        anchor = Anchor(
            document_date=anchor_data.get("documentDate"),
            time_zone=anchor_data.get("timeZone"),
            calendar=anchor_data.get("calendar", "gregorian"),
            speech_time=anchor_data.get("speechTime"),
        )
    return Source(
        text=record["text"],
        language=record["language"],
        type=SourceType(record["sourceType"]),
        trust_tier=TrustTier(record["trustTier"]),
        sensitivity=Sensitivity(record["sensitivity"]),
        uri=record.get("uri"),
        anchor=anchor,
        ref=ref,
        text_hash=record.get("textHash", ""),
    )


def _assertion_projection(record: Mapping[str, Any], id_map: Mapping[str, Mapping[str, Any]]):
    if record.get("attributedToRef") is not None:
        raise ContractMappingError("Attributed referents are not yet native document records in kernel 0.4.0")
    if record.get("evidenceRefs"):
        raise ContractMappingError("Evidence records are preserved canonically; no exact Evidence record adapter exists yet")
    if record.get("definitionRef") is not None or record.get("alternativeGroupRef") is not None:
        raise ContractMappingError("Definition/alternative-group references have no exact Assertion field mapping")
    from usg.core.records import Assertion, ContentType
    from usg.core.values import CommitmentKind, EpistemicStatus, EvalContextKind, Lifecycle, Origin

    origin = record["origin"]
    if origin not in Origin.__members__:
        raise ContractMappingError(f"Assertion {record['id']} origin {origin!r} has no kernel equivalent")
    status = record["epistemicStatus"]
    if status not in EpistemicStatus.__members__:
        raise ContractMappingError(f"Assertion {record['id']} epistemic status has no kernel equivalent")
    commitment = record["commitment"]
    if commitment not in CommitmentKind.__members__:
        raise ContractMappingError(f"Assertion {record['id']} commitment has no kernel equivalent")
    context = record.get("evaluationContext") or {}
    if context.get("contextRef") is not None:
        raise ContractMappingError(f"Assertion {record['id']} contextRef is not representable in kernel 0.4.0")
    context_kind = context.get("kind")
    if context_kind not in EvalContextKind.__members__:
        raise ContractMappingError(f"Assertion {record['id']} evaluation context has no kernel equivalent")
    if record.get("alternativeGroupRef") is not None:
        raise ContractMappingError(f"Assertion {record['id']} alternativeGroupRef is opaque, not an integer group")
    evidence_refs = record.get("evidenceRefs", [])
    if len(evidence_refs) > 1:
        raise ContractMappingError(f"Assertion {record['id']} has multiple evidenceRefs; kernel 0.4.0 stores one")
    stage = record["lifecycleStage"]
    stage_map = {"FORMALLY_VALIDATED": "VALIDATED_FORMALLY"}
    if stage == "AUTOMATICALLY_EVALUATED":
        raise ContractMappingError(
            f"Assertion {record['id']} AUTOMATICALLY_EVALUATED has no exact kernel lifecycle equivalent"
        )
    stage = stage_map.get(stage, stage)
    if stage not in Lifecycle.__members__:
        raise ContractMappingError(f"Assertion {record['id']} lifecycle stage has no kernel equivalent")

    def ref_for(collection: str, value: str | None, *, required: bool = False):
        if value is None:
            if required:
                raise ContractMappingError(f"Assertion {record['id']} is missing {collection} reference")
            return None
        mapped = id_map.get(collection, {}).get(value)
        if mapped is None:
            raise ContractMappingError(f"Assertion {record['id']} has unmapped {collection} reference {value}")
        return mapped

    expression_ref = ref_for("expressions", record.get("expressionRef"), required=True)
    source_ref = ref_for("sources", record.get("sourceRef"))
    attributed_ref = ref_for("referents", record.get("attributedToRef"))
    if commitment == "ATTRIBUTED" and attributed_ref is None:
        raise ContractMappingError(f"Assertion {record['id']} has no mapped attributed referent")
    evidence_ref = ref_for("evidence", evidence_refs[0]) if evidence_refs else None
    definition_ref = None
    if record.get("definitionRef") is not None:
        definition_ref = next(
            (group[record["definitionRef"]] for group in id_map.values() if record["definitionRef"] in group),
            None,
        )
        if definition_ref is None:
            raise ContractMappingError(f"Assertion {record['id']} has unmapped definitionRef")
    return Assertion(
        content_type=ContentType.NODE,
        content=expression_ref,
        origin=Origin(origin),
        epistemic_status=EpistemicStatus(status),
        commitment=CommitmentKind(commitment),
        attributed_to=attributed_ref,
        eval_context=EvalContextKind(context_kind),
        eval_context_name=context.get("name"),
        definition_ref=definition_ref,
        source=source_ref,
        evidence=evidence_ref,
        lifecycle=Lifecycle(stage),
        ref=id_map["assertions"][record["id"]],
    )


def validate_contract_document(document: Mapping[str, Any], schema_path: str | Path = SCHEMA_PATH) -> list[str]:
    """Validate JSON Schema plus cross-record references and expression graph integrity."""
    errors: list[str] = []
    try:
        import jsonschema
    except ImportError as exc:
        raise ContractMappingError("Install jsonschema>=4.18,<5 to validate USG-SEM documents") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors.extend(f"schema:{e.json_path}: {e.message}" for e in validator.iter_errors(document))
    if errors:
        return errors

    collections = (
        "sources", "referents", "mentions", "expressions", "assertions", "evidence",
        "contexts", "expressionRelations", "unresolvedItems", "derivations",
    )
    all_ids = [document["documentId"]]
    for collection in collections:
        all_ids.extend(item["id"] for item in document.get(collection, []))
    for collection in ("concepts", "frames", "roles", "relations"):
        all_ids.extend(item["id"] for item in document["definitions"].get(collection, []))
    if len(all_ids) != len(set(all_ids)):
        errors.append("duplicate ID across document record collections")

    sources = {x["id"]: x for x in document["sources"]}
    expressions = {x["id"]: x for x in document["expressions"]}
    referents = {x["id"]: x for x in document["referents"]}
    mentions = {x["id"]: x for x in document["mentions"]}
    evidence = {x["id"]: x for x in document["evidence"]}
    if document["primarySourceRef"] not in sources:
        errors.append("primarySourceRef does not resolve")

    for item in expressions.values():
        for child in item.get("operandRefs", []):
            if child not in expressions:
                errors.append(f"expression {item['id']} has dangling operandRef {child}")
        for span in (item.get("annotations") or {}).get("spans", []):
            _validate_span(span, sources, errors, f"expression {item['id']}")
    for root in document["rootExpressionRefs"]:
        if root not in expressions:
            errors.append(f"missing root expression {root}")
        elif expressions[root]["sort"] != "PROP":
            errors.append(f"root expression {root} is not PROP-sorted")

    color: dict[str, int] = {}
    for root in expressions:
        if color.get(root) == 2:
            continue
        stack = [(root, False)]
        while stack:
            node_id, exiting = stack.pop()
            if exiting:
                color[node_id] = 2
                continue
            if color.get(node_id) == 1:
                errors.append(f"expression graph cycle at {node_id}")
                continue
            if color.get(node_id) == 2:
                continue
            color[node_id] = 1
            stack.append((node_id, True))
            for child in reversed(expressions[node_id].get("operandRefs", [])):
                if child in expressions:
                    if color.get(child) == 1:
                        errors.append(f"expression graph cycle {node_id}->{child}")
                    elif color.get(child) != 2:
                        stack.append((child, False))

    for item in document["mentions"]:
        if item.get("referentRef") and item["referentRef"] not in referents:
            errors.append(f"mention {item['id']} has dangling referentRef")
        if item.get("antecedentMentionRef") and item["antecedentMentionRef"] not in mentions:
            errors.append(f"mention {item['id']} has dangling antecedentMentionRef")
    for item in document["assertions"]:
        if item["expressionRef"] not in expressions:
            errors.append(f"assertion {item['id']} has dangling expressionRef")
        if item.get("sourceRef") and item["sourceRef"] not in sources:
            errors.append(f"assertion {item['id']} has dangling sourceRef")
    for item in document["evidence"]:
        source = sources.get(item["sourceRef"])
        if source is None:
            errors.append(f"evidence {item['id']} has dangling sourceRef")
        else:
            _validate_span(item["span"], sources, errors, f"evidence {item['id']}")
            span = item["span"]
            if source["text"][span["start"]:span["end"]] != item["quote"]:
                errors.append(f"evidence {item['id']} quote does not match exact source span")
    return errors


def _validate_span(span: Mapping[str, Any], sources: Mapping[str, Any], errors: list[str], where: str) -> None:
    source = sources.get(span.get("sourceRef"))
    if source is None:
        errors.append(f"{where} has dangling sourceRef")
        return
    start, end = span.get("start"), span.get("end")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start or end > len(source["text"]):
        errors.append(f"{where} has out-of-range Unicode code-point span")


def document_to_python(
    document: Mapping[str, Any],
    *,
    validate: bool = True,
    schema_path: str | Path = SCHEMA_PATH,
) -> ImportedDocument:
    """Import a whole USG-SEM document without discarding non-kernel records.

    Sources, supported expression roots and assertions receive native Python
    projections. Mentions, referent identity metadata, evidence assessments,
    contexts, definitions that lack a full FrameDef, relations, unresolved
    items, derivations, validation certificates and extensions remain in the
    exact canonical document and are enumerated as non-native target content.
    """
    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    payload = copy.deepcopy(dict(document))
    if payload.get("profileId") != "USG-SEM/1.0":
        raise ContractMappingError(f"Unsupported contract profile: {payload.get('profileId')!r}")
    if validate:
        problems = validate_contract_document(payload, schema_path)
        if problems:
            raise ContractMappingError("Invalid USG-SEM document: " + "; ".join(problems[:20]))

    from usg.core.ids import IdSpace
    id_map = _make_id_map(payload)
    sources: dict[str, Any] = {}
    assertions: dict[str, Any] = {}
    diagnostics: list[str] = []
    unmapped: list[str] = []
    record_mapping: dict[str, dict[str, Any]] = {}

    for item in payload.get("sources", []):
        try:
            sources[item["id"]] = _source_projection(item, id_map["sources"][item["id"]])
        except Exception as exc:
            unmapped.append(item["id"])
            diagnostics.append(f"source {item['id']}: {exc}")
    record_mapping["sources"] = {
        "status": "LOSSLESS" if len(sources) == len(payload.get("sources", [])) else "PARTIAL",
        "mapped": sorted(sources),
        "unmappedRefs": sorted(set(item["id"] for item in payload.get("sources", [])) - set(sources)),
    }

    expression_items = payload.get("expressions", [])
    expression_report = mapping_report_for_python(expression_items)
    expression_roots: dict[str, Any] = {}
    if expression_items and not expression_report["unmappedRefs"]:
        try:
            expression_roots = contract_graph_roots_to_semir(expression_items, payload.get("rootExpressionRefs", []))
        except Exception as exc:
            diagnostics.append(f"expression graph: {exc}")
    reachable: set[str] = set()
    expr_map = {item["id"]: item for item in expression_items}
    pending = list(payload.get("rootExpressionRefs", []))
    while pending:
        node_id = pending.pop()
        if node_id in reachable or node_id not in expr_map:
            continue
        reachable.add(node_id)
        pending.extend(expr_map[node_id].get("operandRefs", []))
    mapped_expr_ids = reachable if expression_roots else set()
    expression_unmapped = sorted(set(expr_map) - mapped_expr_ids)
    unmapped.extend(expression_unmapped)
    record_mapping["expressions"] = {
        "status": "LOSSLESS" if expression_items and not expression_unmapped else
                  "PARTIAL" if expression_items else "LOSSLESS",
        "mapped": sorted(mapped_expr_ids),
        "unmappedRefs": expression_unmapped,
        "notes": expression_report.get("notes", []),
    }

    for item in payload.get("assertions", []):
        try:
            if item["expressionRef"] not in expression_roots:
                raise ContractMappingError("referenced expression root is not mapped to a native Node")
            if item.get("sourceRef") and item["sourceRef"] not in sources:
                raise ContractMappingError("referenced source is not mapped to a native Source")
            assertions[item["id"]] = _assertion_projection(item, id_map)
        except Exception as exc:
            unmapped.append(item["id"])
            diagnostics.append(f"assertion {item['id']}: {exc}")
    record_mapping["assertions"] = {
        "status": "LOSSLESS" if len(assertions) == len(payload.get("assertions", [])) else "PARTIAL",
        "mapped": sorted(assertions),
        "unmappedRefs": sorted(set(item["id"] for item in payload.get("assertions", [])) - set(assertions)),
    }

    # These records are preserved in the canonical snapshot. Kernel 0.4.0 has
    # no equivalent for their full distinctions or stable document-local IDs.
    native_collections = {"sources", "expressions", "assertions"}
    for collection in (
        "referents", "mentions", "evidence", "contexts", "expressionRelations",
        "unresolvedItems", "derivations",
    ):
        records = payload.get(collection, [])
        ids = sorted(item["id"] for item in records)
        if records:
            unmapped.extend(ids)
        record_mapping[collection] = {
            "status": "UNMAPPED" if records else "LOSSLESS",
            "mapped": [],
            "unmappedRefs": ids,
            "notes": [
                "Retained losslessly in the canonical document; no complete native Python 0.4.0 record equivalent exists."
            ] if records else [],
        }

    definition_ids = []
    for collection in ("concepts", "frames", "roles", "relations"):
        definition_ids.extend(item["id"] for item in payload["definitions"].get(collection, []))
    if definition_ids:
        unmapped.extend(definition_ids)
    record_mapping["definitions"] = {
        "status": "UNMAPPED" if definition_ids else "LOSSLESS",
        "mapped": [],
        "unmappedRefs": sorted(definition_ids),
        "notes": [
            "Definitions remain canonical: the contract frame/concept profile does not always contain every field required by Python FrameDef/Concept."
        ] if definition_ids else [],
    }

    # Validation, mapping, and namespaced extensions are preserved as document
    # metadata; they are not imported as kernel certificates or authority.
    for collection in ("validation", "mapping", "extensions"):
        record_mapping[collection] = {
            "status": "PRESERVED",
            "mapped": [],
            "unmappedRefs": [],
            "notes": ["Preserved verbatim; not promoted into Python kernel authority."],
        }

    unmapped = sorted(set(unmapped))
    status = "LOSSLESS" if not unmapped else "PARTIAL"
    mapping_report = {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel",
        "targetVersion": "0.4.0",
        "status": status,
        "unmappedRefs": unmapped,
        "notes": [
            "The complete USG-SEM document remains available unchanged for export.",
            "Native Python projections are limited to exact supported sources, expression roots and assertions.",
            "Non-native records remain preserved in the canonical snapshot; no semantic content is silently discarded.",
        ],
    }
    return ImportedDocument(
        document=payload,
        original_digest=_digest(payload),
        id_map=id_map,
        sources=sources,
        expression_roots=expression_roots,
        assertions=assertions,
        record_mapping=record_mapping,
        mapping_report=mapping_report,
        diagnostics=tuple(diagnostics),
    )
