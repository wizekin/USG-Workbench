from __future__ import annotations

from .node import Ann, Node


def explicit(node: Node, *spans: tuple[int, int]) -> Node:
    """The element is stated by these source spans (basis EXPLICIT)."""
    return node.with_ann(Ann(spans=tuple(spans), basis="EXPLICIT"))


def grammatical(node: Node, rule: str, *spans: tuple[int, int]) -> Node:
    """Derived from syntax by a registered interpretation/construction rule (basis GRAMMATICAL)."""
    return node.with_ann(Ann(spans=tuple(spans), rules=(rule,), basis="GRAMMATICAL"))


def background(node: Node, rule: str, *spans: tuple[int, int]) -> Node:
    """Inferred from background knowledge by a registered inference rule (basis BACKGROUND)."""
    return node.with_ann(Ann(spans=tuple(spans), rules=(rule,), basis="BACKGROUND"))