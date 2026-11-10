import unittest

from usg.errors import InvariantViolation
from usg.grammar import node as N
from usg.grammar.node import (Ann, Node, alt, and_, apply, assert_, cond, depth, error, extent, fig, hole, holds,
                              kind, lit, modal, not_, or_, pretty, q, ref, relate, role_entries, size, sort_of,
                              speech_time, tense, value, var, walk)
from usg.grammar.scope import alpha_rename, anonymize_bound, check_scope, free_vars
from usg.grammar.serialize import (canonical_string, full_hash, node_from_json, node_to_json, structural_hash)

R = lambda n: ref(f"REFERENT:{n}")


def give(a=1, s=1, r=2, t=3):
    return apply("GIVE", 1, {"AGENT": R(a), "SOURCE": R(s), "RECIPIENT": R(r), "THEME": R(t)})


def raises(code, fn):
    try:
        fn()
    except InvariantViolation as e:
        assert e.code == code, f"expected {code}, got {e.code}: {e}"
        return e
    raise AssertionError("did not raise")


class NodeTests(unittest.TestCase):
    def test_sorts_of_builders(self):
        S = N.Sort
        self.assertEqual(sort_of(R(1)), S.TERM)
        self.assertEqual(sort_of(lit(2, "Integer")), S.VAL)
        self.assertEqual(sort_of(value("Red")), S.VAL)
        self.assertEqual(sort_of(give()), S.SIT)
        self.assertEqual(sort_of(holds(give())), S.PROP)
        self.assertEqual(sort_of(extent(give())), S.TIME)
        self.assertEqual(sort_of(speech_time()), S.TIME)
        self.assertEqual(sort_of(hole()), N.ANY)

    def test_negated_situation_is_a_proposition_never_an_event(self):
        n = not_(give())
        self.assertEqual(sort_of(n), N.Sort.PROP)
        self.assertEqual(n.args[0].op, "HOLDS")  # shorthand expanded: NOT applies to a proposition (SG-CON-009)
        e = raises("SG-CON-006", lambda: Node("NOT", (give(),)))
        self.assertIn("HOLDS", str(e))
        raises("SG-CON-006", lambda: Node("HOLDS", (holds(give()),)))  # a proposition is not a situation

    def test_shorthand_holds_in_every_builder(self):
        g = give()
        for built in (and_(g, g), or_(g, g), cond(g, g), q("EXISTS", "x", g, g), modal("POSSIBILITY", "EPISTEMIC", g),
                      tense("PAST", speech_time(), g), assert_(g)):
            for a in built.args:
                if sort_of(a) in (N.Sort.SIT,):
                    self.fail(f"{built.op} kept a bare situation")
        self.assertEqual(assert_(g).args[0], holds(g))

    def test_signature_violations(self):
        raises("SG-CON-006", lambda: Node("BOGUS"))
        raises("SG-CON-006", lambda: Node("AND", (holds(give()),)))  # needs >= 2
        raises("SG-CON-006", lambda: Node("TENSE", (holds(give()), speech_time()), {"tense": "PAST"}))  # arg order/sorts
        raises("SG-CON-006", lambda: Node("MODAL", (holds(give()),), {"force": "NECESSITY"}))  # missing param
        raises("SG-CON-006", lambda: Node("REF", (), {"ref": "REFERENT:1", "junk": 1}))  # unexpected param
        raises("SG-CON-006", lambda: Node("LIT", (), {"value": 1.5, "vtype": "Decimal"}))  # no binary floats
        raises("SG-CON-006", lambda: Node("RELATE", (R(1),), {"relation": "X"}))
        raises("SG-CON-006", lambda: Node("APPLY", (R(1),), {"frame": "G", "version": 1, "roles": ("A#0", "B#0")}))

    def test_alt_and_fig_rules(self):
        a, b = holds(give()), holds(give(2, 2, 1, 3))
        ok = alt("g1", [a, b])
        self.assertEqual(ok.get("ranks"), (1, 2))
        self.assertEqual(sort_of(ok), N.Sort.PROP)
        raises("SG-CON-007", lambda: alt("g", [a, give()]))  # mixed sorts
        raises("SG-CON-007", lambda: alt("g", [a, b], ranks=[1]))  # one ordinal rank per alternative
        raises("SG-CON-006", lambda: Node("ALT", (a,), {"group": "g", "ranks": (1,)}))  # at least two
        raises("SG-TYP-002", lambda: fig("m", give(), holds(give())))  # same sort on both sides
        self.assertEqual(fig("m", give(), give(2, 2, 1, 3)).op, "FIG")

    def test_apply_ordering_is_canonical(self):
        a = apply("GIVE", 1, {"AGENT": R(1), "THEME": R(3), "RECIPIENT": R(2)})
        b = apply("GIVE", 1, {"RECIPIENT": R(2), "AGENT": R(1), "THEME": R(3)})
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual([r for r, _, _ in role_entries(a)], ["AGENT", "RECIPIENT", "THEME"])
        multi = apply("X", 1, {"INPUTS": [R(1), R(2), R(3)]})
        self.assertEqual([(r, o) for r, o, _ in role_entries(multi)], [("INPUTS", 0), ("INPUTS", 1), ("INPUTS", 2)])

    def test_annotations_never_change_equality(self):
        plain = R(1)
        noted = R(1).with_ann(Ann(spans=((0, 3),), rules=("SG-INT-010",), basis="EXPLICIT"))
        self.assertEqual(plain, noted)
        self.assertEqual(hash(plain), hash(noted))
        self.assertEqual(structural_hash(plain), structural_hash(noted))  # SG-CAN-004
        self.assertNotEqual(full_hash(plain), full_hash(noted))
        self.assertEqual(holds(give()), holds(give(1, 1, 2, 3)))

    def test_params_are_normalised_and_sorted(self):
        a = Node("Q", (holds(give()), holds(give())), {"var": "x", "quant": "EXISTS"})
        b = Node("Q", (holds(give()), holds(give())), (("quant", "EXISTS"), ("var", "x")))
        self.assertEqual(a, b)
        self.assertEqual([k for k, _ in a.params], ["quant", "var"])
        self.assertIsInstance(apply("G", 1, {"A": R(1)}).get("roles"), tuple)

    def test_traversal_helpers(self):
        t = assert_(not_(give()))
        ops = [n.op for _, n in walk(t)]
        self.assertEqual(ops[:3], ["ASSERT", "NOT", "HOLDS"])
        self.assertEqual(depth(t), 5)  # ASSERT NOT HOLDS APPLY REF
        self.assertEqual(size(t), len(ops))
        self.assertIn("GIVE@1", pretty(t))
        self.assertIn("NOT", str(t))
        self.assertEqual(error("X").op, "ERROR")
        self.assertEqual(hole("UNKNOWN").get("state"), "UNKNOWN")


class SerializeTests(unittest.TestCase):
    def sample(self):
        return assert_(tense("PAST", speech_time(), and_(
            give().with_ann(Ann(spans=((4, 10),), rules=("SG-INT-012",), basis="GRAMMATICAL")),
            q("EXACTLY", "x", holds(apply("OPEN", 1, {"UNDERGOER": var("x")})), holds(give()), n=2),
            alt("g", [holds(give()), holds(give(2, 2, 1, 3))]))), origin="SOURCE_TEXT")

    def test_json_roundtrip_is_exact(self):
        s = self.sample()
        back = node_from_json(node_to_json(s))
        self.assertEqual(back, s)
        self.assertEqual(full_hash(back), full_hash(s))  # annotations survive too
        walk_ann = [n.ann for _, n in walk(back) if n.ann is not None]
        self.assertEqual(walk_ann[0].spans, ((4, 10),))

    def test_canonical_string_is_stable(self):
        s = self.sample()
        self.assertEqual(canonical_string(s), canonical_string(node_from_json(node_to_json(s))))
        a = Node("LIT", (), {"value": "x", "vtype": "Text", "unit": "m"})
        b = Node("LIT", (), (("unit", "m"), ("vtype", "Text"), ("value", "x")))
        self.assertEqual(canonical_string(a), canonical_string(b))
        self.assertNotIn("ann", canonical_string(s))


class ScopeTests(unittest.TestCase):
    def body(self, v):
        return holds(apply("OPEN", 1, {"UNDERGOER": var(v)}))

    def test_free_variables(self):
        self.assertEqual(free_vars(self.body("x")), {"x"})
        closed = q("EXISTS", "x", self.body("x"), self.body("x"))
        self.assertEqual(free_vars(closed), set())
        self.assertEqual([c for c, _ in check_scope(assert_(self.body("x")))], ["VC-S12"])
        self.assertEqual(check_scope(self.body("x"), closed=False), [])
        self.assertEqual(check_scope(assert_(closed)), [])

    def test_variable_is_not_visible_in_the_domain(self):
        domain = holds(apply("OPEN", 1, {"UNDERGOER": var("x")}))
        n = Node("Q", (self.body("x"), self.body("x"), var("x")), {"quant": "EXISTS", "var": "x"})
        self.assertEqual({"x"}, free_vars(n))  # the third argument (domain) sees no binding

    def test_shadowing_is_rejected(self):
        inner = q("EXISTS", "x", self.body("x"), self.body("x"))
        outer = q("FORALL", "x", self.body("x"), inner)
        self.assertEqual([c for c, _ in check_scope(assert_(outer))], ["VC-S13"])
        sibling = and_(inner, q("FORALL", "x", self.body("x"), self.body("x")))
        self.assertEqual(check_scope(assert_(sibling)), [])  # reusing a name in a sibling binder is fine

    def test_alpha_renaming_gives_canonical_names(self):
        a = q("EXISTS", "x", self.body("x"), q("FORALL", "y", self.body("y"), self.body("x")))
        b = q("EXISTS", "p", self.body("p"), q("FORALL", "q", self.body("q"), self.body("p")))
        self.assertNotEqual(canonical_string(a), canonical_string(b))
        self.assertEqual(alpha_rename(a), alpha_rename(b))  # alpha-equivalent => equal
        ra = alpha_rename(a)
        self.assertEqual(ra.get("var"), "v0")
        self.assertEqual(ra.args[1].get("var"), "v1")
        self.assertEqual(alpha_rename(ra), ra)  # idempotent
        sib = and_(q("EXISTS", "x", self.body("x"), self.body("x")), q("EXISTS", "x", self.body("x"), self.body("x")))
        names = [n.get("var") for _, n in walk(alpha_rename(sib)) if n.op == "Q"]
        self.assertEqual(names, ["v0", "v1"])
        self.assertEqual({n.get("var") for _, n in walk(anonymize_bound(a)) if n.op == "Q"}, {"_"})

    def test_free_names_are_not_renamed(self):
        n = and_(self.body("free"), q("EXISTS", "x", self.body("x"), self.body("x")))
        self.assertEqual(free_vars(alpha_rename(n)), {"free"})


if __name__ == "__main__":
    unittest.main()
