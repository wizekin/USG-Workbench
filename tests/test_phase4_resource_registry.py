import unittest

from tools.usg_interpretation_v0_1_0 import (
    ResourceDescriptor, SemanticAssociation, SemanticResourceRegistry,
)


class SemanticResourceRegistryTests(unittest.TestCase):
    def test_resource_manifest_is_versioned_and_content_addressed(self):
        registry = SemanticResourceRegistry("workspace-resources", 1)
        resource = ResourceDescriptor("en-lexicon-v1", "LEXICON", "1.0.0",
                                      "a" * 64, "en", "curated-fixture")
        updated = registry.with_resource(resource)
        self.assertEqual(updated.version, 2)
        self.assertEqual(len(updated.digest()), 64)
        self.assertNotEqual(registry.digest(), updated.digest())

    def test_associations_are_provisional_and_ranked_without_becoming_definitions(self):
        registry = SemanticResourceRegistry("workspace-resources", 1)
        low = SemanticAssociation("a1", "concept:code", "concept:computer",
                                  "used_with", "CO_OCCURRENCE", 0.4, 2, "corpus:1")
        high = SemanticAssociation("a2", "concept:code", "concept:program",
                                   "used_for", "FUNCTIONAL", 0.8, 1, "curated:1")
        updated = registry.with_association(low).with_association(high)
        ranked = updated.active_associations("concept:code")
        self.assertEqual([x.association_id for x in ranked], ["a2", "a1"])
        self.assertTrue(all(x.status == "PROVISIONAL" for x in ranked))
        self.assertNotIn("definitions", updated.manifest())

    def test_rejects_duplicate_resource_or_association_ids(self):
        registry = SemanticResourceRegistry("r", 1)
        resource = ResourceDescriptor("lex", "LEXICON", "1", "b" * 64, "en", "test")
        with_resource = registry.with_resource(resource)
        with self.assertRaises(ValueError):
            with_resource.with_resource(resource)
        association = SemanticAssociation("a", "x", "y", "related", "CONTEXTUAL", 0.5, 0, "test")
        with_association = registry.with_association(association)
        with self.assertRaises(ValueError):
            with_association.with_association(association)

    def test_rejects_invalid_weight_and_truthy_association_status(self):
        with self.assertRaises(ValueError):
            SemanticAssociation("a", "x", "y", "r", "CONTEXTUAL", 1.1, 0, "test")
        with self.assertRaises(ValueError):
            SemanticAssociation("a", "x", "y", "r", "CONTEXTUAL", 0.5, 0, "test", "VERIFIED")


if __name__ == "__main__":
    unittest.main()
