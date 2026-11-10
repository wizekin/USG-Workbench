"""USG-SEM/1.0 expression-graph adapter for Python kernel 0.5.0.

This module is deliberately separate from the v0.4.0 document adapter. It
projects expression graphs into the new native constructors while retaining
canonical-only fields and unsupported roots explicitly. It never changes the
canonical interchange document or claims that OPAQUE content is interpretable.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .usg_sem_1 import ContractMappingError


_METADATA_FIELDS = {
    "PREDICATE_APP": ("argumentRequirements", "argumentBindings", "eventFrame", "grammaticalTense",
                      "aspect", "temporalFrame", "attribution", "provenance", "completeness",
                      "evidenceRefs", "nativeSourceClaimId"),
    "CONNECTIVE": ("marker", "logicalStatus", "antecedentInterpretation",
                   "conditionMetadata", "disjunctionSemantics", "attribution", "evidenceRefs"),
    "QUANTIFIER": ("restrictor", "variableBinding", "surfaceText", "evidenceRefs", "attribution"),
    "OPAQUE": ("payload", "evidenceRefs"),
    "UNRESOLVED_REF": ("evidenceRefs",),
}


@dataclass
class KernelV05Graph:
    """Native v0.5.0 projections plus an immutable-by-digest canonical graph snapshot."""
    expressions: dict[str, dict[str, Any]]
    root_refs: list[str]
    roots: dict[str, Any]
    node_identity_refs: dict[int, str]
    original_node_metadata: dict[str, dict[str, Any]]
    failed_roots: dict[str, str]
    partial_refs: set[str]
    diagnostics: list[str]
    preservation: dict[str, Any]

    @property
    def mapping_report(self) -> dict[str, Any]:
        unmapped = sorted(set(self.failed_roots) | self.partial_refs)
        return {
            "sourceProfile": "USG-SEM/1.0",
            "targetProfile": "usg-python-kernel",
            "targetVersion": "0.5.0",
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "unmappedRefs": unmapped,
            "notes": list(self.diagnostics),
        }


def _tuple_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_tuple_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuple_value(item) for key, item in value.items()}
    return value


def _annotation(data: Mapping[str, Any] | None, node_id: str):
    if not data:
        return None
    from usg.grammar.node import Ann
    allowed = {"spans", "ruleIds", "basis", "languageFeatures"}
    extra = set(data) - allowed
    if extra:
        raise ContractMappingError(f"Unsupported annotation fields on {node_id}: {sorted(extra)}", node_refs=[node_id])
    spans = data.get("spans", [])
    source_refs = {span.get("sourceRef") for span in spans}
    if len(source_refs) > 1:
        raise ContractMappingError(f"Kernel 0.5.0 Ann cannot retain multiple source IDs on {node_id}", node_refs=[node_id])
    pairs = []
    for span in spans:
        if span.get("offsetUnit") != "unicode_code_point":
            raise ContractMappingError(f"Unsupported offset unit on {node_id}", node_refs=[node_id])
        start, end = span.get("start"), span.get("end")
        if (not isinstance(start, int) or isinstance(start, bool) or
                not isinstance(end, int) or isinstance(end, bool) or start < 0 or end < start):
            raise ContractMappingError(f"Invalid source span on {node_id}", node_refs=[node_id])
        pairs.append((start, end))
    features = data.get("languageFeatures") or {}
    if not isinstance(features, dict):
        raise ContractMappingError(f"languageFeatures must be an object on {node_id}", node_refs=[node_id])
    return Ann(tuple(pairs), tuple(data.get("ruleIds", [])), data.get("basis"),
               tuple((str(k), str(v)) for k, v in features.items()))


def contract_graph_roots_to_kernel_v05_partial(
    expressions: Iterable[Mapping[str, Any]], root_refs: Iterable[str]
) -> KernelV05Graph:
    """Project supported roots independently; preserve failures and shared DAG nodes."""
    from usg import __version__
    if __version__ != "0.5.0":
        raise ContractMappingError(
            f"Kernel v0.5 adapter requires usg 0.5.0, found {__version__!r}; isolate the kernel import path"
        )
    from usg.grammar.node import (
        Node, OPS, predicate_app, connective, quantifier, opaque, unresolved_ref, sort_of,
    )

    node_map: dict[str, Mapping[str, Any]] = {}
    for item in expressions:
        node_id = item.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise ContractMappingError("Every contract expression needs a non-empty id")
        if node_id in node_map:
            raise ContractMappingError(f"Duplicate expression id: {node_id}", node_refs=[node_id])
        node_map[node_id] = item

    roots_requested = list(root_refs)
    built: dict[str, Node] = {}
    visiting: set[str] = set()
    node_identity_refs: dict[int, str] = {}
    original_metadata: dict[str, dict[str, Any]] = {}
    failed_roots: dict[str, str] = {}
    partial_refs: set[str] = set()
    diagnostics: list[str] = []

    def build(node_id: str) -> Node:
        if node_id in built:
            return built[node_id]
        if node_id in visiting:
            raise ContractMappingError("Expression graph contains a cycle", node_refs=[node_id])
        item = node_map.get(node_id)
        if item is None:
            raise ContractMappingError(f"Missing operand expression {node_id}", node_refs=[node_id])
        visiting.add(node_id)
        try:
            op = item.get("op")
            child_refs = item.get("operandRefs", [])
            if not isinstance(child_refs, list):
                raise ContractMappingError(f"operandRefs for {node_id} must be an array", node_refs=[node_id])
            children = tuple(build(ref) for ref in child_refs)
            params = dict(item.get("params") or {})
            ann = _annotation(item.get("annotations"), node_id)
            if op == "PREDICATE_APP":
                metadata = {k: params[k] for k in _METADATA_FIELDS[op] if k in params}
                result = predicate_app(params.get("predicate"), params.get("roles", ()), children, **metadata)
            elif op == "CONNECTIVE":
                metadata = {k: params[k] for k in _METADATA_FIELDS[op] if k in params}
                result = connective(params.get("connective"), children, params.get("operandRoles", ()), **metadata)
            elif op == "QUANTIFIER":
                metadata = {k: params[k] for k in ("surfaceText", "evidenceRefs", "attribution") if k in params}
                result = quantifier(
                    params.get("operatorType"), params.get("operator"), params.get("binderId"),
                    params.get("variable"), children[0], params.get("scopeKind"),
                    restrictor=params.get("restrictor"), variable_binding=params.get("variableBinding"),
                    count=params.get("count"), **metadata,
                )
            elif op == "OPAQUE":
                result = opaque(params.get("sourceOp"), params.get("reason"), params.get("sourceSort"),
                                operands=children, payload=params.get("payload"),
                                evidence_refs=params.get("evidenceRefs"))
            elif op == "UNRESOLVED_REF":
                result = unresolved_ref(
                    params.get("referenceId"), params.get("reason"), params.get("sourceSort"),
                    role=params.get("role"), mention_ref=params.get("mentionRef"),
                    evidence_refs=params.get("evidenceRefs"),
                )
            elif op in OPS:
                result = Node(op, children, _tuple_value(params), ann)
            else:
                result = opaque(
                    str(op), "No native v0.5.0 constructor is registered for this USG-SEM operator",
                    str(item.get("sort", "ANY")), operands=children,
                    payload={"sourceNodeId": node_id, "params": params, "operandRefs": child_refs},
                )
                partial_refs.add(node_id)
                diagnostics.append(f"{node_id}: {op!r} preserved as OPAQUE; operator semantics are not interpreted")
            if ann is not None and result.ann is None:
                result = result.with_ann(ann)
            expected_sort = item.get("sort")
            actual_sort = getattr(sort_of(result), "value", str(sort_of(result)))
            if result.op not in ("OPAQUE", "UNRESOLVED_REF") and expected_sort != actual_sort:
                raise ContractMappingError(
                    f"Sort mismatch for {node_id}: contract={expected_sort}, kernel 0.5.0={actual_sort}",
                    node_refs=[node_id],
                )
            # These fields are retained beside the native AST, not reinterpreted as semantics.
            sidecar = {key: copy.deepcopy(item[key]) for key in ("semanticKind", "interpretationStatus", "nativeId")
                       if key in item}
            if sidecar:
                original_metadata[node_id] = sidecar
            built[node_id] = result
            node_identity_refs[id(result)] = node_id
            return result
        except ContractMappingError:
            raise
        except Exception as exc:
            raise ContractMappingError(
                f"Kernel 0.5.0 rejected contract node {node_id}: {exc}", node_refs=[node_id]
            ) from exc
        finally:
            visiting.discard(node_id)

    imported_roots: dict[str, Node] = {}
    for root in roots_requested:
        try:
            imported_roots[root] = build(root)
        except ContractMappingError as exc:
            failed_roots[root] = str(exc)
            diagnostics.append(str(exc))

    return KernelV05Graph(
        expressions=node_map, root_refs=roots_requested, roots=imported_roots,
        node_identity_refs=node_identity_refs, original_node_metadata=original_metadata,
        failed_roots=failed_roots, partial_refs=partial_refs, diagnostics=diagnostics, preservation={},
    )


def contract_graph_roots_to_kernel_v05(
    expressions: Iterable[Mapping[str, Any]], root_refs: Iterable[str]
) -> dict[str, Any]:
    result = contract_graph_roots_to_kernel_v05_partial(expressions, root_refs)
    if result.failed_roots:
        details = "; ".join(f"{key}: {value}" for key, value in result.failed_roots.items())
        raise ContractMappingError(f"One or more roots are not representable in kernel 0.5.0: {details}",
                                   node_refs=result.failed_roots)
    return result.roots


def kernel_v05_graph_to_contract(
    imported: KernelV05Graph, *, validate: bool = True
) -> dict[str, Any]:
    """Serialize current native Nodes; retain failed roots and canonical-only fields."""
    from usg.grammar.node import Node, metadata_value, sort_of
    from usg.grammar.serialize import ann_to_json

    used_ids = set(imported.expressions)
    object_ids: dict[int, str] = {}
    records: list[dict[str, Any]] = []
    states: dict[int, int] = {}
    stack = [(root, False) for root in reversed(list(imported.roots.values()))]
    while stack:
        node, exiting = stack.pop()
        if not isinstance(node, Node):
            raise ContractMappingError(f"Non-Node in kernel v0.5 projection: {type(node).__name__}")
        ident = id(node)
        if ident in object_ids:
            continue
        if not exiting:
            if states.get(ident) == 1:
                raise ContractMappingError("Kernel v0.5 expression graph contains a cycle")
            states[ident] = 1
            stack.append((node, True))
            for child in reversed(node.args):
                if id(child) not in object_ids:
                    stack.append((child, False))
            continue
        node_id = imported.node_identity_refs.get(ident)
        if node_id is None:
            n = len(object_ids) + 1
            node_id = f"py05:node:{n}"
            while node_id in used_ids:
                n += 1
                node_id = f"py05:node:{n}"
            used_ids.add(node_id)
        object_ids[ident] = node_id
        params = {key: _json_value(value) for key, value in node.params_dict().items()}
        for key in _METADATA_FIELDS.get(node.op, ()):
            if key in params:
                params[key] = metadata_value(node, key)
        record = {
            "id": node_id, "op": node.op,
            "sort": getattr(sort_of(node), "value", str(sort_of(node))),
            "operandRefs": [object_ids[id(child)] for child in node.args],
            "params": params,
        }
        original = imported.expressions.get(node_id)
        if original:
            for key, value in imported.original_node_metadata.get(node_id, {}).items():
                record[key] = copy.deepcopy(value)
            original_ann = original.get("annotations")
            if original_ann and node.ann is not None:
                original_pairs = [(x.get("start"), x.get("end")) for x in original_ann.get("spans", [])]
                if original_pairs == list(node.ann.spans):
                    record["annotations"] = copy.deepcopy(original_ann)
                else:
                    imported.partial_refs.add(node_id)
                    imported.preservation[node_id] = {
                        "nativeAnnotation": {
                            "spans": [list(span) for span in node.ann.spans],
                            "rules": list(node.ann.rules),
                            "basis": node.ann.basis,
                            "features": [list(feature) for feature in node.ann.features],
                        },
                        "reason": "Native Ann does not retain sourceRef; original canonical annotation is retained separately",
                    }
                    record["annotations"] = copy.deepcopy(original_ann)
                    imported.diagnostics.append(
                        f"{node_id}: changed annotation spans have no sourceRef; canonical annotation retained and changed native annotation stored in preservation sidecar"
                    )
            elif node.ann is not None:
                record["annotations"] = ann_to_json(node.ann)
        elif node.ann is not None:
            record["annotations"] = ann_to_json(node.ann)
        records.append(record)
        states[ident] = 2

    by_id = {item["id"]: item for item in records}
    original_order = [key for key in imported.expressions if key in by_id]
    new_order = [item["id"] for item in records if item["id"] not in set(original_order)]
    serialized = [by_id[key] for key in original_order if key in by_id]
    serialized.extend(by_id[key] for key in new_order)
    projected_roots = [object_ids[id(root)] for root in imported.roots.values()]
    preserved_roots = [ref for ref in imported.root_refs if ref in imported.failed_roots]
    serialized_ids = {item["id"] for item in serialized}
    # Retain every original expression not represented by a current native Node.
    # This includes unreachable canonical nodes and the old version of an edited root.
    retained = [copy.deepcopy(item) for key, item in imported.expressions.items() if key not in serialized_ids]
    merged = {item["id"]: item for item in retained}
    merged.update({item["id"]: item for item in serialized})
    ordered_ids = list(dict.fromkeys(
        [key for key in imported.expressions if key in merged] +
        [item["id"] for item in serialized]
    ))
    all_records = [merged[key] for key in ordered_ids]
    unmapped = sorted(set(imported.failed_roots) | imported.partial_refs)
    result = {
        "profileId": "USG-SEM/1.0",
        "expressions": all_records,
        "rootExpressionRefs": projected_roots + preserved_roots,
        "mapping": {
            "sourceProfile": "usg-python-kernel",
            "sourceVersion": "0.5.0",
            "status": "PARTIAL" if unmapped else "LOSSLESS",
            "unmappedRefs": unmapped,
            "notes": list(imported.diagnostics) + [
                "Kernel v0.5.0 native Nodes were serialized afresh; canonical-only roots remain unchanged.",
                "PREDICATE_APP is SIT; proposition-level use requires an explicit HOLDS wrapper.",
                "OPAQUE and UNRESOLVED_REF are preservation nodes, not inferred semantic premises.",
            ],
        },
    }
    if imported.preservation:
        result["preservation"] = copy.deepcopy(imported.preservation)
    return result


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if hasattr(value, "value") and isinstance(value.value, (str, int, bool)):
        return value.value
    if value is None or isinstance(value, (str, int, bool, float)):
        return value
    raise ContractMappingError(f"Unsupported Python semantic parameter value: {type(value).__name__}")
