"""Loss-aware Python kernel 0.4.0 -> USG-SEM/1.0 reverse serializer.

This serializes the *current native projections* in an ImportedDocument. The
canonical snapshot supplies document-local identity and carries record classes
that kernel 0.4.0 cannot represent; it is never substituted for changed
Source/Node/Assertion projections. The serializer refuses a modified snapshot.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping

from .usg_sem_1 import ContractMappingError


def _json_value(value: Any) -> Any:
    """Convert kernel tuples/Enums/Refs into JSON-compatible values without loss."""
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if hasattr(value, "value") and isinstance(value.value, (str, int, bool)):
        return value.value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise ContractMappingError(f"Unsupported Python semantic parameter value: {type(value).__name__}")


def _ref_index(id_map: Mapping[str, Mapping[str, Any]]) -> dict[Any, str]:
    return {native_ref: opaque_id for collection in id_map.values()
            for opaque_id, native_ref in collection.items()}


def _source_to_contract(source: Any, opaque_id: str, expected_ref: Any) -> tuple[dict[str, Any], dict[str, Any] | None]:
    from usg.core.records import Source

    if not isinstance(source, Source):
        raise ContractMappingError(f"Source projection {opaque_id} is not a kernel Source")
    if source.ref != expected_ref:
        raise ContractMappingError(f"Source projection {opaque_id} changed its typed identity reference")
    result = {
        "id": opaque_id,
        "text": source.text,
        "language": source.language,
        "sourceType": source.type.value,
        "trustTier": source.trust_tier.value,
        "sensitivity": source.sensitivity.value,
        "uri": source.uri,
        "textHash": source.text_hash,
        "hashAlgorithm": "SHA-256",
        "encoding": "UTF-8",
        "offsetUnit": "unicode_code_point",
    }
    if source.anchor is not None:
        result["anchor"] = {
            "documentDate": source.anchor.document_date,
            "timeZone": source.anchor.time_zone,
            "calendar": source.anchor.calendar,
            "speechTime": source.anchor.speech_time,
        }
    result = {key: value for key, value in result.items() if value is not None}
    archival = None
    if source.genre is not None:
        archival = {"genre": source.genre}
    return result, archival


def _pair_original_nodes(imported: Any) -> tuple[dict[int, str], dict[str, dict[str, Any]]]:
    """Use the identity map captured during import, never infer IDs by similarity."""
    records = {item["id"]: item for item in imported.document.get("expressions", [])}
    identity_refs = dict(imported.node_identity_refs)
    by_contract_id = {
        contract_id: records[contract_id]
        for contract_id in identity_refs.values()
        if contract_id in records
    }
    return identity_refs, by_contract_id

def _annotation_to_contract(node: Any, original: Mapping[str, Any] | None,
                            node_id: str, archival: dict[str, Any], unmapped: list[str]) -> dict[str, Any] | None:
    ann = node.ann
    if ann is None:
        return None
    result: dict[str, Any] = {
        "ruleIds": list(ann.rules),
        "basis": ann.basis,
        "languageFeatures": dict(ann.features),
    }
    original_spans = ((original or {}).get("annotations") or {}).get("spans", [])
    original_pairs = [(span.get("start"), span.get("end")) for span in original_spans]
    current_pairs = list(ann.spans)
    if not current_pairs:
        result["spans"] = []
    elif len(original_pairs) == len(current_pairs) and original_pairs == current_pairs:
        result["spans"] = copy.deepcopy(original_spans)
    else:
        # Ann has no sourceRef. Never guess that a changed span belongs to the
        # document's primary source. Keep the native annotation in an extension.
        unmapped.append(node_id)
        archival[node_id] = {
            "nativeAnnotation": {
                "spans": [list(span) for span in ann.spans],
                "rules": list(ann.rules),
                "basis": ann.basis,
                "features": [list(feature) for feature in ann.features],
            },
            "reason": "Python Ann does not retain sourceRef; changed span/source association cannot be proven",
        }
        result["spans"] = []
    return result


def _serialize_graph(imported: Any, used_ids: set[str], archival: dict[str, Any],
                     unmapped: list[str]) -> tuple[list[dict[str, Any]], list[str], dict[str, str]]:
    from usg.grammar.node import Node

    original_by_object, original_records = _pair_original_nodes(imported)
    object_to_id: dict[int, str] = {}
    node_records: list[dict[str, Any]] = []
    ordered_roots: list[str] = []
    root_id_map: dict[str, str] = {}
    pending: list[Any] = []
    for old_root_id, root in imported.expression_roots.items():
        pending.append(root)
        if old_root_id not in root_id_map:
            root_id_map[old_root_id] = original_by_object.get(id(root), old_root_id)

    # Iterative postorder traversal assigns IDs before writing operands while
    # preserving shared object identity and avoiding Python recursion limits.
    states: dict[int, int] = {}
    stack: list[tuple[Any, bool]] = [(root, False) for root in reversed(pending)]
    while stack:
        node, exiting = stack.pop()
        if not isinstance(node, Node):
            raise ContractMappingError(f"Expression projection contains non-Node value {type(node).__name__}")
        identity = id(node)
        if identity in object_to_id:
            continue
        if not exiting:
            if states.get(identity) == 1:
                raise ContractMappingError("Python expression graph contains a cycle")
            if states.get(identity) == 2:
                continue
            states[identity] = 1
            stack.append((node, True))
            for child in reversed(node.args):
                if id(child) not in object_to_id:
                    stack.append((child, False))
            continue

        old_id = original_by_object.get(identity)
        if old_id is not None:
            node_id = old_id
        else:
            counter = len(object_to_id) + 1
            node_id = f"py:node:{counter}"
            while node_id in used_ids:
                counter += 1
                node_id = f"py:node:{counter}"
            used_ids.add(node_id)
        object_to_id[identity] = node_id
        original = original_records.get(old_id) if old_id else None
        params = _json_value(node.params_dict())
        annotation = _annotation_to_contract(node, original, node_id, archival, unmapped)
        record = {
            "id": node_id,
            "op": node.op,
            "sort": getattr(node.sort, "value", str(node.sort)),
            "operandRefs": [object_to_id[id(child)] for child in node.args],
            "params": params,
        }
        if annotation is not None:
            record["annotations"] = annotation
        node_records.append(record)
        states[identity] = 2

    # Stable output order: retain original expression ordering, then append new
    # nodes in deterministic traversal order. IDs and operand order are semantic.
    by_id = {record["id"]: record for record in node_records}
    original_order = [item["id"] for item in imported.document.get("expressions", []) if item["id"] in by_id]
    order = original_order + [record["id"] for record in node_records if record["id"] not in set(original_order)]
    node_records = [by_id[node_id] for node_id in order]
    for old_root_id, root in imported.expression_roots.items():
        new_id = object_to_id[id(root)]
        ordered_roots.append(new_id)
        root_id_map[old_root_id] = new_id
    return node_records, ordered_roots, root_id_map


def _assertion_to_contract(assertion: Any, opaque_id: str, refs: Mapping[Any, str],
                           expected_ref: Any, root_id_map: Mapping[str, str],
                           archival: dict[str, Any]) -> dict[str, Any]:
    from usg.core.records import Assertion, ContentType

    if not isinstance(assertion, Assertion):
        raise ContractMappingError(f"Assertion projection {opaque_id} is not a kernel Assertion")
    if assertion.ref != expected_ref:
        raise ContractMappingError(f"Assertion projection {opaque_id} changed its typed identity reference")
    if assertion.content_type is not ContentType.NODE:
        raise ContractMappingError("Only NODE content assertions have an exact USG-SEM/1.0 projection")
    expression_id = refs.get(assertion.content)
    if expression_id is None:
        raise ContractMappingError("Assertion content Ref has no canonical expression identity")
    expression_id = root_id_map.get(expression_id, expression_id)
    lifecycle_map = {"VALIDATED_FORMALLY": "FORMALLY_VALIDATED"}
    lifecycle_stage = lifecycle_map.get(assertion.lifecycle.value, assertion.lifecycle.value)
    contract_lifecycle = {
        "DISCOVERED", "STRUCTURED", "FORMALLY_VALIDATED", "AUTOMATICALLY_EVALUATED",
        "CORROBORATED", "PROMOTED", "REJECTED", "DEFERRED", "DEPRECATED",
    }
    if lifecycle_stage not in contract_lifecycle:
        archival.setdefault(opaque_id, {})["unsupportedLifecycle"] = assertion.lifecycle.value
        raise ContractMappingError(
            f"Python lifecycle {assertion.lifecycle.value!r} has no USG-SEM/1.0 equivalent"
        )
    result = {
        "id": opaque_id,
        "expressionRef": expression_id,
        "origin": assertion.origin.value,
        "epistemicStatus": assertion.epistemic_status.value,
        "commitment": assertion.commitment.value,
        "evaluationContext": {
            "kind": assertion.eval_context.value,
            **({"name": assertion.eval_context_name} if assertion.eval_context_name is not None else {}),
        },
        "lifecycleStage": lifecycle_stage,
    }
    if assertion.source is not None:
        source_id = refs.get(assertion.source)
        if source_id is None:
            raise ContractMappingError("Assertion source Ref has no canonical source identity")
        result["sourceRef"] = source_id
    archival.setdefault(opaque_id, {})["pythonVersionMetadata"] = {
        "grammarVersion": assertion.grammar_version,
        "ontologyRelease": assertion.ontology_release,
    }
    unsupported = {}
    if assertion.attributed_to is not None:
        unsupported["attributedTo"] = str(assertion.attributed_to)
    if assertion.evidence is not None:
        unsupported["evidence"] = str(assertion.evidence)
    if assertion.definition_ref is not None:
        unsupported["definitionRef"] = str(assertion.definition_ref)
    if assertion.alt_group is not None:
        unsupported["altGroup"] = assertion.alt_group
    if unsupported:
        archival.setdefault(opaque_id, {}).update({
            "nativeAssertionMetadata": unsupported,
            "reason": "The current ImportedDocument has no proven canonical identity mapping for these native references",
        })
        raise ContractMappingError("Assertion has native metadata without an exact canonical ID mapping")
    return result


def python_to_contract_document(imported: Any, *, validate: bool = True,
                                schema_path: str | None = None) -> dict[str, Any]:
    """Serialize current Python projections into a new USG-SEM document.

    The imported canonical snapshot is used only as a document envelope and as
    the source of records for which kernel 0.4.0 has no native equivalent.
    Current Source, Node and Assertion projections are serialized afresh.
    """
    from .document import _digest, validate_contract_document

    if _digest(imported.document) != imported.original_digest:
        raise ContractMappingError(
            "Canonical snapshot changed after import; reverse serialization refuses stale canonical-only records"
        )
    document = copy.deepcopy(imported.document)
    archival: dict[str, Any] = {}
    unmapped: list[str] = []

    source_records = []
    for opaque_id, source in imported.sources.items():
        try:
            record, extra = _source_to_contract(source, opaque_id, imported.id_map["sources"][opaque_id])
            source_records.append(record)
            if extra:
                archival[opaque_id] = extra
        except Exception as exc:
            unmapped.append(opaque_id)
            archival[opaque_id] = {"reason": str(exc)}

    graph_records, roots, root_id_map = _serialize_graph(imported, {
        item["id"] for collection in document.values() if isinstance(collection, list)
        for item in collection if isinstance(item, dict) and isinstance(item.get("id"), str)
    } | {document["documentId"]}, archival, unmapped)

    ref_ids = _ref_index(imported.id_map)
    assertion_records = []
    for opaque_id, assertion in imported.assertions.items():
        try:
            assertion_records.append(_assertion_to_contract(
                assertion, opaque_id, ref_ids, imported.id_map["assertions"][opaque_id],
                root_id_map, archival
            ))
        except Exception as exc:
            unmapped.append(opaque_id)
            archival.setdefault(opaque_id, {})["reason"] = str(exc)

    # Keep canonical records that did not receive a native projection. A
    # failed/unsupported root must remain present and reachable as a root.
    def merge_by_id(original_records: list[dict[str, Any]], current_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        current_by_id = {item["id"]: item for item in current_records}
        merged = [current_by_id.pop(item["id"], item) for item in original_records]
        merged.extend(current_by_id.values())
        return merged

    original_sources = copy.deepcopy(document.get("sources", []))
    original_expressions = copy.deepcopy(document.get("expressions", []))
    original_assertions = copy.deepcopy(document.get("assertions", []))
    document["sources"] = merge_by_id(original_sources, source_records)
    document["expressions"] = merge_by_id(original_expressions, graph_records)
    document["assertions"] = merge_by_id(original_assertions, assertion_records)
    mapped_root_ids = set(imported.expression_roots)
    preserved_roots = [root for root in document.get("rootExpressionRefs", []) if root not in mapped_root_ids]
    document["rootExpressionRefs"] = roots + preserved_roots
    unmapped.extend(item["id"] for item in original_sources if item["id"] not in {x["id"] for x in source_records})
    unmapped.extend(item["id"] for item in original_expressions if item["id"] not in {x["id"] for x in graph_records})
    unmapped.extend(item["id"] for item in original_assertions if item["id"] not in {x["id"] for x in assertion_records})
    if source_records:
        original_primary = document.get("primarySourceRef")
        if original_primary not in {item["id"] for item in document["sources"]}:
            document["primarySourceRef"] = source_records[0]["id"]
    else:
        unmapped.append(document.get("primarySourceRef", "primarySourceRef"))

    namespace = "org.usg.python-kernel.v0.4.0"
    extensions = document.setdefault("extensions", {})
    prior = extensions.get(namespace, {})
    if not isinstance(prior, dict):
        prior = {"previousValue": prior}
    prior = copy.deepcopy(prior)
    if archival:
        prior["reverseSerializerPreservation"] = archival
    extensions[namespace] = prior

    # Canonical-only record classes remain in the document, and are reported as
    # unmapped to the native kernel rather than being deleted or fabricated.
    for collection in ("referents", "mentions", "evidence", "contexts",
                      "expressionRelations", "unresolvedItems", "derivations"):
        unmapped.extend(item["id"] for item in document.get(collection, []))
    for collection in ("sources", "expressions", "assertions"):
        unmapped.extend(imported.record_mapping.get(collection, {}).get("unmappedRefs", []))
    for collection in ("concepts", "frames", "roles", "relations"):
        unmapped.extend(item["id"] for item in document["definitions"].get(collection, []))

    unmapped = sorted(set(unmapped))
    status = "LOSSLESS" if not unmapped else "PARTIAL"
    document["mapping"] = {
        "sourceProfile": "usg-python-kernel",
        "sourceVersion": "0.4.0",
        "status": status,
        "unmappedRefs": unmapped,
        "notes": [
            "Source, expression and assertion projections were serialized from current Python objects.",
            "Canonical-only record classes were carried forward unchanged and remain explicitly unmapped to Python kernel 0.4.0.",
            "Python Ann does not contain sourceRef; span associations are restored only when they exactly match the imported canonical annotation.",
        ],
        "targetMappings": [{
            "targetProfile": "usg-python-kernel",
            "targetVersion": "0.4.0",
            "status": status,
            "unmappedRefs": unmapped,
            "notes": ["No unsupported constructor or record was coerced or silently removed."],
        }],
    }
    if validate:
        errors = validate_contract_document(document, schema_path) if schema_path else validate_contract_document(document)
        if errors:
            raise ContractMappingError("Reverse serializer produced an invalid USG-SEM document: " + "; ".join(errors[:20]))
    return document
