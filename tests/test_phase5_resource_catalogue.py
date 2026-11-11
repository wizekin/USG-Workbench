"""Phase 5 Step 5.9 persistent resource catalogue conformance tests."""
from datetime import datetime, timezone
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore
from tools.usg_resource_catalogue_v0_1_0 import (
    InvalidResourceError,
    ResourceActivationConflictError,
    ResourceCatalogueError,
    ResourceIntegrityError,
    ResourceNotFoundError,
    ResourceVersionConflictError,
    SQLiteResourceCatalogue,
)


class ResourceCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "usg.sqlite3"
        self.catalogue = SQLiteResourceCatalogue(self.database)

    def tearDown(self):
        self.catalogue.close()
        self.temp.cleanup()

    @staticmethod
    def provenance():
        return {"origin": "project_authored", "method": "bounded_test_fixture"}

    def put(self, resource_id="lex.en.core", version="1.0.0",
            resource_class="LEXICAL_REALIZATION", content=None, **kwargs):
        return self.catalogue.put_resource(
            resource_id, version, resource_class,
            content if content is not None else {"entries": [{"form": "write", "lemma": "write"}]},
            self.provenance(), **kwargs,
        )

    def test_versioned_snapshot_is_immutable_and_identical_retry_is_idempotent(self):
        first = self.put(activate=True)
        retry = self.put()
        self.assertEqual(first.digest, retry.digest)
        self.assertEqual(retry.write_status, "UNCHANGED")
        with self.assertRaises(ResourceVersionConflictError):
            self.put(content={"entries": [{"form": "write", "lemma": "compose"}]})
        self.assertEqual(self.catalogue.get_resource("lex.en.core").content["entries"][0]["lemma"], "write")

    def test_new_versions_are_secondary_until_explicit_activation(self):
        self.put(activate=True)
        self.put(version="1.1.0", content={"entries": [{"form": "read"}]})
        self.assertEqual(self.catalogue.get_resource("lex.en.core").version, "1.0.0")
        results = self.catalogue.retrieve("LEXICAL_REALIZATION")
        self.assertEqual([item.snapshot.version for item in results], ["1.0.0", "1.1.0"])
        self.assertTrue(results[0].snapshot.active)
        self.assertFalse(results[1].snapshot.active)

    def test_activation_uses_compare_and_swap(self):
        self.put(activate=True)
        self.put(version="1.1.0", content={"entries": [{"form": "read"}]})
        with self.assertRaises(ResourceActivationConflictError):
            self.catalogue.set_active_version("lex.en.core", "1.1.0", expected_active_version=None)
        self.catalogue.set_active_version(
            "lex.en.core", "1.1.0", expected_active_version="1.0.0"
        )
        self.assertEqual(self.catalogue.get_resource("lex.en.core").version, "1.1.0")
        self.assertEqual(self.catalogue.get_resource("lex.en.core", "1.0.0").version, "1.0.0")

    def test_activation_rejects_missing_snapshot(self):
        with self.assertRaises(ResourceNotFoundError):
            self.catalogue.set_active_version("missing", "1.0.0", expected_active_version=None)

    def test_all_resource_classes_are_supported_and_separate(self):
        classes = (
            "LEXICAL_REALIZATION", "GRAMMAR_PATTERN", "SEMANTIC_FRAME",
            "DISCOURSE_RESOURCE",
        )
        for index, resource_class in enumerate(classes):
            self.put(
                resource_id=f"resource.{index}", resource_class=resource_class,
                content={"payload": [resource_class]},
            )
        self.put(
            resource_id="resource.association", resource_class="PROVISIONAL_ASSOCIATION",
            content={"associations": [{
                "association_id": "a1", "source_ref": "concept:a",
                "relation": "related_to", "target_ref": "concept:b",
            }]},
        )
        self.assertEqual(
            {item.resource_class for item in self.catalogue.list_resources()},
            set(classes) | {"PROVISIONAL_ASSOCIATION"},
        )

    def test_resource_class_cannot_change_between_versions(self):
        self.put(activate=True)
        with self.assertRaises(ResourceCatalogueError):
            self.catalogue.put_resource(
                "lex.en.core", "1.1.0", "GRAMMAR_PATTERN",
                {"patterns": []}, self.provenance(),
            )

    def test_sqlite_triggers_prevent_snapshot_and_usage_event_mutation(self):
        self.put(activate=True)
        self.catalogue.record_usage("lex.en.core", "1.0.0", "2026-01-01T00:00:00+00:00")
        with sqlite3.connect(self.database) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE semantic_resource_snapshots SET created_at=? WHERE resource_id=?",
                    ("changed", "lex.en.core"),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "DELETE FROM semantic_resource_usage_events WHERE resource_id=?",
                    ("lex.en.core",),
                )

    def test_provenance_and_resource_envelope_are_required(self):
        with self.assertRaises(InvalidResourceError):
            self.catalogue.put_resource(
                "empty.provenance", "1.0.0", "LEXICAL_REALIZATION",
                {"entries": []}, {},
            )
        with self.assertRaises(InvalidResourceError):
            self.catalogue.put_resource(
                "bad.version", "latest", "LEXICAL_REALIZATION",
                {"entries": []}, self.provenance(),
            )
        with self.assertRaises(InvalidResourceError):
            self.catalogue.put_resource(
                "bad.class", "1.0.0", "ONTOLOGY_MAGIC",
                {"entries": []}, self.provenance(),
            )
        with self.assertRaises(InvalidResourceError):
            self.catalogue.put_resource(
                "bad.content", "1.0.0", "LEXICAL_REALIZATION",
                ["not", "an", "object"], self.provenance(),
            )

    def test_provisional_association_requires_explicit_endpoints_and_unique_ids(self):
        invalid = [
            {"associations": [{}]},
            {"associations": [
                {"association_id": "same", "source_ref": "a", "relation": "r", "target_ref": "b"},
                {"association_id": "same", "source_ref": "c", "relation": "r", "target_ref": "d"},
            ]},
            {"entries": []},
        ]
        for index, content in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(InvalidResourceError):
                self.put(
                    resource_id=f"association.invalid.{index}",
                    resource_class="PROVISIONAL_ASSOCIATION", content=content,
                )

    def test_association_retrieval_is_exact_and_never_resolves_identity(self):
        self.put(
            resource_id="associations.project", resource_class="PROVISIONAL_ASSOCIATION",
            content={"associations": [
                {"association_id": "a1", "source_ref": "concept:a", "relation": "used_with",
                 "target_ref": "concept:b", "evidence_ref": "source:1"},
                {"association_id": "a2", "source_ref": "concept:a", "relation": "related_to",
                 "target_ref": "concept:c"},
            ]},
            activate=True,
        )
        results = self.catalogue.retrieve_associations(
            source_ref="concept:a", relation="used_with"
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].association_id, "a1")
        self.assertEqual(results[0].status, "PROVISIONAL")
        self.assertFalse(results[0].identity_resolution)
        self.assertEqual(results[0].attributes, {"evidence_ref": "source:1"})

    def test_usage_decay_is_deterministic_and_is_retrieval_metadata_only(self):
        self.put(activate=True)
        event_time = "2026-01-01T00:00:00+00:00"
        self.catalogue.record_usage("lex.en.core", "1.0.0", event_time)
        exact = self.catalogue.retrieve(
            "LEXICAL_REALIZATION", now=event_time, half_life_seconds=864000
        )[0]
        decayed = self.catalogue.retrieve(
            "LEXICAL_REALIZATION", now="2026-01-11T00:00:00+00:00",
            half_life_seconds=864000,
        )[0]
        self.assertEqual(exact.usage_count, 1)
        self.assertAlmostEqual(exact.activation_score, 1.0)
        self.assertAlmostEqual(decayed.activation_score, 0.5)
        self.assertEqual(exact.snapshot.digest, decayed.snapshot.digest)

    def test_usage_requires_an_existing_version_and_timezone(self):
        with self.assertRaises(ResourceNotFoundError):
            self.catalogue.record_usage("missing", "1.0.0")
        self.put(activate=True)
        with self.assertRaises(InvalidResourceError):
            self.catalogue.record_usage("lex.en.core", "1.0.0", "2026-01-01T00:00:00")

    def test_resource_snapshots_survive_reopen(self):
        self.put(activate=True)
        digest = self.catalogue.get_resource("lex.en.core").digest
        self.catalogue.close()
        self.catalogue = SQLiteResourceCatalogue(self.database)
        restored = self.catalogue.get_resource("lex.en.core")
        self.assertEqual(restored.digest, digest)
        self.assertEqual(self.catalogue.verify_integrity()["status"], "PASS")

    def test_catalogue_shares_the_canonical_sqlite_database_file(self):
        with CanonicalDocumentStore(self.database):
            with sqlite3.connect(self.database) as connection:
                names = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
            self.assertIn("document_revisions", names)
            self.assertIn("semantic_resource_snapshots", names)
            self.assertIn("documents", names)

    def test_resource_reads_reject_tampered_canonical_bytes(self):
        self.put(activate=True)
        with sqlite3.connect(self.database) as connection:
            connection.execute("DROP TRIGGER immutable_resource_snapshot_update")
            connection.execute(
                "UPDATE semantic_resource_snapshots SET canonical_json=? WHERE resource_id=?",
                (sqlite3.Binary(b"{}"), "lex.en.core"),
            )
        with self.assertRaises(ResourceIntegrityError):
            self.catalogue.get_resource("lex.en.core")
        self.assertEqual(self.catalogue.verify_integrity()["status"], "FAIL")

    def test_retrieval_can_exclude_secondary_snapshots(self):
        self.put(activate=True)
        self.put(resource_id="lex.en.extra", content={"entries": [{"form": "read"}]})
        results = self.catalogue.retrieve(
            "LEXICAL_REALIZATION", include_secondary=False
        )
        self.assertEqual([item.snapshot.resource_id for item in results], ["lex.en.core"])

    def test_invalid_retrieval_configuration_is_rejected(self):
        with self.assertRaises(InvalidResourceError):
            self.catalogue.retrieve("UNKNOWN")
        with self.assertRaises(InvalidResourceError):
            self.catalogue.retrieve("LEXICAL_REALIZATION", half_life_seconds=0)


if __name__ == "__main__":
    unittest.main()
