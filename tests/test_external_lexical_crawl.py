"""Tests for the resumable scheduled lexical crawler."""
from __future__ import annotations

import gzip
import json
import unittest

import tools.usg_external_lexical_v0_1_0.crawl as crawl
from tools.usg_external_lexical_v0_1_0.crawl import (
    LexicalCrawler,
    GitHubDataPublisher,
    _compact_entry,
    parse_headword_page,
)
from tools.usg_external_lexical_v0_1_0.providers import ProviderError, parse_english_dictionary_entry


SHA = "a" * 40
SNAPSHOT = "fixture-snapshot-2026-11"


ENTRY = """---
kind: "dictionary-entry"
schema_version: 1
entry_id: "en-cat-fixture"
headword: "cat"
language: "en"
source_records: 1
sense_count: 1
source_id: "enwiktionary"
source_url: "https://en.wiktionary.org/wiki/cat#English"
history_url: "https://en.wiktionary.org/w/index.php?title=cat&action=history"
license: "CC-BY-SA-4.0"
snapshot_id: "fixture-snapshot-2026-11"
review_status: "automated-source-preserving-corrections; full-linguistic-review-pending"
relation_link_scope: "exact-headword-entry; not sense-resolved"
---
# cat

## Noun · Etymology 1 · Record 1

### Forms

- cats — plural

### Senses

<a id="r1-s1"></a>

**Source sense R1.S1**

1. A small domesticated carnivorous mammal.

   **Example:** The cat sleeps.

### Related words

**Source synonyms:** [feline](../../entries/002/feline.md)
"""


class FakeClient:
    def __init__(self, text_map):
        self.text_map = text_map
        self.requests = []

    def get_text(self, url):
        self.requests.append(url)
        if url not in self.text_map:
            raise AssertionError("Unexpected URL: " + url)
        return self.text_map[url], {}

    def get_json(self, url):
        self.requests.append(url)
        return {"sha": SHA}, {}


class FakePublisher:
    def __init__(self):
        self.calls = []

    def publish(self, shard_path, shard_bytes, checkpoint, manifest, message):
        self.calls.append({
            "shard_path": shard_path,
            "shard_bytes": shard_bytes,
            "checkpoint": checkpoint,
            "manifest": manifest,
            "message": message,
        })
        return "b" * 40


def source_urls():
    base = f"https://raw.githubusercontent.com/figueirego/english-dictionary/{SHA}/"
    return {
        base + "dictionary/INDEX.md": """---
kind: "dictionary-index"
headwords: 1
---
- [A](browse/a/INDEX.md)
""",
        base + "dictionary/SOURCE.md": f"""---
kind: "public-source-snapshot"
snapshot_id: "{SNAPSHOT}"
dump_date: "2026-10-01"
license: "CC-BY-SA-4.0"
---
""",
        base + "dictionary/browse/a/INDEX.md": f"""---
kind: "alphabetical-letter-index"
snapshot_id: "{SNAPSHOT}"
headwords: 1
pages: 1
---
| Page | First headword | Last headword | Headwords |
| --- | --- | --- | ---: |
| [1](0001.md) | cat | cat | 1 |
""",
        base + "dictionary/browse/a/0001.md": f"""---
kind: "alphabetical-headword-page"
snapshot_id: "{SNAPSHOT}"
headwords: 1
---
- [cat](../../entries/001/cat--fixture.md)
""",
        base + "dictionary/entries/001/cat--fixture.md": ENTRY,
    }


def initial_checkpoint():
    return {
        "schema_version": "usg-lexical-crawl-checkpoint/0.1.0",
        "status": "not_started",
        "source_repository": "figueirego/english-dictionary",
        "source_commit": None,
        "source_snapshot_id": None,
        "pages": [],
        "page_index": 0,
        "entry_index": 0,
        "batch_number": 0,
        "processed_headwords": 0,
        "processed_entries": 0,
        "processed_senses": 0,
        "failed_headwords": 0,
        "failed_pages": 0,
        "stored_bytes": 0,
        "updated_at": None,
    }


class ScheduledLexicalCrawlerTests(unittest.TestCase):
    def test_headword_page_parser_checks_snapshot_and_safe_entry_paths(self):
        page = f"""---
kind: "alphabetical-headword-page"
snapshot_id: "{SNAPSHOT}"
headwords: 2
---
- [cat](../../entries/001/cat.md)
- [Cat](../../entries/002/cat-capital.md)
"""
        rows = parse_headword_page(
            page, "dictionary/browse/c/0001.md", expected_snapshot_id=SNAPSHOT
        )
        self.assertEqual([row["headword_candidate"] for row in rows], ["cat", "Cat"])
        self.assertEqual(rows[0]["entry_path"], "dictionary/entries/001/cat.md")

    def test_headword_page_rejects_snapshot_mismatch_and_path_traversal(self):
        page = """---
kind: "alphabetical-headword-page"
snapshot_id: "different"
headwords: 1
---
- [cat](../../entries/001/cat.md)
"""
        with self.assertRaises(Exception):
            parse_headword_page(
                page, "dictionary/browse/c/0001.md", expected_snapshot_id=SNAPSHOT
            )
        unsafe = f"""---
kind: "alphabetical-headword-page"
snapshot_id: "{SNAPSHOT}"
headwords: 1
---
- [cat](../../../../README.md)
"""
        with self.assertRaises(Exception):
            parse_headword_page(unsafe, "dictionary/browse/c/0001.md", SNAPSHOT)

    def test_compact_projection_keeps_relations_and_provenance_but_not_definition_text(self):
        parsed = parse_english_dictionary_entry(
            ENTRY, "cat", "https://raw.githubusercontent.com/example/dictionary/cat.md"
        )
        parsed["source"]["provider"] = "english_dictionary_github"
        for item in parsed["entries"]:
            item["provider"] = "english_dictionary_github"
        analysis = {
            "analysis_version": "test-analysis/1",
            "validation": {"status": "valid", "error_count": 0, "warning_count": 0},
        }
        compact = _compact_entry(parsed, "cat", "dictionary/entries/001/cat.md", analysis)
        serialized = json.dumps(compact, ensure_ascii=False)
        self.assertNotIn("A small domesticated carnivorous mammal.", serialized)
        self.assertNotIn("The cat sleeps.", serialized)
        self.assertIn("definition_sha256", serialized)
        self.assertIn("history_url", serialized)
        self.assertEqual(compact["analysis_summary"]["sense_count"], 1)
        sense = compact["entries"][0]["senses"][0]
        self.assertEqual(sense["definition_pattern"]["pattern_type"], "initial_nominal_phrase")
        self.assertEqual(compact["entries"][0]["relations"][0]["scope"], "entry")
        self.assertEqual(compact["rights_policy"]["raw_definitions_persisted"], False)

    def test_scheduled_batch_resumes_and_publishes_one_compressed_shard(self):
        urls = source_urls()
        data_branch_url = (
            "https://raw.githubusercontent.com/wizekin/USG-Workbench/"
            "usg-external-lexical-data/state/checkpoint.json"
        )
        urls[data_branch_url] = json.dumps(initial_checkpoint())
        client = FakeClient(urls)
        publisher = FakePublisher()
        crawler = LexicalCrawler(client=client, publisher=publisher, delay_seconds=0)
        result = crawler.run_batch(
            max_runtime_seconds=60, max_headwords=10, max_shard_bytes=1024 * 1024,
            run_id="test-run",
        )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["batch"]["headwords"], 1)
        self.assertEqual(result["batch"]["senses"], 1)
        self.assertTrue(result["published"])
        self.assertEqual(len(publisher.calls), 1)
        call = publisher.calls[0]
        self.assertTrue(call["shard_path"].endswith(".jsonl.gz"))
        self.assertEqual(call["checkpoint"]["processed_headwords"], 1)
        row = json.loads(gzip.decompress(call["shard_bytes"]).decode("utf-8").splitlines()[0])
        self.assertEqual(row["headword_candidate"], "cat")
        self.assertNotIn("definition", row["entries"][0]["senses"][0])
        self.assertEqual(row["source_provenance"]["license"], "CC-BY-SA-4.0")

    def test_browse_page_error_is_recorded_without_advancing_cursor(self):
        urls = source_urls()
        data_branch_url = (
            "https://raw.githubusercontent.com/wizekin/USG-Workbench/"
            "usg-external-lexical-data/state/checkpoint.json"
        )
        urls[data_branch_url] = json.dumps(initial_checkpoint())

        class FailingPageClient(FakeClient):
            def get_text(self, url):
                if url.endswith("/dictionary/browse/a/0001.md"):
                    raise ProviderError("temporary browse page failure")
                return super().get_text(url)

        publisher = FakePublisher()
        crawler = LexicalCrawler(
            client=FailingPageClient(urls), publisher=publisher, delay_seconds=0
        )
        result = crawler.run_batch(
            max_runtime_seconds=60, max_headwords=10,
            max_shard_bytes=1024 * 1024, run_id="page-retry-test",
        )

        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["stop_reason"], "browse_page_error")
        self.assertEqual(result["cursor"]["page_index"], 0)
        self.assertEqual(result["cursor"]["entry_index"], 0)
        self.assertEqual(result["batch"]["headwords"], 0)
        self.assertEqual(result["batch"]["failed_pages"], 1)
        self.assertEqual(result["batch"]["failed_headwords"], 0)
        checkpoint = publisher.calls[0]["checkpoint"]
        self.assertEqual(checkpoint["page_index"], 0)
        self.assertEqual(checkpoint["entry_index"], 0)
        self.assertEqual(checkpoint["failed_pages"], 1)
        self.assertEqual(checkpoint["failed_headwords"], 0)
        events = gzip.decompress(publisher.calls[0]["shard_bytes"]).decode("utf-8")
        event = json.loads(events.splitlines()[0])
        self.assertEqual(event["event_type"], "browse_page_error")

    def test_publisher_updates_branch_ref_after_building_commit(self):
        calls = []
        def fake_api(method, url, token, payload=None):
            calls.append((method, url, payload))
            if method == "GET" and url.endswith("/git/ref/heads/usg-external-lexical-data"):
                return {"object": {"sha": "head-sha"}}
            if method == "GET" and url.endswith("/git/commits/head-sha"):
                return {"tree": {"sha": "base-tree"}}
            if method == "POST" and url.endswith("/git/blobs"):
                return {"sha": f"blob-{len(calls)}"}
            if method == "POST" and url.endswith("/git/trees"):
                return {"sha": "new-tree"}
            if method == "POST" and url.endswith("/git/commits"):
                return {"sha": "new-commit"}
            if method == "PATCH" and url.endswith("/git/refs/heads/usg-external-lexical-data"):
                return {}
            raise AssertionError(f"Unexpected API call: {method} {url}")

        original = crawl._github_api_request
        crawl._github_api_request = fake_api
        try:
            publisher = GitHubDataPublisher("wizekin/USG-Workbench", "test-token")
            result = publisher.publish(
                "shards/test/batch-1.jsonl.gz", b"compressed",
                {"status": "in_progress"}, {"batch_count": 1}, "test commit",
            )
        finally:
            crawl._github_api_request = original
        self.assertEqual(result, "new-commit")
        self.assertTrue(any(url.endswith("/git/refs/heads/usg-external-lexical-data") for method, url, _ in calls if method == "PATCH"))
        self.assertTrue(any(method == "POST" and url.endswith("/git/trees") for method, url, _ in calls))


if __name__ == "__main__":
    unittest.main()
