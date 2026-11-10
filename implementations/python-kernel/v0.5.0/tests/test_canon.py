import random
import unittest

from usg.core.records import Anchor
from usg.foundation.builder import build_foundation
from usg.grammar.canon import CANON_RULES, CanonTrace, canonicalize
from usg.grammar.node import (Ann, Node, and_, apply, assert_, attribute, different_from, holds, kind, modal, not_, or_,
                              prop, q, ref, relate, same_as, speech_time, tense, time_rel, value, var, walk)
from usg.grammar.opaque import is_opaque_role, substitute_referent
from usg.grammar.scope import check_scope
from usg.grammar.serialize import canonical_string, node_from_json, node_to_json, structural_hash
from usg.grammar.typecheck import Typechecker
from tests.gen import gen, rename_bound, shuffle_tree

FND = build_foundation()
REL = FND.relations
R = lambda n: ref(f"REFERENT:{n}")
red = lambda t: prop(t, "Color", value("Red"))
blue = lambda t: prop(t, "Color", value("Blue"))
canon = lambda n, **kw: canonicalize(n, relations=REL, **kw)


class PermittedNormalizationTests(unittest.TestCase):
    def test_and_or_flatten_and_sort(self):
        a, b, c = red(R(3)), red(R(1)), blue(R(2))
        left = canon(and_(and_(a, b), c))
        right = canon(and_(a, and_(b, c)))
        flat = canon(and_(c, a, b))
        self.assertEqual(left, right)
        self.assertEqual(left, flat)
        self.assertEqual(len(left.args), 3)
        self.assertEqual(canon(or_(or_(a, b), c)), canon(or_(c, b, a)))
        self.assertNotEqual(canon(and_(a, b)), canon(or_(a, b)))  # AND and OR are never conflated

    def test_inverse_and_symmetric_relations(self):
        pp, hp = relate("PROPER_PART_OF", R(1), R(2)), relate("HAS_PART", R(2), R(1))
        self.assertEqual(canon(pp), canon(hp))  # one canonical direction (SG-CAN-023)
        self.assertEqual(canon(pp).get("relation"), "HAS_PART")  # alphabetically first of the pair
        d1, d2 = relate("DISJOINT_WITH", R(1), R(2)), relate("DISJOINT_WITH", R(2), R(1))
        self.assertEqual(canon(d1), canon(d2))
        self.assertEqual(canon(same_as(R(2), R(1))), canon(same_as(R(1), R(2))))
        self.assertEqual(canon(different_from(R(2), R(1))), canon(different_from(R(1), R(2))))
        # a relation that is neither symmetric nor has an inverse keeps its direction
        self.assertNotEqual(canon(relate("HAS_FUNCTION", R(1), R(2))), canon(relate("HAS_FUNCTION", R(2), R(1))))
        # without a relation catalogue nothing is rewritten
        self.assertEqual(canonicalize(pp).get("relation"), "PROPER_PART_OF")

    def test_time_normalization_adds_bounds_alongside(self):
        t = tense("PAST", time_rel("YESTERDAY"), holds(apply("OPEN", 1, {"UNDERGOER": R(1)})))
        c = canon(t, anchor=Anchor(document_date="2026-10-16"))
        tr = [n for _, n in walk(c) if n.op == "TIME_REL"][0]
        self.assertEqual((tr.get("expr"), tr.get("resolved_start")), ("YESTERDAY", "2026-10-15"))
        self.assertEqual(canon(t), t)  # no anchor: unchanged, nothing invented

    def test_variables_are_renamed_canonically(self):
        a = q("EXISTS", "x", red(var("x")), blue(var("x")))
        b = q("EXISTS", "foo", red(var("foo")), blue(var("foo")))
        self.assertEqual(canon(a), canon(b))
        self.assertEqual(canon(a).get("var"), "v0")

    def test_trace_records_every_applied_rule(self):
        t = CanonTrace()
        canon(and_(red(R(3)), red(R(1)), q("EXISTS", "foo", red(var("foo")), red(var("foo")))), trace=t)
        self.assertIn("SG-CAN-020", t.rules())
        self.assertIn("SG-CAN-021", t.rules())
        t2 = CanonTrace()
        canon(relate("PROPER_PART_OF", R(1), R(2)), trace=t2)
        self.assertEqual(t2.rules(), {"SG-CAN-023"})
        self.assertTrue(t2.rules() <= set(CANON_RULES))
        already = canon(and_(red(R(1)), red(R(2))))
        t3 = CanonTrace()
        canon(already, trace=t3)
        self.assertEqual(t3.entries, [])  # a canonical expression applies nothing

    def test_annotations_are_carried_through(self):
        a = holds(apply("OPEN", 1, {"UNDERGOER": R(1).with_ann(Ann(spans=((0, 3),), rules=("SG-INT-010",)))}))
        c = canon(a)
        self.assertEqual(c, a)
        self.assertEqual([n.ann.spans for _, n in walk(c) if n.op == "REF"], [((0, 3),)])
        self.assertEqual(structural_hash(c), structural_hash(a))


class ForbiddenSimplificationTests(unittest.TestCase):
    """SG-CAN-002: canonicalization must never discard natural-language meaning."""

    def test_double_negation_is_kept(self):
        p = red(R(1))
        self.assertEqual(canon(not_(not_(p))), not_(not_(p)))
        self.assertNotEqual(canon(not_(not_(p))), canon(p))  # "not uncommon" != "common"

    def test_quantifier_is_not_moved_across_negation(self):
        a = not_(q("FORALL", "x", red(var("x")), blue(var("x"))))  # not every
        b = q("EXISTS", "x", red(var("x")), not_(blue(var("x"))))  # some are not
        self.assertNotEqual(canon(a), canon(b))
        self.assertEqual(canon(a).op, "NOT")
        self.assertEqual(canon(a).args[0].get("quant"), "FORALL")

    def test_duplicates_are_not_removed(self):
        p = red(R(1))
        self.assertEqual(len(canon(and_(p, p)).args), 2)
        self.assertEqual(len(canon(or_(p, p, p)).args), 3)

    def test_offer_never_becomes_give_and_modality_tense_survive(self):
        offer = holds(apply("OFFER", 1, {"OFFERER": R(1), "OFFEREE": R(2), "CONTENT": apply("GIVE", 1, {"AGENT": R(1)})}))
        give = holds(apply("GIVE", 1, {"AGENT": R(1), "SOURCE": R(1), "RECIPIENT": R(2), "THEME": R(3)}))
        self.assertNotEqual(canon(offer), canon(give))
        self.assertEqual(canon(offer).args[0].get("frame"), "OFFER")
        m = modal("POSSIBILITY", "EPISTEMIC", tense("FUTURE", speech_time(), give))
        c = canon(m)
        self.assertEqual({n.op for _, n in walk(c)} >= {"MODAL", "TENSE"}, True)
        self.assertEqual(c.get("flavor"), "EPISTEMIC")

    def test_negation_scope_ambiguity_is_not_resolved_by_normalisation(self):
        every = q("FORALL", "x", red(var("x")), blue(var("x")))
        self.assertNotEqual(canon(not_(every)), canon(q("FORALL", "x", red(var("x")), not_(blue(var("x"))))))


class PropertyTests(unittest.TestCase):
    N = 300

    def setUp(self):
        self.tc = Typechecker(FND.frames, REL)

    def cases(self):
        rng = random.Random(20261020)
        for _ in range(self.N):
            yield assert_(gen(rng, 4)), rng

    def test_idempotent(self):
        for e, _ in self.cases():
            c = canon(e)
            self.assertEqual(canon(c), c)
            self.assertEqual(canonical_string(canon(c)), canonical_string(c))

    def test_invariant_under_reordering_and_renaming(self):
        for e, rng in self.cases():
            noisy = rename_bound(shuffle_tree(e, rng), rng)
            self.assertEqual(canonical_string(canon(noisy)), canonical_string(canon(e)))

    def test_validity_is_preserved(self):
        for e, _ in self.cases():
            before = self.tc.check(e)
            after = self.tc.check(canon(e))
            self.assertEqual(before.codes(), after.codes(), str(e))
            self.assertEqual(before.codes(), [], str(e))  # the generator produces valid expressions

    def test_json_roundtrip_of_canonical_forms(self):
        for e, _ in self.cases():
            c = canon(e)
            self.assertEqual(node_from_json(node_to_json(c)), c)

    def test_free_variables_never_appear(self):
        for e, _ in self.cases():
            self.assertEqual(check_scope(canon(e)), [])


class OpaqueContextTests(unittest.TestCase):
    def test_substitution_skips_attitude_content(self):
        inside = holds(apply("OPEN", 1, {"UNDERGOER": R(1)}))
        believe = holds(apply("BELIEVE", 1, {"EXPERIENCER": R(2), "CONTENT": inside}))
        outside = holds(apply("OPEN", 1, {"UNDERGOER": R(1)}))
        both = and_(believe, outside)
        out = substitute_referent(both, "REFERENT:1", "REFERENT:9", FND.frames)
        refs = [n.get("ref") for _, n in walk(out) if n.op == "REF"]
        self.assertIn("REFERENT:9", refs)  # replaced in the author's context
        content = [n for _, n in walk(out) if n.op == "APPLY" and n.get("frame") == "BELIEVE"][0].args
        self.assertEqual([n.get("ref") for _, n in walk(content[0]) if n.op == "REF"], ["REFERENT:1"])  # untouched inside (roles sort: CONTENT first)

    def test_attribute_holder_is_substituted_but_content_is_not(self):
        n = attribute(R(1), "REPORT", holds(apply("OPEN", 1, {"UNDERGOER": R(1)})))
        out = substitute_referent(n, "REFERENT:1", "REFERENT:9")
        self.assertEqual(out.args[0].get("ref"), "REFERENT:9")
        self.assertEqual([x.get("ref") for _, x in walk(out.args[1]) if x.op == "REF"], ["REFERENT:1"])

    def test_wanted_situation_is_opaque_too(self):
        want = holds(apply("WANT", 1, {"EXPERIENCER": R(1), "CONTENT": apply("EAT", 1, {"EATER": R(1), "FOOD": R(5)})}))
        out = substitute_referent(want, "REFERENT:1", "REFERENT:9", FND.frames)
        refs = {r: [x.get("ref") for _, x in walk(f) if x.op == "REF"] for r, _, f in
                __import__("usg.grammar.node", fromlist=["role_entries"]).role_entries(out.args[0])}
        self.assertEqual(refs["EXPERIENCER"], ["REFERENT:9"])
        self.assertEqual(refs["CONTENT"], ["REFERENT:1", "REFERENT:5"])

    def test_opaque_role_detection(self):
        self.assertTrue(is_opaque_role("BELIEVE", "CONTENT", FND.frames))
        self.assertTrue(is_opaque_role("ANY", "CONTENT", None))
        self.assertFalse(is_opaque_role("GIVE", "THEME", FND.frames))

    def test_substitution_is_total_outside_opaque_positions(self):
        n = and_(holds(apply("OPEN", 1, {"UNDERGOER": R(1)})), red(R(1)), relate("HAS_PART", R(1), R(2)))
        out = substitute_referent(n, "REFERENT:1", "REFERENT:7", FND.frames)
        self.assertNotIn("REFERENT:1", [x.get("ref") for _, x in walk(out) if x.op == "REF"])


if __name__ == "__main__":
    unittest.main()
