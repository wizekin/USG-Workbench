import unittest

from usg.core.kinds import SemKind as K
from usg.errors import InvariantViolation
from usg.foundation.relations import RELATIONS
from usg.model.relations import RelationCategory as C
from usg.model.relations import RelationDef, check_edge, reaches
from usg.ontology import Compat, ConceptSeed as S, Ontology


def small():
    return Ontology().add_all([
        S("Entity", K.ENTITY),
        S("Physical", K.ENTITY, ("Entity",), disjoint_with=("Abstract",)),
        S("Abstract", K.ENTITY, ("Entity",)),
        S("Animal", K.ENTITY, ("Physical",)),
        S("Dog", K.ENTITY, ("Animal",)),
        S("Idea", K.ENTITY, ("Abstract",)),
        S("Color", K.PROPERTY, value_domain="ColorValue"),
        S("ColorValue", K.VALUE),
        S("Red", K.VALUE, ("ColorValue",)),
        S("Loud", K.VALUE),
    ])


class OntologyTests(unittest.TestCase):
    def test_closure_and_subclass(self):
        o = small()
        self.assertEqual(o.ancestors("Dog"), {"Animal", "Physical", "Entity"})
        self.assertTrue(o.is_subclass("Dog", "Entity"))
        self.assertTrue(o.is_subclass("Dog", "Dog"))
        self.assertFalse(o.is_subclass("Entity", "Dog"))
        self.assertEqual(o.descendants("Animal"), {"Dog"})
        self.assertEqual(set(o.children_of("Entity")), {"Physical", "Abstract"})

    def test_disjointness_is_inherited_and_symmetric(self):
        o = small()
        self.assertTrue(o.disjoint("Dog", "Idea"))
        self.assertTrue(o.disjoint("Idea", "Dog"))
        self.assertFalse(o.disjoint("Dog", "Animal"))
        self.assertFalse(o.disjoint("Animal", "Entity"))

    def test_three_valued_compatibility(self):
        o = small()
        self.assertEqual(o.classes_compatible(["Dog"], "Animal"), Compat.COMPATIBLE)
        self.assertEqual(o.classes_compatible(["Idea"], "Animal"), Compat.INCOMPATIBLE)
        # open world: no class information is never incompatibility
        self.assertEqual(o.classes_compatible([], "Animal"), Compat.UNDETERMINED)
        self.assertEqual(o.classes_compatible(["Unknown"], "Animal"), Compat.UNDETERMINED)
        # related but neither derivable nor refutable
        self.assertEqual(o.classes_compatible(["Physical"], "Animal"), Compat.UNDETERMINED)
        # one compatible class is enough; a mix of incompatible and unrefuted is undetermined
        self.assertEqual(o.classes_compatible(["Idea", "Dog"], "Animal"), Compat.COMPATIBLE)
        self.assertEqual(o.classes_compatible(["Idea", "Physical"], "Animal"), Compat.UNDETERMINED)

    def test_value_domain(self):
        o = small()
        self.assertTrue(o.value_in_domain("Color", "Red"))
        self.assertFalse(o.value_in_domain("Color", "Loud"))

    def test_validation_finds_structural_problems(self):
        o = Ontology().add_all([S("A", K.ENTITY, ("Missing",)), S("B", K.VALUE, ("A",))])
        codes = {c for c, _ in o.validate()}
        self.assertIn("I-02", codes)  # unknown parent
        self.assertIn("SG-KNW-005", codes)  # parent of a different kind
        with self.assertRaises(InvariantViolation):
            o.assert_valid()

    def test_unsatisfiable_concept_detected(self):
        o = small()
        o.add(S("Ghost", K.ENTITY, ("Animal", "Idea")))  # inherits from disjoint Physical and Abstract
        msgs = [m for c, m in o.validate() if c == "SG-KNW-005"]
        self.assertTrue(any("Ghost" in m for m in msgs))

    def test_cycle_detected_and_duplicates_rejected(self):
        o = Ontology().add_all([S("A", K.ENTITY, ("B",)), S("B", K.ENTITY, ("A",))])
        self.assertTrue(any(c == "VC-G01" for c, _ in o.validate()))
        with self.assertRaises(InvariantViolation):
            o.add(S("A", K.ENTITY))
        with self.assertRaises(KeyError):
            o.ancestors("Nope")


class RelationTests(unittest.TestCase):
    def test_declaration_consistency(self):
        for kw in (dict(symmetric=True, asymmetric=True), dict(reflexive=True, irreflexive=True),
                   dict(asymmetric=True, reflexive=True), dict(asymmetric=True, cycles_allowed=True),
                   dict(transitive=True, irreflexive=True, cycles_allowed=True)):
            with self.assertRaises(InvariantViolation):
                RelationDef("X", C.LOGICAL, **kw)
        with self.assertRaises(InvariantViolation):
            RelationDef("X", C.LOGICAL, defeasible=True)  # defeasible implies not LOGICAL
        RelationDef("X", C.EPISTEMIC, defeasible=True)

    def test_only_associative_relations_carry_weights(self):
        self.assertTrue(RelationDef("A", C.ASSOCIATIVE).weights_allowed)
        self.assertFalse(RelationDef("A", C.LOGICAL).weights_allowed)
        self.assertFalse(RelationDef("A", C.EPISTEMIC).weights_allowed)
        err = check_edge(RelationDef("L", C.LOGICAL), 1, 2, {}, weight=0.7)
        self.assertEqual(err[0], "SG-KNW-002")
        self.assertIsNone(check_edge(RelationDef("A", C.ASSOCIATIVE), 1, 2, {}, weight=0.7))

    def test_edge_checks(self):
        strict = RelationDef("PART", C.LOGICAL, irreflexive=True, asymmetric=True, transitive=True)
        self.assertEqual(check_edge(strict, 1, 1, {})[0], "VC-G02")
        self.assertEqual(check_edge(strict, 2, 1, {1: {2}})[0], "VC-G02")  # reverse edge exists
        self.assertEqual(check_edge(strict, 3, 1, {1: {2}, 2: {3}})[0], "VC-G01")  # closes a longer cycle
        self.assertIsNone(check_edge(strict, 1, 3, {1: {2}, 2: {3}}))  # redundant but acyclic: allowed
        social = RelationDef("KNOWS", C.LOGICAL, cycles_allowed=True)
        self.assertIsNone(check_edge(social, 2, 1, {1: {2}}))

    def test_reaches(self):
        adj = {1: {2}, 2: {3}, 4: {1}}
        self.assertTrue(reaches(adj, 4, 3))
        self.assertFalse(reaches(adj, 3, 4))

    def test_json_roundtrip_and_catalogue(self):
        names = [r.name for r in RELATIONS]
        self.assertEqual(len(names), len(set(names)))
        for r in RELATIONS:
            self.assertEqual(RelationDef.from_json(r.to_json()), r)
        by = {r.name: r for r in RELATIONS}
        self.assertTrue(by["KNOWS"].cycles_allowed)  # a valid social cycle
        self.assertFalse(by["PROPER_PART_OF"].cycles_allowed)
        self.assertEqual(by["ASSOCIATED_WITH"].category, C.ASSOCIATIVE)
        self.assertTrue(by["TYPICALLY_HAS"].defeasible)
        for r in RELATIONS:
            for ref in (r.inverse_of, r.sub_relation_of):
                if ref:
                    self.assertIn(ref, by)


if __name__ == "__main__":
    unittest.main()
