"""Phase 5 SQLite resource catalogue, integrity, and retrieval tests."""
import sqlite3
import unittest
from pathlib import Path

from tools.usg_interpretation_v0_1_0.resources import ResourceDescriptor, SemanticAssociation
from tools.usg_interpretation_v0_2_0 import (
    SQLiteResourceCatalogue, bundled_resource_descriptors,
    register_bundled_resources, verify_resource_file,
)


class Phase5SQLiteResourceCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("CREATE TABLE canonical_documents(document_id TEXT PRIMARY KEY)")
        self.connection.execute("BEGIN IMMEDIATE")
        self.catalogue = SQLiteResourceCatalogue(self.connection)
        self.connection.commit()
        self.connection.execute("BEGIN IMMEDIATE")

    def tearDown(self):
        if self.connection.in_transaction:
            self.connection.rollback()
        self.connection.close()

    def resource(self, resource_id="lexicon@test", digest="a" * 64):
        return ResourceDescriptor(
            resource_id, "LEXICON", "1.0.0", digest, "en",
            "Test resource descriptor with explicit provenance.",
        )

    def association(self, association_id, target, weight, observations=0):
        return SemanticAssociation(
            association_id, "concept:source", target, "RELATED_TO",
            "CONTEXTUAL", weight, observations,
            "Provisional association fixture; not a canonical definition.",
        )

    def test_catalogue_uses_the_callers_existing_sqlite_connection(self):
        self.assertIs(self.catalogue.connection, self.connection)
        self.catalogue.register_resource(self.resource(), registered_at=100.0)
        self.connection.commit()
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM canonical_documents"
        ).fetchone()[0], 0)
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM usg_resource_descriptor"
        ).fetchone()[0], 1)

    def test_installation_and_writes_require_caller_owned_transactions(self):
        other = sqlite3.connect(":memory:")
        try:
            with self.assertRaises(RuntimeError):
                SQLiteResourceCatalogue(other)
        finally:
            other.close()
        self.connection.commit()
        with self.assertRaises(RuntimeError):
            self.catalogue.register_resource(self.resource("no-txn"), 100.0)

    def test_resource_descriptors_are_immutable_and_new_versions_need_new_ids(self):
        self.catalogue.register_resource(self.resource(), 100.0)
        with self.assertRaises(ValueError):
            self.catalogue.register_resource(self.resource(), 101.0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "UPDATE usg_resource_descriptor SET version='2.0.0' WHERE resource_id='lexicon@test'"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "DELETE FROM usg_resource_descriptor WHERE resource_id='lexicon@test'"
            )
        self.catalogue.register_resource(self.resource("lexicon@test@2.0.0", "b" * 64), 102.0)

    def test_associations_remain_provisional_and_append_only(self):
        association = self.association("assoc-1", "concept:target", 0.6)
        self.catalogue.register_association(association, 100.0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "UPDATE usg_semantic_association SET status='CANONICAL' WHERE association_id='assoc-1'"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "DELETE FROM usg_semantic_association WHERE association_id='assoc-1'"
            )
        row = self.connection.execute(
            "SELECT status FROM usg_semantic_association WHERE association_id='assoc-1'"
        ).fetchone()
        self.assertEqual(row[0], "PROVISIONAL")

    def test_usage_ledger_is_append_only_and_does_not_change_manifest_digest(self):
        self.catalogue.register_association(self.association("assoc-1", "concept:target", 0.6), 100.0)
        before = self.catalogue.digest()
        version = self.catalogue.version
        self.catalogue.record_use("assoc-1", 200.0, "document:1")
        self.assertEqual(self.catalogue.digest(), before)
        self.assertEqual(self.catalogue.version, version)
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute("DELETE FROM usg_association_usage WHERE association_id='assoc-1'")

    def test_active_and_secondary_retrieval_uses_usage_and_slow_decay(self):
        self.catalogue.register_association(self.association("high-old", "concept:old", 0.8), 0.0)
        self.catalogue.register_association(self.association("medium-recent", "concept:recent", 0.5), 990.0)
        self.catalogue.register_association(self.association("used-often", "concept:frequent", 0.4), 990.0)
        for _ in range(4):
            self.catalogue.record_use("used-often", 995.0)
        ranked = self.catalogue.retrieve_associations(
            "concept:source", now=1000.0, active_limit=1, secondary_limit=1,
            half_life_seconds=1000.0,
        )
        self.assertEqual([x.association.association_id for x in ranked],
                         ["used-often", "medium-recent"])
        self.assertEqual([x.tier for x in ranked], ["ACTIVE", "SECONDARY"])
        self.assertEqual(ranked[0].total_observations, 4)
        self.assertGreater(ranked[0].activation_score, ranked[1].activation_score)

    def test_retrieval_is_deterministic_and_does_not_promote_associations(self):
        self.catalogue.register_association(self.association("assoc-1", "concept:a", 0.7), 100.0)
        self.catalogue.register_association(self.association("assoc-2", "concept:b", 0.7), 100.0)
        first = self.catalogue.retrieve_associations("concept:source", now=100.0)
        second = self.catalogue.retrieve_associations("concept:source", now=100.0)
        self.assertEqual([x.association.association_id for x in first],
                         [x.association.association_id for x in second])
        self.assertTrue(all(x.association.status == "PROVISIONAL" for x in first))

    def test_bundled_resources_have_reproducible_digests_and_register_as_one_snapshot(self):
        descriptors = bundled_resource_descriptors()
        self.assertGreaterEqual(len(descriptors), 8)
        root = Path(__file__).resolve().parents[1]
        lexicon = next(x for x in descriptors if x.resource_id == "usg-en-ar-discourse-lexicon")
        self.assertTrue(verify_resource_file(
            lexicon, root / "resources/lexical/v0.3.0/en-ar-discourse-lexicon.json"
        ))
        registered = register_bundled_resources(self.catalogue, registered_at=500.0)
        self.assertEqual(len(registered), len(descriptors))
        manifest = self.catalogue.manifest()
        self.assertEqual(len(manifest["resources"]), len(descriptors))
        self.assertEqual(manifest["registry_id"], "usg-v0.2-resource-catalogue")
        self.assertEqual(len(self.catalogue.digest()), 64)

    def test_catalogue_version_increments_for_registry_changes_but_not_usage_events(self):
        initial = self.catalogue.version
        self.catalogue.register_resource(self.resource(), 100.0)
        self.assertEqual(self.catalogue.version, initial + 1)
        self.catalogue.register_association(self.association("assoc-1", "concept:target", 0.6), 100.0)
        self.assertEqual(self.catalogue.version, initial + 2)
        self.catalogue.record_use("assoc-1", 101.0)
        self.assertEqual(self.catalogue.version, initial + 2)

    def test_rollback_removes_uncommitted_catalogue_changes(self):
        self.catalogue.register_resource(self.resource("rolled-back"), 100.0)
        self.connection.rollback()
        self.assertEqual(self.connection.execute(
            "SELECT COUNT(*) FROM usg_resource_descriptor"
        ).fetchone()[0], 0)
        self.assertEqual(self.connection.execute(
            "SELECT version FROM usg_resource_catalogue_state"
        ).fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
