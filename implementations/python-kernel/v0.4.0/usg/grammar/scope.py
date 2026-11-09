"""Variables, binders and scope (spec Part 3 §3.6, SG-CON-005a-e).

Q binds one variable. The variable is visible in the restrictor and the scope
(arguments 0 and 1) but not in the optional domain (argument 2).

  VC-S12  an asserted expression has no free variable
  VC-S13  a binder never rebinds a variable already in scope (no shadowing)
  SG-CON-005c  variables are alpha-renamed v0, v1, ... in order of binder occurrence
"""

from __future__ import annotations

from .node import Node


def _scan(node: Node, env: frozenset[str], free: set[str], issues: list[tuple[str, str]]) -> None:
    if node.op == "VAR":
        name = node.get("name")
        if name not in env:
            free.add(name)
        return
    if node.op == "Q":
        v = node.get("var")
        if v in env:
            issues.append(("VC-S13", f"binder {v!r} shadows a variable already in scope"))
        inner = env | {v}
        for i, a in enumerate(node.args):
            _scan(a, inner if i < 2 else env, free, issues)
        return
    for a in node.args:
        _scan(a, env, free, issues)


def free_vars(node: Node) -> set[str]:
    free: set[str] = set()
    _scan(node, frozenset(), free, [])
    return free


def check_scope(node: Node, *, closed: bool = True) -> list[tuple[str, str]]:
    free: set[str] = set()
    issues: list[tuple[str, str]] = []
    _scan(node, frozenset(), free, issues)
    if closed and free:
        issues.append(("VC-S12", f"free variable(s) {sorted(free)} in a closed expression"))
    return issues


def _rename(node: Node, mapping: dict[str, str], counter: list[int], namer=None) -> Node:
    if node.op == "VAR":
        name = node.get("name")
        return Node("VAR", (), {"name": mapping.get(name, name)}, node.ann)
    if node.op == "Q":
        old = node.get("var")
        new = namer(counter[0]) if namer else f"v{counter[0]}"
        counter[0] += 1
        inner = {**mapping, old: new}
        args = [_rename(a, inner if i < 2 else mapping, counter, namer) for i, a in enumerate(node.args)]
        params = {**node.params_dict(), "var": new}
        return Node("Q", tuple(args), params, node.ann)
    if not node.args:
        return node
    return Node(node.op, tuple(_rename(a, mapping, counter, namer) for a in node.args), node.params, node.ann)


def alpha_rename(node: Node) -> Node:
    """Canonical variable names (SG-CON-005c): equal up to renaming => structurally equal."""
    return _rename(node, {}, [0])


def anonymize_bound(node: Node) -> Node:
    """Replace every BOUND variable name by '_' (used only to build order-independent sort keys)."""
    return _rename(node, {}, [0], namer=lambda i: "_")


def to_debruijn(node: Node, env: tuple[str, ...] = ()) -> Node:
    """Variables as binding distances (innermost binder = 0); binder names erased.

    Used ONLY to build sort keys: it is independent of variable names, of the
    order of sibling subtrees, and of renaming, which is exactly what makes
    canonical ordering idempotent. ``env`` lists the enclosing binders
    (outermost first); variables not bound anywhere keep their names."""
    if node.op == "VAR":
        name = node.get("name")
        for i, n in enumerate(reversed(env)):
            if n == name:
                return Node("VAR", (), {"name": f"#{i}"})
        return node
    if node.op == "Q":
        v = node.get("var")
        args = [to_debruijn(a, env + (v,) if i < 2 else env) for i, a in enumerate(node.args)]
        return Node("Q", tuple(args), {**node.params_dict(), "var": "#"})
    if not node.args:
        return node
    return Node(node.op, tuple(to_debruijn(a, env) for a in node.args), node.params)
