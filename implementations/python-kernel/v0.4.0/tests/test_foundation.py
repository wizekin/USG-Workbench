import unittest

from usg.core.ids import IdSpace, Ref
from usg.core.records import Filler, RoleBinding
from usg.core.spans import Span
from usg.core.values import Basis, ValueState
from usg.foundation.builder import build_foundation
from usg.foundation.frames import SPEC_KERNEL_20
from usg.foundation.functions import FN_DERIVED, FN_PRIMITIVES, FUNCTIONS
from usg.model.frames import ConsequenceKind
from usg.ontology import Compat

F = build_foundation()
L = F.frames
O = F.ontology


def rb(role, n=1, st=ValueState.SPECIFIED):
    if st is ValueState.SPECIFIED:
        return RoleBinding(role, st, Basis.EXPLICIT, Filler.referent(Ref(IdSpace.REFERENT, n)), span=Span(0, 1))
    return RoleBinding(role, st)


class PackageShapeTests(unittest.TestCase):
    def test_all_specification_kernel_frames_exist_and_are_marked(self):
        for n in SPEC_KERNEL_20:
            self.assertTrue(L.has(n), n)
            self.assertTrue(L.get(n).kernel, n)
        self.assertGreaterEqual(len(L.kernel_frames()), 20)
        self.assertEqual(set(L.kernel_frames()) - set(SPEC_KERNEL_20), {"OPEN", "SEE", "ALLERGIC", "OWNERSHIP_TRANSFER"})

    def test_every_frame_has_the_four_test_groups(self):
        for n in L.names():
            self.assertTrue(L.get(n).tests.complete(), n)

    def test_layers_and_authority(self):
        for n in L.names():
            f = L.get(n)
            self.assertIn(f.layer, (1, 2, 3))
            self.assertEqual(f.authority.value, "GRAMMAR" if f.layer <= 2 else "DOMAIN", n)
        self.assertEqual(L.get("BLOOD_CIRCULATION").layer, 3)

    def test_function_ontology(self):
        self.assertEqual(len(FN_PRIMITIVES), 6)
        self.assertEqual(set(FN_DERIVED), {"FN.PROCESS_INFORMATION", "FN.REGULATE"})
        for fn in FUNCTIONS:
            self.assertEqual(O.kind_of(fn.name).value, "FUNCTION")
        reg = next(f for f in FUNCTIONS if f.name == "FN.REGULATE")
        self.assertTrue(reg.derived)
        self.assertEqual(set(reg.composed_of), {"FN.DETECT", "FN.DECIDE", "FN.ACT"})
        self.assertTrue(O.is_subclass("FN.DRIVE_FLUID_FLOW", "FN.TRANSPORT"))
        # a pump DRIVES flow, a pipe CONDUCTS it: sub-functions are distinct siblings
        self.assertFalse(O.is_subclass("FN.CONDUCT_FLUID", "FN.DRIVE_FLUID_FLOW"))

    def test_edges_reference_known_things(self):
        rels = set(F.relations)
        for e in F.edges:
            self.assertIn(e.relation, rels)
            self.assertTrue(O.has(e.src) and O.has(e.tgt))
        fn_edges = [e for e in F.edges if e.relation == "HAS_FUNCTION"]
        self.assertIn(("Heart", "FN.DRIVE_FLUID_FLOW"), {(e.src, e.tgt) for e in fn_edges})
        self.assertFalse(O.is_subclass("Heart", "Pump"))  # a shared function never implies a shared class (SG-FRM-005)

    def test_hash_is_deterministic(self):
        self.assertEqual(build_foundation().content_hash(), F.content_hash())


class FrameSemanticsTests(unittest.TestCase):
    def test_give_resolution_and_order(self):
        r = L.resolved("GIVE")
        self.assertEqual(r.role_names(), ("AGENT", "SOURCE", "RECIPIENT", "THEME", "TIME"))
        self.assertTrue(all(r.role(n).required for n in ("AGENT", "SOURCE", "RECIPIENT", "THEME")))
        self.assertEqual(dict(r.pins), {"DIMENSION": "POSSESSION"})
        self.assertTrue(L.is_specialization_of("GIVE", "TRANSFER"))
        self.assertTrue(L.get("TRANSFER").abstract)

    def test_the_giver_may_fill_agent_and_source(self):
        b = [rb("AGENT", 1), rb("SOURCE", 1), rb("RECIPIENT", 2), rb("THEME", 3)]
        self.assertEqual(L.validate_bindings("GIVE", b), [])

    def test_agentless_passive_leaves_holes_not_inventions(self):
        b = [rb("AGENT", st=ValueState.UNSPECIFIED), rb("SOURCE", st=ValueState.UNSPECIFIED), rb("RECIPIENT", 2), rb("THEME", 3)]
        self.assertEqual(L.validate_bindings("GIVE", b), [])
        self.assertEqual([i.code for i in L.validate_bindings("GIVE", [rb("RECIPIENT", 2), rb("THEME", 3)])], ["VC-S07", "VC-S07"])

    def test_give_projects_to_transfer(self):
        b = [rb("AGENT", 1), rb("SOURCE", 1), rb("RECIPIENT", 2), rb("THEME", 3)]
        proj = L.project_bindings("GIVE", "TRANSFER", b)
        self.assertEqual(L.validate_bindings("TRANSFER", proj, allow_abstract=True), [])
        self.assertEqual([i.code for i in L.validate_bindings("TRANSFER", proj)], ["VC-S05"])  # abstract

    def test_tier1_roles_cannot_bypass_frame_specific_roles(self):
        out = L.validate_bindings("TREAT", [rb("AGENT", 1), rb("UNDERGOER", 2), rb("INSTRUMENT", 3)])
        msgs = " | ".join(i.message for i in out)
        self.assertIn("PRACTITIONER", msgs)
        self.assertIn("INTERVENTION", msgs)
        self.assertEqual([i.code for i in out].count("VC-S06"), 3)
        self.assertEqual(L.validate_bindings("TREAT", [rb("PRACTITIONER", 1), rb("TREATED_ENTITY", 2)]), [])

    def test_parameters_are_never_set_by_instances(self):
        out = L.validate_bindings("SEE", [rb("EXPERIENCER", 1), rb("STIMULUS", 2), rb("MODALITY", 3)])
        self.assertEqual([i.code for i in out], ["SG-FRM-002"])
        self.assertEqual(dict(L.resolved("SEE").pins), {"MODALITY": "SIGHT"})

    def test_state_change_specializations_pin_the_dimension(self):
        self.assertEqual(dict(L.resolved("OPEN").pins), {"DIMENSION": "Openness", "DIRECTION": "INCREASE", "TARGET_VALUE": "OpenState"})
        self.assertEqual(dict(L.resolved("FREEZE").pins)["TARGET_VALUE"], "PhaseSolid")
        self.assertEqual(L.resolved("OPEN").role("UNDERGOER").cls, "Artifact")

    def test_commercial_transaction_is_composite_with_disjoint_parties(self):
        f = L.get("COMMERCIAL_TRANSACTION")
        self.assertEqual(len(f.components), 2)
        self.assertEqual({c.frame for c in f.components}, {"OWNERSHIP_TRANSFER"})
        self.assertIn(("BUYER", "SELLER"), f.disjoint_roles)
        same = [rb("BUYER", 1), rb("SELLER", 1), rb("GOODS", 2)]
        self.assertEqual([i.code for i in L.validate_bindings("COMMERCIAL_TRANSACTION", same)], ["VC-T06"])
        self.assertEqual({p.name for p in f.perspectives}, {"BUY", "SELL", "PAY", "COST"})

    def test_attitude_family_kinds_are_not_forced_into_one(self):
        self.assertEqual(L.resolved("ATTITUDE").role_names(), ("EXPERIENCER",))
        self.assertEqual(L.resolved("BELIEVE").role("CONTENT").spec.expected_kind.value, "PROPOSITION")
        self.assertEqual(L.resolved("WANT").role("CONTENT").spec.expected_kind.value, "EVENT")
        self.assertTrue(L.get("KNOW").presuppositions)  # factive
        self.assertFalse(L.get("BELIEVE").presuppositions)
        self.assertEqual(L.get("WANT").control.controller_role, "EXPERIENCER")

    def test_attempt_and_offer_are_not_completed_events(self):
        for n in ("ATTEMPT", "OFFER"):
            self.assertEqual(L.resolved(n).role("CONTENT").spec.expected_kind.value, "EVENT")
            self.assertFalse(L.get(n).consequences)  # no effect of the content is entailed
        self.assertFalse(L.is_specialization_of("OFFER", "GIVE"))
        self.assertFalse(L.is_specialization_of("OFFER", "TRANSFER"))

    def test_give_effects_distinguish_essential_from_typical(self):
        kinds = {(c.kind, c.strength.value) for c in L.get("GIVE").consequences}
        self.assertIn((ConsequenceKind.EFFECT, "ESSENTIAL"), kinds)
        self.assertIn((ConsequenceKind.TYPICAL_OUTCOME, "TYPICAL"), kinds)

    def test_move_has_perspectives_and_completed_view_semantics(self):
        f = L.get("MOVE")
        self.assertEqual({p.name for p in f.perspectives}, {"ARRIVE", "DEPART"})
        self.assertEqual(f.applies_when, "COMPLETED_VIEW")
        self.assertEqual(L.resolved("MOVE").role("MOVER").spec.parent_role, "THEME")

    def test_cross_domain_frames_narrow_by_class(self):
        self.assertEqual(L.resolved("TRANSPORT").role("TRANSPORTED_ENTITY").cls, "PhysicalEntity")
        self.assertEqual(L.resolved("FLUID_TRANSPORT").role("TRANSPORTED_ENTITY").cls, "Fluid")
        self.assertEqual(L.resolved("BLOOD_CIRCULATION").role("TRANSPORTED_ENTITY").cls, "Blood")
        self.assertTrue(L.is_specialization_of("BLOOD_CIRCULATION", "TRANSPORT"))
        # a fan moving air needs no conduit: CONDUIT must stay OPTIONAL
        self.assertFalse(L.resolved("FLUID_CIRCULATION_SYSTEM").role("CONDUIT").required)

    def test_every_concrete_frame_accepts_an_all_holes_instance_and_rejects_dropping_a_required_role(self):
        for n in L.names():
            rf = L.resolved(n)
            if rf.frame.abstract:
                continue
            holes = [rb(r.name, st=ValueState.UNSPECIFIED) for r in rf.roles if r.required]
            self.assertEqual(L.validate_bindings(n, holes), [], n)
            for dropped in [r for r in rf.roles if r.required]:
                partial = [b for b in holes if b.role != dropped.name]
                self.assertEqual([i.code for i in L.validate_bindings(n, partial)], ["VC-S07"], (n, dropped.name))


class SeedTypeCheckTests(unittest.TestCase):
    def test_three_valued_class_checks_for_benchmark_phenomena(self):
        cc = O.classes_compatible
        self.assertEqual(cc(["Argument"], "PhysicalEntity"), Compat.INCOMPATIBLE)  # "John bought the argument"
        self.assertEqual(cc(["Apple"], "EdibleEntity"), Compat.COMPATIBLE)
        self.assertEqual(cc(["Tablet"], "EdibleEntity"), Compat.UNDETERMINED)  # open world: neither derivable nor refutable
        self.assertEqual(cc(["Hospital"], "Location"), Compat.COMPATIBLE)  # multiple inheritance: place and institution
        self.assertEqual(cc(["Hospital"], "Organization"), Compat.COMPATIBLE)
        self.assertEqual(cc(["Hospital"], "Person"), Compat.INCOMPATIBLE)
        self.assertEqual(cc(["Pump"], "AnimateEntity"), Compat.INCOMPATIBLE)  # "a pump eats"
        self.assertEqual(cc(["Doctor"], "Person"), Compat.COMPATIBLE)
        self.assertEqual(cc(["Blood"], "Fluid"), Compat.COMPATIBLE)
        self.assertEqual(cc(["Liquid"], "Gas"), Compat.INCOMPATIBLE)

    def test_value_domains(self):
        self.assertTrue(O.value_in_domain("Color", "Red"))
        self.assertFalse(O.value_in_domain("Color", "Young"))
        self.assertTrue(O.disjoint("Red", "Blue"))
        self.assertTrue(O.disjoint("PhaseSolid", "PhaseGas"))


if __name__ == "__main__":
    unittest.main()
