"""Step 5B native-constructor and binder conformance tests."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from usg.core.kinds import Sort
from usg.errors import InvariantViolation
from usg.grammar.node import (
    Node, predicate_app, connective, quantifier, var, ref, holds, not_, opaque,
    unresolved_ref, inference_eligible, metadata_value, sort_of,
)
from usg.grammar.serialize import node_to_json, node_from_json, canonical_string
from usg.grammar.canon import canonicalize
from usg.grammar.scope import (
    free_variable_occurrences, check_native_scope, alpha_equivalent, substitute_free,
    free_vars, check_scope, alpha_rename,
)


def proposition(label):
    return Node("RELATE", (ref(label + "-a"), ref(label + "-b")), {"relation": "TEST_REL"})


class PredicateApplicationTests(unittest.TestCase):
    def test_result_sort_is_situation_not_proposition(self):
        app = predicate_app("give", ("agent", "theme"), (ref("doctor"), ref("medicine")))
        self.assertEqual(sort_of(app), Sort.SIT)
        with self.assertRaises(InvariantViolation):
            Node("NOT", (app,))

    def test_roles_align_one_to_one_and_preserve_order(self):
        app = predicate_app("transfer", ("recipient", "agent", "theme"),
                            (ref("patient"), ref("doctor"), ref("drug")))
        self.assertEqual(app.get("roles"), ("recipient", "agent", "theme"))
        self.assertEqual([x.get("ref") for x in app.args], ["patient", "doctor", "drug"])

    def test_role_mismatch_and_empty_role_are_rejected(self):
        with self.assertRaises(InvariantViolation):
            predicate_app("give", ("agent",), (ref("doctor"), ref("drug")))
        with self.assertRaises(InvariantViolation):
            predicate_app("give", ("agent", ""), (ref("doctor"), ref("drug")))

    def test_structured_metadata_round_trips_without_becoming_logic(self):
        source = {"participants": [{"role": "agent", "id": "r1"}], "attributes": {"voice": "passive"}}
        app = predicate_app("give", ("agent",), (ref("doctor"),), eventFrame=source,
                            evidenceRefs=["ev-1"], temporalFrame={"tense": "past"})
        restored = node_from_json(node_to_json(app))
        self.assertEqual(restored, app)
        self.assertEqual(metadata_value(restored, "eventFrame"), source)
        self.assertEqual(metadata_value(restored, "evidenceRefs"), ["ev-1"])


class ConnectiveTests(unittest.TestCase):
    def test_connective_identity_and_operand_order_are_preserved(self):
        left, right = proposition("left"), proposition("right")
        node = connective("WHEN", (left, right), ("trigger", "result"), marker="when")
        self.assertEqual(sort_of(node), Sort.PROP)
        self.assertEqual(node.get("connective"), "WHEN")
        self.assertEqual(node.get("operandRoles"), ("trigger", "result"))
        self.assertEqual(node.args, (left, right))
        self.assertEqual(canonicalize(node), node)

    def test_conditional_requires_directed_antecedent_then_consequent(self):
        left, right = proposition("if"), proposition("then")
        self.assertEqual(connective("CONDITIONAL", (left, right),
                                    ("antecedent", "consequent")).args, (left, right))
        with self.assertRaises(InvariantViolation):
            connective("CONDITIONAL", (left, right), ("consequent", "antecedent"))

    def test_connective_rejects_non_prop_and_bad_roles(self):
        with self.assertRaises(InvariantViolation):
            connective("AND", (predicate_app("run", (), ()), proposition("p")),
                       ("left", "right"))
        with self.assertRaises(InvariantViolation):
            connective("AND", (proposition("a"), proposition("b")), ("same", "same"))
        with self.assertRaises(InvariantViolation):
            connective("AND", (proposition("a"), proposition("b")), ("left",))

    def test_unknown_connective_is_not_coerced(self):
        node = connective("SOURCE_SPECIFIC_CONNECTIVE", (proposition("a"), proposition("b")),
                          ("first", "second"))
        self.assertEqual(node.get("connective"), "SOURCE_SPECIFIC_CONNECTIVE")
        self.assertNotEqual(node.op, "AND")


class QuantifierTests(unittest.TestCase):
    def test_quantifier_has_prop_body_and_stable_binder_identity(self):
        body = Node("RELATE", (var("x", "binder-1"), ref("doctor")), {"relation": "OWNS"})
        q = quantifier("GENERAL", "FORALL", "binder-1", "x", body, "BODY",
                       restrictor={"predicate": "PERSON", "referent": "r1"},
                       variable_binding={"binderId": "binder-1", "role": "agent"})
        self.assertEqual(sort_of(q), Sort.PROP)
        self.assertEqual(q.args, (body,))
        self.assertEqual(metadata_value(q, "restrictor")["predicate"], "PERSON")
        self.assertEqual(check_native_scope(q), [])

    def test_free_binder_reference_is_reported(self):
        q = quantifier("GENERAL", "FORALL", "binder-1", "x",
                       Node("RELATE", (var("x", "other-binder"), ref("doctor")),
                            {"relation": "OWNS"}), "BODY")
        self.assertEqual(len(free_variable_occurrences(q)), 1)
        self.assertEqual(check_native_scope(q)[0][0], "VC-S12")

    def test_alpha_equivalence_uses_binder_identity_not_display_names(self):
        left = quantifier("GENERAL", "FORALL", "b1", "x",
                          Node("RELATE", (var("x", "b1"), ref("doctor")), {"relation": "OWNS"}), "BODY")
        right = quantifier("GENERAL", "FORALL", "b2", "person",
                           Node("RELATE", (var("person", "b2"), ref("doctor")), {"relation": "OWNS"}), "BODY")
        self.assertTrue(alpha_equivalent(left, right))
        left_with_binding = quantifier("GENERAL", "FORALL", "b1", "x",
            Node("RELATE", (var("x", "b1"), ref("doctor")), {"relation": "OWNS"}), "BODY",
            variable_binding={"binderId": "b1", "variable": "x", "role": "agent"})
        right_with_binding = quantifier("GENERAL", "FORALL", "b2", "person",
            Node("RELATE", (var("person", "b2"), ref("doctor")), {"relation": "OWNS"}), "BODY",
            variable_binding={"binderId": "b2", "variable": "person", "role": "agent"})
        self.assertTrue(alpha_equivalent(left_with_binding, right_with_binding))
        self.assertFalse(alpha_equivalent(left, quantifier("GENERAL", "EXISTS", "b2", "person",
                          Node("RELATE", (var("person", "b2"), ref("doctor")), {"relation": "OWNS"}), "BODY")))

    def test_quantifier_round_trip_and_canonicalization_are_idempotent(self):
        q = quantifier("COUNT", "EXACTLY", "b1", "x",
                       Node("RELATE", (var("x", "b1"), ref("doctor")), {"relation": "OWNS"}),
                       "BODY", count=3, surfaceText="exactly three")
        restored = node_from_json(node_to_json(q))
        self.assertEqual(restored, q)
        once = canonicalize(restored)
        twice = canonicalize(once)
        self.assertEqual(canonical_string(once), canonical_string(twice))
        self.assertEqual(once.get("binderId"), "b1")

    def test_count_must_be_nonnegative_integer(self):
        with self.assertRaises(InvariantViolation):
            quantifier("COUNT", "EXACTLY", "b1", "x", proposition("body"), "BODY", count=-1)

    def test_variable_binding_metadata_must_match_binder_identity(self):
        with self.assertRaises(InvariantViolation):
            quantifier("GENERAL", "FORALL", "b1", "x", proposition("body"), "BODY",
                       variable_binding={"binderId": "different-binder", "variable": "x"})

    def test_existing_scope_api_recognizes_identity_bound_variables(self):
        q = quantifier("GENERAL", "FORALL", "b1", "x",
                       Node("RELATE", (var("x", "b1"), ref("doctor")), {"relation": "OWNS"}), "BODY")
        self.assertEqual(free_vars(q), set())
        self.assertEqual(check_scope(q), [])
        renamed = alpha_rename(q)
        self.assertEqual(renamed.args[0].args[0].get("binderId"), "b1")

    def test_identity_bound_variable_is_not_captured_by_display_name(self):
        q = quantifier("GENERAL", "FORALL", "b1", "x",
                       Node("RELATE", (var("x", "b1"), var("y")), {"relation": "RELATED"}), "BODY")
        result = substitute_free(q, "y", ref("replacement"))
        self.assertEqual(result.args[0].args[0].get("binderId"), "b1")
        self.assertEqual(result.args[0].args[1].get("ref"), "replacement")


class PreservationNodeTests(unittest.TestCase):
    def test_opaque_and_unresolved_reference_are_distinct_and_not_inference_premises(self):
        op = opaque("NEW_OPERATOR", "no registered semantics", "PROP",
                    payload={"raw": "preserve"}, evidence_refs=["ev-1"])
        unresolved = unresolved_ref("ref-9", "referent not resolved", "TERM",
                                    role="agent", mention_ref="m-9")
        self.assertEqual(op.op, "OPAQUE")
        self.assertEqual(unresolved.op, "UNRESOLVED_REF")
        self.assertNotEqual(op, unresolved)
        self.assertEqual(sort_of(op), "ANY")
        self.assertFalse(inference_eligible(op))
        self.assertFalse(inference_eligible(Node("RELATE", (unresolved, ref("x")), {"relation": "R"})))
        self.assertTrue(inference_eligible(proposition("ordinary")))
        self.assertEqual(metadata_value(node_from_json(node_to_json(op)), "payload"), {"raw": "preserve"})


class LegacyCompatibilityTests(unittest.TestCase):
    def test_legacy_q_and_var_serialization_remain_unchanged(self):
        legacy = Node("Q", (proposition("restrictor"), proposition("scope")),
                      {"quant": "FORALL", "var": "x"})
        restored = node_from_json(node_to_json(legacy))
        self.assertEqual(restored, legacy)
        self.assertEqual(restored.op, "Q")

    def test_sit_is_only_promoted_by_explicit_holds(self):
        app = predicate_app("run", (), ())
        self.assertEqual(sort_of(holds(app)), Sort.PROP)
        self.assertEqual(sort_of(not_(app)), Sort.PROP)


if __name__ == "__main__":
    unittest.main()
