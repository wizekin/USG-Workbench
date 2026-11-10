import unittest

from tools.usg_interpretation_v0_1_0 import (
    DiscourseAnalyzer, initial_discourse_registry, ingest_source,
    segment_source, LexicalAnalyzer, LexicalResource,
)


class DiscourseTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(LexicalResource("empty-lexicon", 1, ()))
        self.analyzer = DiscourseAnalyzer(initial_discourse_registry())

    def test_explicit_english_contrast_marker_links_adjacent_sentences(self):
        source = ingest_source("First event. However, second event.", "en")
        result = self.analyzer.analyze(segment_source(source), self.lexical.analyze(source))
        self.assertEqual(len(result.links), 1)
        link = result.links[0]
        self.assertEqual(link.relation, "CONTRAST")
        self.assertEqual(link.status, "MARKER_DETECTED")
        self.assertEqual(link.source_sentence_ref, "p0.s0")
        self.assertEqual(link.target_sentence_ref, "p0.s1")
        self.assertEqual(source.text[slice(*link.marker_span)], "However")

    def test_arabic_condition_marker_is_detected_without_truth_claim(self):
        source = ingest_source("حدث أول. إذا حدث ثان.", "ar")
        result = self.analyzer.analyze(segment_source(source), self.lexical.analyze(source))
        self.assertEqual(result.links[0].relation, "CONDITION")
        self.assertEqual(result.links[0].status, "MARKER_DETECTED")

    def test_marker_without_prior_sentence_remains_unresolved(self):
        source = ingest_source("If this happens.", "en")
        result = self.analyzer.analyze(segment_source(source), self.lexical.analyze(source))
        self.assertEqual(result.links[0].status, "UNRESOLVED")
        self.assertIsNone(result.links[0].target_sentence_ref)

    def test_source_mismatch_is_rejected(self):
        left = ingest_source("However.", "en")
        right = ingest_source("However!", "en")
        with self.assertRaises(ValueError):
            self.analyzer.analyze(segment_source(left), self.lexical.analyze(right))


if __name__ == "__main__":
    unittest.main()
