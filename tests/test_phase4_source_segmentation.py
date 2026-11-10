from __future__ import annotations

import hashlib
import unittest

from tools.usg_interpretation_v0_1_0 import ingest_source, segment_source


class SourceIngestionTests(unittest.TestCase):
    def test_exact_source_and_hash_are_preserved(self):
        text = "  A\r\nB.  \n\n  جَرّاحٌ\t"
        source = ingest_source(text, "ar", source_id="src:test")
        self.assertEqual(source.text, text)
        self.assertEqual(source.sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(source.language_profile, "ar-msa-written/0.1.0")

    def test_rejects_unsupported_language_and_non_string(self):
        with self.assertRaises(ValueError):
            ingest_source("hello", "fr")
        with self.assertRaises(TypeError):
            ingest_source(None, "en")

    def test_rejects_tampered_snapshot_hash(self):
        source = ingest_source("hello", "en")
        from tools.usg_interpretation_v0_1_0.source import SourceSnapshot
        with self.assertRaises(ValueError):
            SourceSnapshot(source.source_id, "changed", "en",
                           "en-standard-written/0.1.0", source.sha256)

    def test_empty_and_whitespace_only_sources_are_preserved(self):
        for text in ("", " \t\r\n "):
            source = ingest_source(text, "en")
            result = segment_source(source)
            self.assertEqual(result.source.text, text)
            self.assertEqual(result.paragraphs, ())
            self.assertEqual(result.sentences, ())
            self.assertEqual(result.clauses, ())


class SegmentationTests(unittest.TestCase):
    def assert_spans_are_exact(self, source, segments):
        for segment in segments:
            self.assertGreaterEqual(segment.start, 0)
            self.assertLess(segment.start, segment.end)
            self.assertLessEqual(segment.end, len(source.text))
            self.assertTrue(source.text[segment.start:segment.end].strip())

    def test_paragraph_sentence_and_clause_hierarchy(self):
        text = "First; part. Second!\r\n\r\nثالث؛ رابع؟"
        source = ingest_source(text, "ar")
        result = segment_source(source)
        self.assertEqual(len(result.paragraphs), 2)
        self.assertEqual(len(result.sentences), 3)
        self.assertEqual(len(result.clauses), 5)
        self.assertEqual(source.text[result.sentences[0].start:result.sentences[0].end],
                         "First; part.")
        self.assertEqual(source.text[result.clauses[0].start:result.clauses[0].end],
                         "First;")
        self.assertEqual(source.text[result.clauses[1].start:result.clauses[1].end],
                         "part.")

    def test_crlf_lf_tabs_punctuation_and_unicode_spans(self):
        text = "A\tB.\r\n\r\nCafe\u0301!\n\n𐐷 ends؟"
        source = ingest_source(text, "en")
        result = segment_source(source)
        for group in (result.paragraphs, result.sentences, result.clauses):
            self.assert_spans_are_exact(source, group)
        for sentence in result.sentences:
            exact = source.text[sentence.start:sentence.end]
            self.assertTrue(exact.endswith((".", "!", "؟")))
        self.assertIn("Cafe\u0301!", [source.text[x.start:x.end] for x in result.sentences])

    def test_unpunctuated_fragments_are_not_dropped(self):
        text = "unfinished fragment\nsecond line"
        source = ingest_source(text, "en")
        result = segment_source(source)
        self.assertEqual(len(result.paragraphs), 1)
        self.assertEqual(len(result.sentences), 1)
        self.assertEqual(source.text[result.sentences[0].start:result.sentences[0].end], text)

    def test_every_child_has_a_valid_parent(self):
        result = segment_source(ingest_source("A.\n\nB;", "en"))
        paragraph_ids = {x.segment_id for x in result.paragraphs}
        sentence_ids = {x.segment_id for x in result.sentences}
        self.assertTrue(all(x.parent_id in paragraph_ids for x in result.sentences))
        self.assertTrue(all(x.parent_id in sentence_ids for x in result.clauses))


if __unit_test__ := (__name__ == "__main__"):
    unittest.main()
