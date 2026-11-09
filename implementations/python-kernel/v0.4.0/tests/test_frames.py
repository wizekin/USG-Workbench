import unittest

from usg.core.ids import IdSpace, Ref
from usg.core.kinds import SemKind as K
from usg.core.records import Filler, RoleBinding
from usg.core.spans import Span
from usg.core.values import Basis, ValueState
from usg.errors import InvariantViolation
from usg.model.frames import (Authority, CompKind, ComponentSpec, ControlHint, ControlKind, FrameDef, FrameLibrary,
                              FrameTests, LinkKind, ParamDecl, ParentLink, Perspective, Presupposition, RoleDecl,
                              SituationKind, StatePattern)
from usg.ontology import ConceptSeed as S, Ontology

G, D = Authority.GRAMMAR, Authority.DOMAIN
OK = FrameTests(("v",), ("i",), ("x",), (("a", "b"),))


def onto():
    return Ontology().add_all([
        S("Entity", K.ENTITY),
        S("Physical", K.ENTITY, ("Entity",), disjoint_with=("Abstract",)),
        S("Abstract", K.ENTITY, ("Entity",)),
        S("Animal", K.ENTITY, ("Physical",)),
        S("Person", K.ENTITY, ("Animal",)),
        S("Idea", K.ENTITY, ("Abstract",)),
        S("Place", K.ENTITY, ("Physical",)),
        S("Color", K.PROPERTY), S("Red", K.VALUE), S("Sad", K.STATE),
    ])


def t1(n, req=False, kind=K.ENTITY, cls=None, card=1):
    return RoleDecl(n, 1, None, kind, cls, req, card)


def t2(n, parent, req=False, kind=K.ENTITY, cls=None, card=1):
    return RoleDecl(n, 2, parent, kind, cls, req, card)


def F(name, layer=1, tests=OK, **kw):
    return FrameDef(name, layer, G if layer <= 2 else D, tests=tests, **kw)


def spec(p, **m):
    return (ParentLink(p, LinkKind.SPECIALIZES, tuple(m.items())),)


def lib(*frames, tests=True):
    return FrameLibrary(onto(), require_tests=tests).add_all(frames)


def codes(*frames, tests=True):
    return [i.code for i in lib(*frames, tests=tests).build()]


def rb(role, n=1, st=ValueState.SPECIFIED):
    if st is ValueState.SPECIFIED:
        return RoleBinding(role, st, Basis.EXPLICIT, Filler.referent(Ref(IdSpace.REFERENT, n)), span=Span(0, 1))
    return RoleBinding(role, st)


class ResolutionTests(unittest.TestCase):
    def test_inherited_roles_first_then_own_and_stable_indexes(self):
        L = lib(F("P", roles=(t1("AGENT", True), t1("THEME"))),
                F("C", parents=spec("P"), roles=(t1("GOAL"), t1("THEME", True)))).finalize()
        p, c = L.resolved("P"), L.resolved("C")
        self.assertEqual(p.role_names(), ("AGENT", "THEME"))
        self.assertEqual(c.role_names(), ("AGENT", "THEME", "GOAL"))  # append-only order (SG-FRM-006)
        self.assertEqual([r.index for r in c.roles], [0, 1, 2])
        self.assertTrue(c.role("THEME").required)  # strengthened OPTIONAL -> REQUIRED is allowed
        self.assertEqual(c.role("AGENT").origin, "P")
        self.assertTrue(L.is_specialization_of("C", "P"))
        self.assertFalse(L.is_specialization_of("P", "C"))

    def test_narrowing_rules(self):
        base = F("P", roles=(t1("AGENT", True, cls="Animal"), t1("THEME", card=2)))
        ok = lib(base, F("C", parents=spec("P"), roles=(t1("AGENT", True, cls="Person"),))).finalize()
        self.assertEqual(ok.resolved("C").role("AGENT").cls, "Person")
        self.assertEqual(ok.resolved("C").role("THEME").spec.card_max, 2)  # unmentioned roles inherited unchanged
        bad = {
            "class widened": F("C", parents=spec("P"), roles=(t1("AGENT", True, cls="Entity"),)),
            "required weakened": F("C", parents=spec("P"), roles=(t1("AGENT", False, cls="Person"),)),
            "kind changed": F("C", parents=spec("P"), roles=(t1("AGENT", True, kind=K.EVENT, cls="Person"),)),
            "cardinality widened": F("C", parents=spec("P"), roles=(t1("THEME", card=3),)),
        }
        for label, child in bad.items():
            self.assertIn("SG-FRM-003", codes(base, child), label)

    def test_class_inherited_when_child_omits_it(self):
        L = lib(F("P", roles=(t1("AGENT", True, cls="Animal"),)),
                F("C", parents=spec("P"), roles=(t1("AGENT", True),))).finalize()
        self.assertEqual(L.resolved("C").role("AGENT").cls, "Animal")

    def test_multi_parent_conjunction(self):
        a = F("A", roles=(t1("AGENT", False, cls="Animal"),))
        b = F("B", roles=(t1("AGENT", True, cls="Person"),))
        L = lib(a, b, F("C", parents=spec("A") + spec("B"))).finalize()
        r = L.resolved("C").role("AGENT")
        self.assertEqual(r.cls, "Person")  # more specific class wins
        self.assertTrue(r.required)  # REQUIRED if either parent requires it
        self.assertEqual(L.resolved("C").specializes, ("A", "B"))
        a2 = F("A2", roles=(t1("AGENT", cls="Animal"),))
        b2 = F("B2", roles=(t1("AGENT", cls="Idea"),))
        self.assertIn("SG-FRM-004", codes(a2, b2, F("C2", parents=spec("A2") + spec("B2"))))  # empty conjunction
        a3 = F("A3", roles=(t1("AGENT", cls="Person"),))
        b3 = F("B3", roles=(t1("AGENT", cls="Place"),))
        self.assertIn("SG-FRM-004", codes(a3, b3, F("C3", parents=spec("A3") + spec("B3"))))  # unrelated: child must narrow

    def test_parameters_and_pins(self):
        base = F("P", roles=(t1("AGENT"),), params=(ParamDecl("DIM", ("X", "Y")), ParamDecl("PROP", concept_kind=K.PROPERTY)))
        good = F("C", parents=spec("P"), pins=(("DIM", "X"), ("PROP", "Color")))
        L = lib(base, good).finalize()
        self.assertEqual(dict(L.resolved("C").pins), {"DIM": "X", "PROP": "Color"})
        self.assertIn("SG-FRM-002", codes(base, F("C", parents=spec("P"), pins=(("DIM", "Z"),))))  # not allowed
        self.assertIn("SG-FRM-002", codes(base, F("C", parents=spec("P"), pins=(("NOPE", "X"),))))  # undeclared
        self.assertIn("SG-FRM-002", codes(base, F("C", parents=spec("P"), pins=(("PROP", "Red"),))))  # wrong concept kind
        self.assertIn("SG-FRM-002", codes(base, F("C", parents=spec("P"), pins=(("DIM", "X"),)),
                                          F("D", parents=spec("C"), pins=(("DIM", "Y"),))))  # re-pin inherited

    def test_layer_discipline_and_authority(self):
        self.assertIn("SG-FRM-010", codes(F("P", layer=2, roles=(t1("AGENT"),)), F("C", layer=1, parents=spec("P"))))
        self.assertIn("SG-FRM-010", codes(FrameDef("X", 3, G, tests=OK)))  # layer 3 must be DOMAIN
        self.assertIn("SG-FRM-010", codes(FrameDef("X", 1, D, tests=OK)))
        self.assertIn("SG-FRM-010", codes(FrameDef("X", 4, G, tests=OK)))  # layer 4 never defines a frame
        self.assertEqual(codes(F("P", layer=1), F("C", layer=2, parents=spec("P")), F("E", layer=3, parents=spec("C"))), [])

    def test_structural_link_shares_structure_not_entailments(self):
        base = F("COMBINE", roles=(t1("THEME", True), t1("GOAL")))
        child = F("FUSE", roles=(t2("PARTS", "THEME", True), t2("RESULT", "GOAL")),
                  parents=(ParentLink("COMBINE", LinkKind.STRUCTURAL_INSTANCE_OF, (("PARTS", "THEME"), ("RESULT", "GOAL"))),))
        L = lib(base, child).finalize()
        self.assertEqual(L.resolved("FUSE").role_names(), ("PARTS", "RESULT"))  # no role inheritance
        self.assertEqual(L.resolved("FUSE").structural, ("COMBINE",))
        self.assertFalse(L.is_specialization_of("FUSE", "COMBINE"))
        badmap = F("FUSE", roles=(t2("PARTS", "THEME", True),),
                   parents=(ParentLink("COMBINE", LinkKind.STRUCTURAL_INSTANCE_OF, (("PARTS", "MISSING"),)),))
        self.assertIn("SG-FRM-003", codes(base, badmap))

    def test_tests_are_mandatory(self):
        self.assertIn("SG-FRM-008", codes(F("P", tests=FrameTests(("v",), (), ("x",), ()))))
        self.assertEqual(codes(F("P", tests=FrameTests()), tests=False), [])

    def test_structural_errors(self):
        self.assertIn("VC-G01", codes(F("A", parents=spec("B")), F("B", parents=spec("A"))))
        self.assertIn("I-02", codes(F("A", parents=spec("Nope"))))
        self.assertIn("I-02", codes(F("A", roles=(t1("AGENT", cls="NoSuchClass"),))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),), perspectives=(Perspective("P", "MISSING"),))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),), disjoint_roles=(("AGENT", "MISSING"),))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),), presuppositions=(Presupposition("CONTENT"),))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),),
                                            control=ControlHint(ControlKind.SUBJECT_CONTROL, "AGENT", "CONTENT"))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),), final=(StatePattern("P", ("AGENT", "NOPE")),))))
        self.assertIn("SG-FRM-001", codes(F("A", roles=(t1("AGENT"),), final=(StatePattern("P", ("AGENT", "param:NOPE")),))))
        self.assertIn("I-02", codes(F("A", roles=(t1("AGENT"),), final=(StatePattern("P", ("AGENT", "value:Nope")),))))
        cyc = (ComponentSpec("B", (("AGENT", "AGENT"),), CompKind.SEQUENCE),)
        self.assertIn("VC-G01", codes(F("A", roles=(t1("AGENT"),), components=cyc),
                                      F("B", roles=(t1("AGENT"),), components=(ComponentSpec("A", (("AGENT", "AGENT"),)),))))
        with self.assertRaises(InvariantViolation) as cm:
            lib(F("A", parents=spec("Nope"))).finalize()
        self.assertEqual(cm.exception.code, "I-02")
        with self.assertRaises(InvariantViolation):
            lib(F("A")).add(F("A"))

    def test_role_decl_validation_reuses_role_rules(self):
        for args in ((2, None), (2, "NOT_A_ROLE")):
            with self.assertRaises(InvariantViolation):
                RoleDecl("X", *args)
        with self.assertRaises(InvariantViolation):
            RoleDecl("AGENT", 2, "AGENT")  # name collides with a tier-1 role


class BindingValidationTests(unittest.TestCase):
    def setUp(self):
        self.L = lib(
            F("ACT", roles=(t2("DOER", "AGENT", True), t2("DONE", "THEME", True, card=2), t1("LOCATION")),
              disjoint_roles=(("DOER", "DONE"),), params=(ParamDecl("MODE", ("A", "B")),)),
            F("ABS", abstract=True, roles=(t1("AGENT"),)),
        ).finalize()

    def vb(self, frame, *bs, **kw):
        return [(i.code, i.role) for i in self.L.validate_bindings(frame, bs, **kw)]

    def test_valid_instance(self):
        self.assertEqual(self.vb("ACT", rb("DOER", 1), rb("DONE", 2)), [])
        # holes satisfy REQUIRED roles but must be explicit
        self.assertEqual(self.vb("ACT", rb("DOER", st=ValueState.UNSPECIFIED), rb("DONE", st=ValueState.UNKNOWN)), [])

    def test_missing_required_role(self):
        self.assertEqual(self.vb("ACT", rb("DOER", 1)), [("VC-S07", "DONE")])

    def test_unknown_frame_abstract_and_parameters(self):
        self.assertEqual(self.vb("NOPE")[0][0], "VC-S05")
        self.assertEqual(self.vb("ABS")[0][0], "VC-S05")
        self.assertEqual(self.vb("ABS", allow_abstract=True), [])
        self.assertIn(("SG-FRM-002", "MODE"), self.vb("ACT", rb("DOER", 1), rb("DONE", 2), rb("MODE", 3)))  # instances never set params

    def test_closed_role_list_with_tier1_hint(self):
        out = self.L.validate_bindings("ACT", [rb("AGENT", 1), rb("DONE", 2)])
        issue = [i for i in out if i.code == "VC-S06"][0]
        self.assertIn("DOER", issue.message)  # points to the frame-specific role (E-45)
        self.assertIn("specialization of AGENT", issue.message)
        out = self.L.validate_bindings("ACT", [rb("DOER", 1), rb("DONE", 2), rb("NOPE", 3)])
        self.assertEqual([i.code for i in out], ["VC-S06"])

    def test_cardinality(self):
        two = [rb("DOER", 1), RoleBinding("DONE", ValueState.SPECIFIED, Basis.EXPLICIT, Filler.referent(Ref(IdSpace.REFERENT, 2)), Span(0, 1), ord=0),
               RoleBinding("DONE", ValueState.SPECIFIED, Basis.EXPLICIT, Filler.referent(Ref(IdSpace.REFERENT, 3)), Span(0, 1), ord=1)]
        self.assertEqual([i.code for i in self.L.validate_bindings("ACT", two)], [])
        three = two + [RoleBinding("DONE", ValueState.SPECIFIED, Basis.EXPLICIT, Filler.referent(Ref(IdSpace.REFERENT, 4)), Span(0, 1), ord=2)]
        self.assertEqual([i.code for i in self.L.validate_bindings("ACT", three)], ["VC-S08"])

    def test_disjoint_roles_cannot_share_a_referent(self):
        self.assertEqual(self.vb("ACT", rb("DOER", 7), rb("DONE", 7)), [("VC-T06", "DOER")])
        self.assertEqual(self.vb("ACT", rb("DOER", 7), rb("DONE", 8)), [])


class ProjectionAndVersionTests(unittest.TestCase):
    def test_projection_through_specialization(self):
        L = lib(F("P", roles=(t1("AGENT", True), t1("THEME", True))),
                F("C", parents=spec("P"), roles=(t1("GOAL"),))).finalize()
        child_binds = [rb("AGENT", 1), rb("THEME", 2), rb("GOAL", 3)]
        self.assertEqual(L.validate_bindings("C", child_binds), [])
        proj = L.project_bindings("C", "P", child_binds)
        self.assertEqual([b.role for b in proj], ["AGENT", "THEME"])  # extra role dropped
        self.assertEqual(L.validate_bindings("P", proj), [])  # projection test (SG-FRM-003)
        with self.assertRaises(InvariantViolation):
            L.project_bindings("P", "C", child_binds)

    def test_projection_follows_role_renames(self):
        L = lib(F("P", roles=(t1("AGENT", True),)),
                F("C", parents=(ParentLink("P", LinkKind.SPECIALIZES, (("DOER", "AGENT"),)),))).finalize()
        self.assertEqual(L.resolved("C").role_names(), ("DOER",))
        self.assertEqual(L.resolved("C").role("DOER").spec.parent_role, "AGENT")  # renamed tier-1 becomes tier-2 under it
        proj = L.project_bindings("C", "P", [rb("DOER", 1)])
        self.assertEqual([b.role for b in proj], ["AGENT"])

    def test_append_only_versions(self):
        v1 = lib(F("P", roles=(t1("AGENT"), t1("THEME")))).finalize()
        ok = lib(F("P", roles=(t1("AGENT"), t1("THEME"), t1("GOAL")))).finalize()
        moved = lib(F("P", roles=(t1("THEME"), t1("AGENT")))).finalize()
        removed = lib(F("P", roles=(t1("AGENT"),))).finalize()
        self.assertEqual(v1.check_append_only(v1.resolved("P"), ok.resolved("P")), [])
        self.assertTrue(v1.check_append_only(v1.resolved("P"), moved.resolved("P")))
        self.assertEqual(v1.check_append_only(v1.resolved("P"), removed.resolved("P"))[0].code, "SG-FRM-006")

    def test_json_roundtrip_and_hash(self):
        f = F("X", roles=(t1("AGENT", True, cls="Animal"), t2("D", "THEME", kind=K.EVENT)), params=(ParamDecl("M", ("A",)),),
              pins=(), perspectives=(Perspective("V", "AGENT", ("h",)),), final=(StatePattern("P", ("AGENT", "param:M")),),
              control=ControlHint(ControlKind.SUBJECT_CONTROL, "AGENT", "D"), presuppositions=(Presupposition("D"),),
              components=(ComponentSpec("Y", (("AGENT", "AGENT"),)),), role_functions=(("AGENT", "Fn"),), doc="d")
        self.assertEqual(FrameDef.from_json(f.to_json()), f)
        self.assertEqual(f.content_hash(), FrameDef.from_json(f.to_json()).content_hash())
        import dataclasses
        self.assertNotEqual(f.content_hash(), dataclasses.replace(f, doc="changed").content_hash())

    def test_topo_order_puts_parents_first(self):
        L = lib(F("C", parents=spec("B")), F("B", parents=spec("A")), F("A")).finalize()
        order = L.topo_order()
        self.assertTrue(order.index("A") < order.index("B") < order.index("C"))


if __name__ == "__main__":
    unittest.main()
