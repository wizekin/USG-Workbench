"""Phase 5 sentence segmentation and richer syntax tests."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0 import (
    LexicalAnalyzer, bundled_lexical_resource, segment_document, SyntaxAnalyzer,
)


class Phase5SegmentationSyntaxTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(bundled_lexical_resource())

    def analyze(self, text, language):
        lex = self.lexical.analyze(ingest_source(text, language))
        segmented = segment_document(lex)
        syntax = SyntaxAnalyzer().analyze(lex, segmented)
        return lex, segmented, syntax

    def test_simple_english_svo_candidate_has_named_roles(self):
        _, segmented, syntax = self.analyze("Ada writes code.", "en")
        self.assertEqual(len(segmented.sentences), 1)
        self.assertEqual(len(segmented.clauses), 1)
        self.assertEqual(syntax.status, "COMPLETE")
        candidate = syntax.clauses[0].candidates[0]
        self.assertEqual(candidate.construction_id, "en.simple_transitive.svo")
        self.assertEqual(set(dict(candidate.role_token_refs)), {"AGENT", "ACTION", "PATIENT"})

    def test_arabic_vso_and_svo_patterns_are_distinct(self):
        _, _, vso = self.analyze("كتب الطالب الرسالة", "ar")
        _, _, svo = self.analyze("الطالب كتب الرسالة", "ar")
        self.assertEqual(vso.status, "COMPLETE")
        self.assertEqual(svo.status, "COMPLETE")
        self.assertEqual(vso.clauses[0].candidates[0].construction_id, "ar.simple_transitive.vso")
        self.assertEqual(svo.clauses[0].candidates[0].construction_id, "ar.simple_transitive.svo")

    def test_coordination_splits_two_clauses_and_keeps_boundary_relation(self):
        text = "Ada writes code, and Mira reads reports."
        _, segmented, syntax = self.analyze(text, "en")
        self.assertEqual(len(segmented.sentences), 1)
        self.assertEqual(len(segmented.clauses), 2)
        self.assertEqual(segmented.boundaries[0].relation, "COORDINATION_AND")
        self.assertEqual(text[slice(*segmented.boundaries[0].marker_span)], "and")
        self.assertEqual(syntax.status, "COMPLETE")
        self.assertEqual([x.status for x in syntax.clauses], ["RESOLVED", "RESOLVED"])

    def test_subordinate_marker_splits_only_with_verb_evidence_on_both_sides(self):
        text = "Ada writes code because Mira reads reports."
        _, segmented, syntax = self.analyze(text, "en")
        self.assertEqual(len(segmented.clauses), 2)
        self.assertEqual(segmented.boundaries[0].relation, "CAUSE")
        self.assertEqual(syntax.status, "COMPLETE")
        _, no_split, _ = self.analyze("Ada and Mira write code.", "en")
        self.assertEqual(len(no_split.clauses), 1)

    def test_arabic_temporal_marker_splits_clauses(self):
        text = "كتب الطالب الرسالة ثم قرأ المعلم الكتاب"
        _, segmented, syntax = self.analyze(text, "ar")
        self.assertEqual(len(segmented.clauses), 2)
        self.assertEqual(segmented.boundaries[0].relation, "TEMPORAL")
        self.assertEqual(syntax.status, "COMPLETE")

    def test_semicolon_splits_clause_sequence(self):
        text = "Ada writes code; Mira reads reports."
        _, segmented, syntax = self.analyze(text, "en")
        self.assertEqual(len(segmented.clauses), 2)
        self.assertEqual(segmented.boundaries[0].relation, "CLAUSE_SEQUENCE")
        self.assertEqual(syntax.status, "COMPLETE")

    def test_lexical_sense_ambiguity_produces_multiple_syntax_candidates(self):
        _, _, syntax = self.analyze("Ada writes bank.", "en")
        self.assertEqual(syntax.status, "AMBIGUOUS")
        self.assertEqual(len(syntax.clauses[0].candidates), 2)

    def test_unknown_token_makes_clause_incomplete_not_guessed(self):
        _, _, syntax = self.analyze("Ada writes flibbertigibbet.", "en")
        self.assertEqual(syntax.clauses[0].status, "INCOMPLETE")
        self.assertEqual(syntax.status, "PARTIAL")

    def test_known_but_unregistered_order_is_unsupported(self):
        _, _, syntax = self.analyze("Ada code writes.", "en")
        self.assertEqual(syntax.status, "UNSUPPORTED")

    def test_candidate_budget_is_explicit(self):
        lex = self.lexical.analyze(ingest_source("Ada writes bank.", "en"))
        segmented = segment_document(lex)
        result = SyntaxAnalyzer(max_candidates=1).analyze(lex, segmented)
        self.assertEqual(result.status, "INCOMPLETE_RESOURCE_LIMIT")
        self.assertEqual(result.clauses[0].status, "INCOMPLETE_RESOURCE_LIMIT")

    def test_exact_spans_survive_unicode_and_sentence_boundaries(self):
        text = "كتب الطالب الرسالة؟\nMira reads reports."
        lex = self.lexical.analyze(ingest_source(text, "ar"))
        segmented = segment_document(lex)
        for sentence in segmented.sentences:
            self.assertEqual(text[sentence.start:sentence.end], text[sentence.start:sentence.end].strip())
        for clause in segmented.clauses:
            self.assertEqual(text[clause.start:clause.end], text[clause.start:clause.end].strip())
        for item in lex.tokens:
            self.assertEqual(text[item.token.start:item.token.end], item.token.surface_text)

    def test_artifacts_from_different_sources_are_rejected(self):
        lex = self.lexical.analyze(ingest_source("Ada writes code.", "en"))
        other = self.lexical.analyze(ingest_source("Mira reads reports.", "en"))
        segmented = segment_document(other)
        with self.assertRaises(ValueError):
            SyntaxAnalyzer().analyze(lex, segmented)


if __name__ == "__main__":
    unittest.main()
