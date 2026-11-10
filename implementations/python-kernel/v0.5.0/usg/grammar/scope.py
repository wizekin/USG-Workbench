"""Variables, binders and scope (spec Part 3 §3.6, SG-CON-005a-e).

Q binds one variable. The variable is visible in the restrictor and the scope
(arguments 0 and 1) but not in the optional domain (argument 2).

  VC-S12  an asserted expression has no free variable
  VC-S13  a binder never rebinds a variable already in scope (no shadowing)
  SG-CON-005c  variables are alpha-renamed v0, v1, ... in order of binder occurrence
"""

from __future__ import annotations

import json
from .node import Node


def _scan(node: Node, env: frozenset[str], free: set[str], issues: list[tuple[str, str]]) -> None:
    if node.op == "VAR":
        name, binder_id = node.get("name"), node.get("binderId")
        token = "@" + binder_id if binder_id is not None else name
        if token not in env:
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
    if node.op == "QUANTIFIER":
        binder_id = node.get("binderId")
        token = "@" + binder_id
        if token in env:
            issues.append(("VC-S13", f"duplicate active binder identity {binder_id!r}"))
        _scan(node.args[0], env | {token}, free, issues)
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
        params = {"name": name if node.get("binderId") is not None else mapping.get(name, name)}
        if node.get("binderId") is not None:
            params["binderId"] = node.get("binderId")
        return Node("VAR", (), params, node.ann)
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


# Step 5B: stable-identity binder operations for native QUANTIFIER nodes.
def free_variable_occurrences(node: Node) -> list[tuple[tuple[int, ...], str, str | None]]:
    """Return (operand path, display name, binderId) for every free variable occurrence."""
    found: list[tuple[tuple[int, ...], str, str | None]] = []
    def visit(n: Node, path: tuple[int, ...], names: frozenset[str], ids: frozenset[str]) -> None:
        if n.op == "VAR":
            name, binder_id = n.get("name"), n.get("binderId")
            is_free = binder_id not in ids if binder_id is not None else name not in names
            if is_free:
                found.append((path, name, binder_id))
            return
        if n.op == "Q":
            v = n.get("var")
            if v in names:
                raise ValueError(f"legacy Q binder shadows active variable {v!r}")
            for i, child in enumerate(n.args):
                visit(child, path + (i,), names | {v} if i < 2 else names, ids)
            return
        if n.op == "QUANTIFIER":
            binder_id = n.get("binderId")
            if binder_id in ids:
                raise ValueError(f"duplicate active binder identity {binder_id!r}")
            visit(n.args[0], path + (0,), names, ids | {binder_id})
            return
        for i, child in enumerate(n.args):
            visit(child, path + (i,), names, ids)
    visit(node, (), frozenset(), frozenset())
    return found


def check_native_scope(node: Node, *, closed: bool = True) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    free = free_variable_occurrences(node)
    if closed and free:
        labels = sorted({name for _, name, _ in free})
        issues.append(("VC-S12", f"free variable occurrence(s): {labels}"))
    return issues


def alpha_equivalent(left: Node, right: Node) -> bool:
    """Compare expressions modulo binder identity/display-name renaming, not operator/scope changes."""
    def eq(a: Node, b: Node, binders: dict[str, str], names: dict[str, str]) -> bool:
        if a.op != b.op or len(a.args) != len(b.args):
            return False
        if a.op == "VAR":
            aid, bid = a.get("binderId"), b.get("binderId")
            if aid is not None or bid is not None:
                return aid is not None and bid is not None and binders.get(aid) == bid
            return names.get(a.get("name"), a.get("name")) == b.get("name")
        ap, bp = a.params_dict(), b.params_dict()
        if a.op == "QUANTIFIER":
            aid, bid = a.get("binderId"), b.get("binderId")
            avar, bvar = a.get("variable"), b.get("variable")
            for key in ("binderId", "variable"):
                ap.pop(key, None); bp.pop(key, None)
            # Binding metadata refers to the binder. Normalize only those two
            # identity/display fields; role and referent constraints stay exact.
            for params, old_id, old_var in ((ap, aid, avar), (bp, bid, bvar)):
                raw = params.get("variableBinding")
                if isinstance(raw, str):
                    try:
                        data = json.loads(raw)
                    except ValueError:
                        data = None
                    if isinstance(data, dict):
                        if data.get("binderId") == old_id:
                            data["binderId"] = "$BOUND"
                        if data.get("variable") == old_var:
                            data["variable"] = "$VARIABLE"
                        params["variableBinding"] = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if ap != bp:
                return False
            return eq(a.args[0], b.args[0], {**binders, aid: bid}, names)
        if a.op == "Q":
            av, bv = ap.pop("var", None), bp.pop("var", None)
            if ap != bp:
                return False
            inner = {**names, av: bv}
            return all(eq(x, y, binders, inner if i < 2 else names)
                       for i, (x, y) in enumerate(zip(a.args, b.args)))
        if ap != bp:
            return False
        return all(eq(x, y, binders, names) for x, y in zip(a.args, b.args))
    return eq(left, right, {}, {})


def substitute_free(node: Node, variable: str, replacement: Node) -> Node:
    """Capture-avoiding substitution for free name-bound variables.

    QUANTIFIER-bound occurrences carry binderId, so a display-name collision
    cannot capture a replacement. Legacy Q continues to bind by variable name.
    """
    if node.op == "VAR":
        if node.get("binderId") is None and node.get("name") == variable:
            return replacement
        return node
    if node.op == "Q":
        binder = node.get("var")
        args = tuple(a if i < 2 and binder == variable else substitute_free(a, variable, replacement)
                     for i, a in enumerate(node.args))
        return Node("Q", args, node.params, node.ann)
    if not node.args:
        return node
    return Node(node.op, tuple(substitute_free(a, variable, replacement) for a in node.args),
                node.params, node.ann)
