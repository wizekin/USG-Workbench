import unittest

from usg_definitions_v14 import (
    MODEL_VERSION, SemanticKind, ConceptDefinitionV14, FrameDefinitionV14,
    RoleDefinitionV14, RelationDefinitionV14, DefinitionsCatalogueV14,
    same_definition,
)


class NativeDefinitionsV14Tests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(MODEL_VERSION, "1.4.0")

    def test_all_semantic_kinds_are_preserved(self):
        self.assertEqual(len(SemanticKind), 15)
        self.assertIn(SemanticKind.EXPRESSION, set(SemanticKind))

    def test_concept_preserves_required_and_optional_fields(self):
        item = ConceptDefinitionV14("concept:1", "CUSTOMER", SemanticKind.ENTITY, 2,
                                    "A customer", "ACTIVE")
        self.assertEqual(item.semantic_kind, SemanticKind.ENTITY)
        self.assertEqual(item.version, 2)
        self.assertEqual(item.definition, "A customer")
        self.assertEqual(item.lifecycle_stage, "ACTIVE")

    def test_concept_rejects_boolean_or_nonpositive_version(self):
        for version in (True, 0, -1):
            with self.subTest(version=version), self.assertRaises(ValueError):
                ConceptDefinitionV14("c:1", "x", SemanticKind.ENTITY, version)

    def test_concept_requires_semantic_kind_enum(self):
        with self.assertRaises(TypeError):
            ConceptDefinitionV14("c:1", "x", "ENTITY", 1)

    def test_frame_preserves_ordered_roles(self):
        item = FrameDefinitionV14("f:1", "TRANSFER", 1, ("AGENT", "THEME", "AGENT"),
                                  SemanticKind.EVENT)
        self.assertEqual(item.roles, ("AGENT", "THEME", "AGENT"))

    def test_frame_roles_require_tuple_of_nonempty_strings(self):
        with self.assertRaises(ValueError):
            FrameDefinitionV14("f:1", "x", 1, ("AGENT", ""))
        with self.assertRaises(ValueError):
            FrameDefinitionV14("f:1", "x", 1, ["AGENT"])

    def test_frame_optional_semantic_kind(self):
        self.assertIsNone(FrameDefinitionV14("f:1", "x", 1, ()).semantic_kind)

    def test_role_constraints_preserve_nested_data(self):
        value = {"minimum": 1, "allowedKinds": ["ENTITY", "ARTIFACT"]}
        item = RoleDefinitionV14("r:1", "AGENT", constraints=value)
        self.assertEqual(item.constraints, value)

    def test_relation_properties_preserve_nested_data(self):
        value = {"symmetric": False, "inverse": {"ref": "relation:2"}}
        item = RelationDefinitionV14("rel:1", "CAUSES", properties=value)
        self.assertEqual(item.properties, value)

    def test_unknown_canonical_extras_are_retained(self):
        extras = {"future": {"preserve": True}}
        concept = ConceptDefinitionV14("c:1", "x", SemanticKind.ENTITY, 1,
                                       canonical_extras=extras)
        extras["future"]["preserve"] = False
        self.assertEqual(concept.canonical_extras, {"future": {"preserve": True}})

    def test_metadata_requires_mapping_and_string_keys(self):
        with self.assertRaises(TypeError):
            RoleDefinitionV14("r:1", "x", constraints=["bad"])
        with self.assertRaises(ValueError):
            RelationDefinitionV14("rel:1", "x", properties={1: "bad"})

    def test_catalogue_preserves_group_order_and_versions(self):
        concept = ConceptDefinitionV14("c:1", "x", SemanticKind.ENTITY, 1)
        frame = FrameDefinitionV14("f:1", "x", 1, ("r:1",))
        role = RoleDefinitionV14("r:1", "x")
        relation = RelationDefinitionV14("rel:1", "x")
        catalogue = DefinitionsCatalogueV14((concept,), (frame,), (role,), (relation,),
                                             "grammar-1", "ontology-2")
        self.assertEqual(catalogue.concepts, (concept,))
        self.assertEqual(catalogue.frames, (frame,))
        self.assertEqual(catalogue.grammar_version, "grammar-1")
        self.assertEqual(catalogue.ontology_release, "ontology-2")

    def test_catalogue_requires_ordered_typed_groups(self):
        with self.assertRaises(TypeError):
            DefinitionsCatalogueV14([], (), (), ())

    def test_definition_identity_is_opaque(self):
        left = ConceptDefinitionV14("c:1", "one", SemanticKind.ENTITY, 1)
        same = ConceptDefinitionV14("c:1", "different", SemanticKind.EVENT, 2)
        other = ConceptDefinitionV14("c:2", "one", SemanticKind.ENTITY, 1)
        self.assertTrue(same_definition(left, same))
        self.assertFalse(same_definition(left, other))


if __name__ == "__main__":
    unittest.main()
