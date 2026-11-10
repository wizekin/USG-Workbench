"""Strict USG-SEM/1.0 expression-graph adapter for Python kernel 0.4.0.

The adapter preserves graph identity (including shared DAG nodes), operand order,
sorts, parameters and supported annotations. Unsupported constructors or metadata
are rejected; no nearest-operator coercion is attempted.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping


class ContractMappingError(ValueError):
    def __init__(self, message: str, *, node_refs: Iterable[str] = ()):
        super().__init__(message)
        self.node_refs = tuple(node_refs)


def _tuple_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_tuple_value(v) for v in value)
    if isinstance(value, dict):
        return {k: _tuple_value(v) for k, v in value.items()}
    return value


def _annotation_from_contract(data: Mapping[str, Any] | None, node_id: str):
    if not data:
        return None
    from usg.grammar.serialize import ann_from_json

    allowed = {"spans", "ruleIds", "basis", "languageFeatures"}
    extra = set(data) - allowed
    if extra:
        raise ContractMappingError(
            f"Python SemIR Ann cannot preserve annotation fields {sorted(extra)} on {node_id}",
            node_refs=[node_id],
        )
    spans = data.get("spans", [])
    source_refs = set()
    pairs = []
    for span in spans:
        if span.get("offsetUnit") != "unicode_code_point":
            raise ContractMappingError(
                f"Unsupported annotation offset unit on {node_id}: {span.get('offsetUnit')}",
                node_refs=[node_id],
            )
        start, end = span.get("start"), span.get("end")
        if (not isinstance(start, int) or isinstance(start, bool) or
                not isinstance(end, int) or isinstance(end, bool) or
                start < 0 or end < start):
            raise ContractMappingError(f"Invalid annotation span on {node_id}", node_refs=[node_id])
        source_refs.add(span.get("sourceRef"))
        pairs.append([start, end])
    if len(source_refs) > 1:
        raise ContractMappingError(
            f"SemIR Ann stores source-relative offsets but not multiple source IDs ({node_id})",
            node_refs=[node_id],
        )
    features = data.get("languageFeatures") or {}
    if not isinstance(features, dict):
        raise ContractMappingError(f"languageFeatures must be an object on {node_id}", node_refs=[node_id])
    return ann_from_json({
        "spans": pairs,
        "rules": list(data.get("ruleIds", [])),
        "basis": data.get("basis"),
        "features": [[str(k), str(v)] for k, v in features.items()],
    })


def contract_graph_roots_to_semir_partial(
    expressions: Iterable[Mapping[str, Any]],
    root_refs: Iterable[str],
) -> dict[str, Any]:
    """Import each root independently while sharing successfully built DAG nodes.

    A failed root does not prevent an unrelated supported root from being
    projected. The result reports failed roots and the exact nodes reachable
    from successful roots.
    """
    try:
        from usg.grammar.node import Node, OPS
    except Exception as exc:
        raise ContractMappingError("The USG Python kernel package is not importable") from exc

    node_map: dict[str, Mapping[str, Any]] = {}
    for item in expressions:
        node_id = item.get("id")
        if not isinstance(node_id, str) or not node_id:
            raise ContractMappingError("Every contract expression needs a non-empty id")
        if node_id in node_map:
            raise ContractMappingError(f"Duplicate expression id: {node_id}", node_refs=[node_id])
        node_map[node_id] = item

    roots = list(root_refs)
    built: dict[str, Node] = {}
    visiting: set[str] = set()

    def build(node_id: str) -> Node:
        if node_id in built:
            return built[node_id]
        if node_id in visiting:
            raise ContractMappingError("Expression graph contains a cycle", node_refs=[node_id])
        item = node_map.get(node_id)
        if item is None:
            raise ContractMappingError(f"Missing operand expression {node_id}", node_refs=[node_id])
        op = item.get("op")
        if op not in OPS:
            raise ContractMappingError(
                f"Contract operator {op!r} is not implemented by Python kernel 0.4.0; no coercion was attempted",
                node_refs=[node_id],
            )
        for field in ("semanticKind", "interpretationStatus", "nativeId"):
            if item.get(field) is not None:
                raise ContractMappingError(
                    f"Python SemIR 0.4.0 cannot preserve expression field {field} ({node_id})",
                    node_refs=[node_id],
                )
        visiting.add(node_id)
        try:
            child_refs = item.get("operandRefs", [])
            if not isinstance(child_refs, list):
                raise ContractMappingError(f"operandRefs for {node_id} must be an array", node_refs=[node_id])
            children = tuple(build(ref) for ref in child_refs)
            params = _tuple_value(dict(item.get("params") or {}))
            ann = _annotation_from_contract(item.get("annotations"), node_id)
            try:
                result = Node(op, children, params, ann)
            except Exception as exc:
                raise ContractMappingError(
                    f"Python SemIR rejected contract node {node_id}: {exc}", node_refs=[node_id]
                ) from exc
            expected_sort = item.get("sort")
            actual_sort = getattr(result.sort, "value", str(result.sort))
            if expected_sort != actual_sort:
                raise ContractMappingError(
                    f"Sort mismatch for {node_id}: contract={expected_sort}, Python SemIR={actual_sort}",
                    node_refs=[node_id],
                )
            built[node_id] = result
            return result
        finally:
            visiting.discard(node_id)

    imported_roots: dict[str, Node] = {}
    failed_roots: dict[str, str] = {}
    for root in roots:
        try:
            imported_roots[root] = build(root)
        except ContractMappingError as exc:
            failed_roots[root] = str(exc)

    reachable: set[str] = set()
    pending = list(imported_roots)
    while pending:
        node_id = pending.pop()
        if node_id in reachable or node_id not in node_map:
            continue
        reachable.add(node_id)
        pending.extend(node_map[node_id].get("operandRefs", []))

    return {
        "roots": imported_roots,
        "failedRoots": failed_roots,
        "mappedNodeRefs": sorted(reachable),
        # Preserve object identity while the native projections are alive.
        # Reverse serialization uses this map to distinguish edited/new Nodes
        # from original nodes without guessing by structural similarity.
        "nodes": dict(built),
    }


def contract_graph_roots_to_semir(
    expressions: Iterable[Mapping[str, Any]],
    root_refs: Iterable[str],
) -> dict[str, Any]:
    """Strict multi-root conversion; preserves shared DAG identity or fails."""
    result = contract_graph_roots_to_semir_partial(expressions, root_refs)
    if result["failedRoots"]:
        failures = "; ".join(f"{ref}: {message}" for ref, message in result["failedRoots"].items())
        raise ContractMappingError(f"One or more expression roots are not representable: {failures}",
                                   node_refs=result["failedRoots"].keys())
    return result["roots"]


def contract_graph_to_semir(
    expressions: Iterable[Mapping[str, Any]],
    root_ref: str,
) -> Any:
    """Strict single-root compatibility wrapper."""
    return contract_graph_roots_to_semir(expressions, [root_ref])[root_ref]


def mapping_report_for_python(expressions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Static constructor/metadata coverage report for kernel 0.4.0."""
    from usg.grammar.node import OPS

    unmapped = []
    for item in expressions:
        node_id = str(item.get("id"))
        ann = item.get("annotations") or {}
        unsupported = (
            item.get("op") not in OPS
            or any(item.get(k) is not None for k in ("semanticKind", "interpretationStatus", "nativeId"))
            or bool(set(ann) - {"spans", "ruleIds", "basis", "languageFeatures"})
            or any(s.get("offsetUnit") != "unicode_code_point" for s in ann.get("spans", []))
        )
        if unsupported:
            unmapped.append(node_id)
    return {
        "sourceProfile": "USG-SEM/1.0",
        "sourceVersion": "1.0",
        "targetProfile": "usg-python-kernel",
        "targetVersion": "0.4.0",
        "status": "LOSSLESS" if not unmapped else "PARTIAL",
        "unmappedRefs": unmapped,
        "notes": [] if not unmapped else [
            "Unsupported constructors or metadata remain in the canonical document and are not coerced."
        ],
    }
