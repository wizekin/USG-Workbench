"""Seeded random expression generator for property tests (no external libraries)."""

import random

from usg.grammar.node import (Node, and_, apply, holds, modal, not_, or_, prop, q, ref, relate, same_as, speech_time,
                              tense, value, var, walk)
from usg.grammar.scope import _rename

COLORS = ("Red", "Blue", "Green")
VARS = ("x", "y", "z", "w")


def term(rng, env):
    if env and rng.random() < 0.4:
        return var(rng.choice(sorted(env)))
    return ref(f"REFERENT:{rng.randint(1, 4)}")


def atom(rng, env):
    k = rng.random()
    R = lambda: ref(f"REFERENT:{rng.randint(1, 4)}")
    if k < 0.25:
        return holds(apply("GIVE", 1, {"AGENT": term(rng, env), "SOURCE": R(), "RECIPIENT": R(), "THEME": R()}))
    if k < 0.45:
        return prop(term(rng, env), "Color", value(rng.choice(COLORS)))
    if k < 0.6:
        rel = rng.choice(("PROPER_PART_OF", "HAS_PART", "DISJOINT_WITH"))
        return relate(rel, term(rng, env), term(rng, env))
    if k < 0.7:
        return same_as(term(rng, env), term(rng, env))
    return holds(apply("OPEN", 1, {"UNDERGOER": term(rng, env)}))


def gen(rng, depth, env=frozenset()):
    if depth <= 0 or rng.random() < 0.2:
        return atom(rng, env)
    c = rng.random()
    sub = lambda: gen(rng, depth - 1, env)
    if c < 0.25:
        return and_(*[sub() for _ in range(rng.randint(2, 3))])
    if c < 0.45:
        return or_(*[sub() for _ in range(rng.randint(2, 3))])
    if c < 0.55:
        return not_(sub())
    if c < 0.65:
        return modal(rng.choice(("POSSIBILITY", "NECESSITY")), rng.choice(("EPISTEMIC", "DEONTIC")), sub())
    if c < 0.75:
        return tense(rng.choice(("PAST", "PRESENT", "FUTURE")), speech_time(), sub())
    free = [v for v in VARS if v not in env]
    if not free:
        return atom(rng, env)
    name = rng.choice(free)
    inner = env | {name}
    return q(rng.choice(("EXISTS", "FORALL", "NO", "MOST", "GEN")), name,
             prop(var(name), "Color", value(rng.choice(COLORS))), gen(rng, depth - 1, inner))


def shuffle_tree(node, rng):
    """Reorder AND/OR children everywhere and rename bound variables arbitrarily: meaning-preserving noise."""
    args = [shuffle_tree(a, rng) for a in node.args]
    if node.op in ("AND", "OR"):
        rng.shuffle(args)
    return Node(node.op, tuple(args), node.params, node.ann)


def rename_bound(node, rng):
    salt = rng.randint(100, 999)
    return _rename(node, {}, [0], namer=lambda i: f"r{salt}_{i}")
