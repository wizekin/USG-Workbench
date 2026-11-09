"""Opaque contexts (spec Part 3 §3.12, SG-KNW-003).

Substituting identical referents is valid in the author's context but NOT inside
another agent's attitude: from "Clark = Superman" one may not conclude "Lois
believes Clark is Superman". Opaque positions are the content of an ATTRIBUTE
node and every role whose tier-1 parent is CONTENT (believe / know / want / say /
attempt / offer ...). ``substitute_referent`` replaces a referent everywhere
EXCEPT those positions."""

from __future__ import annotations

from ..model.frames import FrameLibrary
from .node import Node, role_entries


def is_opaque_role(frame: str, role: str, library: FrameLibrary | None) -> bool:
    if role == "CONTENT":
        return True
    if library is not None and library.has(frame):
        r = library.resolved(frame).role(role)
        return r is not None and r.spec.tier1_parent == "CONTENT"
    return False


def substitute_referent(node: Node, old: str, new: str, library: FrameLibrary | None = None) -> Node:
    if node.op == "REF":
        return Node("REF", (), {"ref": new}, node.ann) if node.get("ref") == old else node
    if node.op == "ATTRIBUTE":
        holder, content = node.args
        return Node("ATTRIBUTE", (substitute_referent(holder, old, new, library), content), node.params, node.ann)
    if node.op == "APPLY":
        frame = node.get("frame")
        args = []
        for (role, _o, filler) in role_entries(node):
            args.append(filler if is_opaque_role(frame, role, library) else substitute_referent(filler, old, new, library))
        return Node("APPLY", tuple(args), node.params, node.ann)
    if not node.args:
        return node
    return Node(node.op, tuple(substitute_referent(a, old, new, library) for a in node.args), node.params, node.ann)
