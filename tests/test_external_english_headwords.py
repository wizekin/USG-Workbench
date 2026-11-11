"""Tests for the external English headword inventory importer."""
import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.usg_lexical_corpus_v0_1_0.import_headwords import (
    SourceFormatError,
    decode_markdown_label,
    iter_markdown_links,
    parse_headword_page,
    parse_initial_index,
    parse_letter_index,
    stable_headword_id,
    import_headwords,
)


class ExternalHeadwordImporterTests(unittest.TestCase):
    def test_markdown_labels_decode_entities_and_escapes(self):
        self.assertEqual(decode_markdown_label("A &amp; B"), "A & B")
        self.assertEqual(decode_markdown_label(r"H\*tler"), "H*tler")
        self.assertEqual(decode_markdown_label(r"Space \[U+0020\]"), "Space [U+0020]")

    def test_markdown_link_parser_handles_nested_and_escaped_labels(self):
        links = list(iter_markdown_links("- [Space [U+0020]](entry.md)\n- [H\\*tler](entry2.md)"))
        self.assertEqual(links, [("Space [U+0020]", "entry.md"), (r"H\*tler", "entry2.md")])

    def test_initial_index_extracts_alphabetical_browse_links(self):
        text = '''---
kind: "dictionary-index"
headwords: 3
---
- [A](browse/a/INDEX.md)
- [Other](browse/_/INDEX.md)
- [Source](SOURCE.md)
'''
        self.assertEqual(
            parse_initial_index(text),
            [("a", "browse/a/INDEX.md"), ("_", "browse/_/INDEX.md")],
        )

    def test_letter_index_extracts_only_numbered_pages(self):
        text = '''---
kind: "alphabetical-letter-index"
snapshot_id: "snap-1"
---
| [1](0001.md) | alpha | beta | 1000 |
| [2](0002.md) | beta | charlie | 12 |
[Source snapshot](../../SOURCE.md)
'''
        self.assertEqual(parse_letter_index(text), ["0001.md", "0002.md"])

    def test_headword_page_preserves_case_spelling_and_entry_provenance(self):
        text = '''---
kind: "alphabetical-headword-page"
snapshot_id: "snap-1"
headwords: 3
---
- [A](../../entries/001/a--one.md)
- [a](../../entries/002/a--two.md)
- [A &amp; B](../../entries/003/a-b--three.md)
[Letter index](INDEX.md)
'''
        rows = parse_headword_page(
            text,
            "dictionary/browse/a/0001.md",
            expected_snapshot_id="snap-1",
            commit_sha="a" * 40,
        )
        self.assertEqual([x["headword_candidate"] for x in rows], ["A", "a", "A & B"])
        self.assertNotEqual(rows[0]["headword_id"], rows[1]["headword_id"])
        self.assertEqual(rows[2]["entry_path"], "dictionary/entries/003/a-b--three.md")
        self.assertIn("/" + "a" * 40 + "/", rows[0]["entry_url"])
        self.assertEqual(rows[0]["lookup_key"], "a")

    def test_snapshot_mismatch_is_rejected(self):
        text = '''---
kind: "alphabetical-headword-page"
snapshot_id: "snap-2"
headwords: 1
---
- [word](../../entries/001/word.md)
'''
        with self.assertRaises(SourceFormatError):
            parse_headword_page(
                text, "dictionary/browse/w/0001.md", expected_snapshot_id="snap-1"
            )

    def test_entry_paths_cannot_escape_source_entries_directory(self):
        text = '''---
kind: "alphabetical-headword-page"
snapshot_id: "snap-1"
headwords: 1
---
- [word](../../../../README.md)
'''
        with self.assertRaises(SourceFormatError):
            parse_headword_page(
                text, "dictionary/browse/w/0001.md", expected_snapshot_id="snap-1"
            )

    def test_import_writes_compressed_inventory_and_manifest_from_one_page(self):
        pages = {
            "dictionary/INDEX.md": '''---
kind: "dictionary-index"
headwords: 2
---
- [A](browse/a/INDEX.md)
''',
            "dictionary/SOURCE.md": '''---
kind: "public-source-snapshot"
snapshot_id: "snap-1"
dump_date: "2026-10-01"
license: "CC-BY-SA-4.0"
---
''',
            "dictionary/browse/a/INDEX.md": '''---
kind: "alphabetical-letter-index"
snapshot_id: "snap-1"
---
| [1](0001.md) | A | atom | 2 |
''',
            "dictionary/browse/a/0001.md": '''---
kind: "alphabetical-headword-page"
snapshot_id: "snap-1"
headwords: 2
---
- [A](../../entries/001/a--one.md)
- [atom](../../entries/002/atom--two.md)
''',
        }
        commit_sha = "a" * 40

        def fake_fetch(url):
            path = url.split("/" + commit_sha + "/", 1)[1]
            return pages[path]

        with TemporaryDirectory() as directory:
            output = Path(directory) / "words.jsonl.gz"
            manifest = import_headwords(
                output=output,
                resolved_commit=commit_sha,
                fetch_text=fake_fetch,
            )
            self.assertTrue(manifest["complete"])
            self.assertEqual(manifest["imported_unique_headword_candidates"], 2)
            with gzip.open(output, "rt", encoding="utf-8") as stream:
                rows = [json.loads(line) for line in stream]
            self.assertEqual([row["headword_candidate"] for row in rows], ["A", "atom"])
            self.assertTrue(output.with_suffix(output.suffix + ".manifest.json").is_file())

    def test_stable_ids_are_deterministic_and_case_sensitive(self):
        self.assertEqual(stable_headword_id("word"), stable_headword_id("word"))
        self.assertNotEqual(stable_headword_id("Word"), stable_headword_id("word"))


if __name__ == "__main__":
    unittest.main()
