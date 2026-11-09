"""Canonical serialisation and hashing of expressions (spec Part 3 §3.16–3.17, Part 11 §11.11).

* ``canonical_string`` / ``structural_hash`` ignore annotations (SG-CAN-004): two
  expressions that differ only in provenance are structurally equal.
* ``full_hash`` includes annotations (record-level identity).
* JSON round trip is exact: ``node_from_json(node_to_json(n)) == n``.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..util import canonical_json, sha256_hex
from .node import Ann, Node


def _val(v: Any) -> Any:
    return [_val(x) for x in v] if isinstance(v, tuple) else v


def ann_to_json(a: Ann | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {"spans": [list(s) for s in a.spans], "rules": list(a.rules), "basis": a.basis,
            "features": [list(f) for f in a.features]}


def ann_from_json(d: Mapping[str, Any] | None) -> Ann | None:
    if d is None:
        return None
    return Ann(tuple(tuple(s) for s in d.get("spans", ())), tuple(d.get("rules", ())), d.get("basis"),
               tuple(tuple(f) for f in d.get("features", ())))


def node_to_json(n: Node, include_ann: bool = True) -> dict[str, Any]:
    d: dict[str, Any] = {"op": n.op, "params": {k: _val(v) for k, v in n.params}, "args": [node_to_json(a, include_ann) for a in n.args]}
    if include_ann and n.ann is not None:
        d["ann"] = ann_to_json(n.ann)
    return d


def node_from_json(d: Mapping[str, Any]) -> Node:
    return Node(d["op"], tuple(node_from_json(a) for a in d.get("args", ())), dict(d.get("params", {})),
                ann_from_json(d.get("ann")))


def canonical_string(n: Node) -> str:
    return canonical_json(node_to_json(n, include_ann=False))


def structural_hash(n: Node) -> str:
    return sha256_hex(canonical_string(n))


def full_hash(n: Node) -> str:
    return sha256_hex(canonical_json(node_to_json(n, include_ann=True)))
