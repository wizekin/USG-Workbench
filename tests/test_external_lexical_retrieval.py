"""Tests for on-demand retrieval, source normalization, cache and analysis contracts."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.usg_external_lexical_v0_1_0.analysis import analyze_bundle, classify_definition_pattern
from tools.usg_external_lexical_v0_1_0.cache import LexicalCache
from tools.usg_external_lexical_v0_1_0.evaluation import run_structural_benchmark
from tools.usg_external_lexical_v0_1_0.providers import (
    DictionaryApiDevProvider,
    EnglishDictionaryGitHubProvider,
    FreeDictionaryApiProvider,
    parse_english_dictionary_entry,
)
from tools.usg_external_lexical_v0_1_0.service import ExternalLexicalService


ENTRY_FIXTURE = """---
kind: "dictionary-entry"
schema_version: 1
entry_id: "en-bank-fixture"
headword: "bank"
language: "en"
source_records: 2
sense_count: 2
source_url: "https://en.wiktionary.org/wiki/bank#English"
history_url: "https://en.wiktionary.org/w/index.php?title=bank&action=history"
license: "CC-BY-SA-4.0"
snapshot_id: "fixture-snapshot"
review_status: "automated-source-preserving-corrections; full-linguistic-review-pending"
relation_link_scope: "exact-headword-entry; not sense-resolved"
---
# bank

## Noun · Etymology 1 · Record 1

### Forms

- banks — plural

### Senses

<a id="r1-s1"></a>

**Source sense R1.S1**

1. The land alongside a river.

   **Example:** The boat reached the bank.

### Related words

**Source synonyms:** [riverside](../../entries/001/riverside.md)

## Verb · Etymology 2 · Record 2

### Senses

<a id="r2-s1"></a>

**Source sense R2.S1**

1. To deposit money at a financial institution.
"""


class FakeClient:
    def __init__(self, json_payload=None, text_payloads=None):
        self.json_payload = json_payload
        self.text_payloads = text_payloads or {}
        self.urls = []

    def get_json(self, url):
        self.urls.append(url)
        return self.json_payload, {}

    def get_text(self, url):
        self.urls.append(url)
        if url not in self.text_payloads:
            raise AssertionError("unexpected network request: " + url)
        return self.text_payloads[url], {}


class FakeProvider:
    provider_id = "fixture_provider"

    def __init__(self):
        self.calls = 0

    def lookup(self, word):
        self.calls += 1
        return {
            "provider": self.provider_id,
            "queried_form": word,
            "retrieved_at": "2026-11-11T00:00:00+00:00",
            "source": {"provider": self.provider_id, "license": "fixture-only"},
            "entries": [{
                "entry_id": "fixture-" + word,
                "lemma": word,
                "language": "en",
                "part_of_speech": "noun",
                "provider": self.provider_id,
                "forms": [{"form": word + "s", "tags": ["plural"]}],
                "relations": [],
                "senses": [{
                    "sense_id": "sense-" + word,
                    "source_sense_id": "1",
                    "part_of_speech": "noun",
                    "definition": "A type of useful example.",
                    "examples": [],
                    "tags": [],
                    "relations": [],
                }],
            }],
        }


class ExternalLexicalTests(unittest.TestCase):
    def test_free_dictionary_api_preserves_sense_relations_and_source_license(self):
        payload = {
            "word": "bright",
            "entries": [{
                "language": {"code": "en", "name": "English"},
                "partOfSpeech": "adjective",
                "forms": [{"word": "brighter", "tags": ["comparative"]}],
                "senses": [{
                    "definition": "Emitting much light.",
                    "examples": ["A bright lamp."],
                    "synonyms": ["luminous"],
                    "antonyms": ["dark"],
                }],
                "synonyms": ["radiant"],
            }],
            "source": {
                "url": "https://en.wiktionary.org/wiki/bright",
                "license": {"name": "CC BY-SA 4.0", "url": "https://creativecommons.org/licenses/by-sa/4.0/"},
            },
        }
        provider = FreeDictionaryApiProvider(FakeClient(json_payload=payload))
        result = provider.lookup("bright")
        entry = result["entries"][0]
        sense = entry["senses"][0]
        self.assertEqual(entry["forms"][0]["form"], "brighter")
        self.assertEqual({r["type"] for r in sense["relations"]}, {"synonym", "antonym"})
        self.assertTrue(all(r["scope"] == "sense" for r in sense["relations"]))
        self.assertEqual(entry["relations"][0]["scope"], "entry")
        self.assertIn("CC BY-SA 4.0", result["source"]["license"])

    def test_dictionaryapi_dev_v2_creates_independent_senses(self):
        payload = [{
            "word": "bank",
            "phonetics": [{"text": "/bæŋk/"}],
            "meanings": [
                {"partOfSpeech": "noun", "definitions": [
                    {"definition": "The land alongside a river.", "synonyms": ["riverside"], "antonyms": []},
                    {"definition": "A financial institution.", "synonyms": [], "antonyms": []},
                ]},
                {"partOfSpeech": "verb", "definitions": [
                    {"definition": "To deposit money.", "example": "I bank at a local branch."},
                ]},
            ],
            "sourceUrls": ["https://en.wiktionary.org/wiki/bank"],
        }]
        result = DictionaryApiDevProvider(FakeClient(json_payload=payload)).lookup("bank")
        senses = [sense for entry in result["entries"] for sense in entry["senses"]]
        # One API meaning/POS entry can contain multiple separately identified senses.
        self.assertEqual(len(result["entries"]), 2)
        self.assertEqual(len(result["entries"][0]["senses"]), 2)
        self.assertEqual(len(senses), 3)
        self.assertEqual(len({sense["sense_id"] for sense in senses}), 3)
        self.assertEqual(senses[0]["relations"][0]["scope"], "sense")
        self.assertEqual(result["source"]["record_urls"], ["https://en.wiktionary.org/wiki/bank"])

    def test_github_entry_parser_retains_pos_senses_forms_and_entry_level_relation_scope(self):
        result = parse_english_dictionary_entry(
            ENTRY_FIXTURE, "bank", "https://raw.githubusercontent.com/example/repo/abc/entry.md"
        )
        self.assertEqual(len(result["entries"]), 2)
        noun, verb = result["entries"]
        self.assertEqual(noun["part_of_speech"], "Noun")
        self.assertEqual(noun["forms"][0]["form"], "banks")
        self.assertEqual(noun["senses"][0]["source_sense_id"], "R1.S1")
        self.assertEqual(noun["senses"][0]["definition"], "The land alongside a river.")
        self.assertEqual(noun["relations"][0]["target_lemma"], "riverside")
        self.assertEqual(noun["relations"][0]["scope"], "entry")
        self.assertEqual(verb["part_of_speech"], "Verb")
        self.assertEqual(verb["senses"][0]["definition"], "To deposit money at a financial institution.")
        self.assertEqual(result["source"]["snapshot_id"], "fixture-snapshot")
        self.assertEqual(result["source"]["editorial_review_status"], "automated-source-preserving-corrections; full-linguistic-review-pending")

    def test_github_provider_fetches_only_the_requested_entry_path(self):
        sha = "a" * 40
        base = f"https://raw.githubusercontent.com/figueirego/english-dictionary/{sha}/"
        index_path = "dictionary/browse/b/INDEX.md"
        page_path = "dictionary/browse/b/0001.md"
        entry_path = "dictionary/entries/abc/bank--fixture.md"
        texts = {
            base + index_path: """---
kind: "alphabetical-letter-index"
---
| [1](0001.md) | bank | bankable | 10 |
""",
            base + page_path: """---
kind: "alphabetical-headword-page"
---
- [bank](../../entries/abc/bank--fixture.md)
""",
            base + entry_path: ENTRY_FIXTURE,
        }
        client = FakeClient(text_payloads=texts)
        provider = EnglishDictionaryGitHubProvider(client=client, commit_sha=sha)
        result = provider.lookup("bank")
        self.assertEqual(result["entries"][0]["lemma"], "bank")
        self.assertEqual(result["source"]["commit_sha"], sha)
        self.assertEqual(len(client.urls), 3)
        self.assertTrue(client.urls[-1].endswith(entry_path))
        self.assertFalse(any("entries/" in url and url != client.urls[-1] for url in client.urls))

    def test_cache_persists_only_requested_words_and_tracks_incremental_use(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "cache.sqlite3"
            provider = FakeProvider()
            cache = LexicalCache(path)
            service = ExternalLexicalService(cache=cache, providers=[provider])
            first = service.lookup("example", providers=[provider.provider_id])
            second = service.lookup("example", providers=[provider.provider_id])
            self.assertEqual(provider.calls, 1)
            self.assertEqual(first["status"], "found")
            self.assertTrue(second["cache"]["hit"])
            self.assertEqual(service.activity(1)[0]["use_count"], 2)
            service.close()
            self.assertTrue(path.exists())
            with LexicalCache(path) as reopened:
                saved = reopened.get_record("en-v1:example")
                self.assertIsNotNone(saved)
                self.assertEqual(saved["payload"]["queried_form"], "example")

    def test_offline_cache_miss_never_calls_provider(self):
        provider = FakeProvider()
        with LexicalCache(":memory:") as cache:
            service = ExternalLexicalService(cache=cache, providers=[provider])
            result = service.lookup("missing", offline=True, providers=[provider.provider_id])
            self.assertEqual(result["status"], "cache_miss_offline")
            self.assertEqual(provider.calls, 0)

    def test_candidate_export_is_non_mutating_and_explicit(self):
        provider = FakeProvider()
        with LexicalCache(":memory:") as cache:
            service = ExternalLexicalService(cache=cache, providers=[provider])
            exported = service.export_usg_candidates("example", providers=[provider.provider_id])
            self.assertEqual(exported["contract"], "USG-LEXICAL-CANDIDATES/0.1.0")
            self.assertFalse(exported["promotion_allowed"])
            self.assertEqual(exported["candidates"][0]["promotion_status"], "candidate_only")
            service.close()

    def test_source_disagreement_is_reported_not_merged(self):
        bundle = {
            "sources": [{"provider": "one"}, {"provider": "two"}],
            "entries": [
                {"entry_id": "one", "lemma": "bank", "part_of_speech": "noun", "provider": "one",
                 "senses": [{"sense_id": "one-sense", "definition": "Land beside a river.", "relations": []}]},
                {"entry_id": "two", "lemma": "bank", "part_of_speech": "noun", "provider": "two",
                 "senses": [{"sense_id": "two-sense", "definition": "A financial institution.", "relations": []}]},
            ],
        }
        analysis = analyze_bundle(bundle)
        self.assertEqual(len(analysis["cross_source_disagreements"]), 1)
        self.assertEqual(len(analysis["semantic_candidate_graph"]["nodes"]), 5)
        self.assertIn("no source is selected as authoritative", analysis["cross_source_disagreements"][0]["note"])

    def test_definition_patterns_are_observations_not_validated_facts(self):
        result = classify_definition_pattern("A person who repairs musical instruments.")
        self.assertEqual(result["pattern_type"], "person_who")
        self.assertEqual(result["validation_status"], "unvalidated_observation")
        self.assertEqual(classify_definition_pattern("A type of small mammal.")["pattern_type"], "kind_or_type_of")

    def test_structural_open_world_benchmark_passes(self):
        result = run_structural_benchmark()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["fixture_count"], 5)
        self.assertEqual(result["checks"]["bundle_structural_validation"], "valid")


if __name__ == "__main__":
    unittest.main()
