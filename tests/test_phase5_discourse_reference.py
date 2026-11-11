"""Phase 5 multi-sentence discourse and conservative reference tests."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0 import (
    LexicalAnalyzer, bundled_lexical_resource_v0_3_0,
    segment_document, DiscourseAnalyzer,
)


class Phase5DiscourseReferenceTests(unittest.TestCase):
    def setUp(self):
        self.lexical = LexicalAnalyzer(bundled_lexical_resource_v0_3_0())

    def analyze(self, text, language, **limits):
        source = ingest_source(text, language)
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        result = DiscourseAnalyzer(**limits).analyze(lexical, segmented)
        return source, lexical, segmented, result

    def test_plural_english_pronoun_retains_matching_prior_mention(self):
        _, _, _, result = self.analyze("Ada writes reports. They read code.", "en")
        pronoun = next(x for x in result.mentions if x.surface_text == "They")
        candidates = [x for x in result.reference_candidates
                      if x.pronoun_mention_ref == pronoun.mention_id]
        self.assertEqual(len(candidates), 1)
        antecedent = next(x for x in result.mentions if x.mention_id == candidates[0].antecedent_mention_ref)
        self.assertEqual(antecedent.surface_text, "reports")
        self.assertEqual(candidates[0].status, "CANDIDATE")
        self.assertEqual(result.status, "CANDIDATES_AVAILABLE")

    def test_singular_pronoun_keeps_multiple_antecedents_ambiguous(self):
        _, _, _, result = self.analyze("Ada writes code. It reads reports.", "en")
        pronoun = next(x for x in result.mentions if x.surface_text == "It")
        candidates = [x for x in result.reference_candidates
                      if x.pronoun_mention_ref == pronoun.mention_id]
        self.assertEqual({next(m.surface_text for m in result.mentions
                               if m.mention_id == x.antecedent_mention_ref) for x in candidates},
                         {"Ada", "code"})
        self.assertEqual(result.status, "AMBIGUOUS")

    def test_gendered_pronoun_without_gender_evidence_remains_unresolved(self):
        _, _, _, result = self.analyze("Ada writes code. She reads reports.", "en")
        pronoun = next(x for x in result.mentions if x.surface_text == "She")
        self.assertIn(pronoun.mention_id, result.unresolved_pronoun_mention_refs)
        self.assertFalse(any(x.pronoun_mention_ref == pronoun.mention_id
                             for x in result.reference_candidates))
        self.assertEqual(result.status, "PARTIAL")

    def test_arabic_plural_pronoun_uses_number_and_gender_compatibility(self):
        _, _, _, result = self.analyze("الكتب وصلت. هم قرأوا الرسائل.", "ar")
        pronoun = next(x for x in result.mentions if x.surface_text == "هم")
        candidates = [x for x in result.reference_candidates
                      if x.pronoun_mention_ref == pronoun.mention_id]
        self.assertEqual(len(candidates), 1)
        antecedent = next(x for x in result.mentions if x.mention_id == candidates[0].antecedent_mention_ref)
        self.assertEqual(antecedent.surface_text, "الكتب")

    def test_sentence_initial_discourse_markers_link_adjacent_sentences(self):
        examples = (
            ("Ada writes reports. Then Mira reads code.", "en", "TEMPORAL_SEQUENCE", "Then"),
            ("كتب الطالب الرسالة. ثم قرأ المعلم الكتاب.", "ar", "TEMPORAL_SEQUENCE", "ثم"),
            ("Ada writes reports. However Mira reads code.", "en", "CONTRAST", "However"),
        )
        for text, language, relation, marker in examples:
            source, _, segmented, result = self.analyze(text, language)
            link = next(x for x in result.relations if x.marker_text == marker)
            self.assertEqual(link.relation, relation)
            self.assertEqual(source.text[slice(*link.marker_span)], marker)
            self.assertEqual(link.source_sentence_ref, segmented.sentences[0].segment_id)
            self.assertEqual(link.target_sentence_ref, segmented.sentences[1].segment_id)
            self.assertEqual(link.status, "CANDIDATE")

    def test_reference_candidates_do_not_merge_or_resolve_mention_identity(self):
        _, _, _, result = self.analyze("Ada writes reports. They read code.", "en")
        self.assertEqual(len(result.mentions), 4)
        self.assertEqual(len({x.mention_id for x in result.mentions}), 4)
        self.assertTrue(all(x.status == "CANDIDATE" for x in result.reference_candidates))

    def test_candidate_budget_is_explicit(self):
        _, _, _, result = self.analyze(
            "Ada writes code. It reads reports.", "en", max_candidates_per_pronoun=1
        )
        self.assertEqual(result.status, "INCOMPLETE_RESOURCE_LIMIT")
        self.assertEqual(len(result.reference_candidates), 1)

    def test_artifacts_from_different_sources_are_rejected(self):
        source = ingest_source("Ada writes code.", "en")
        other = ingest_source("Mira reads reports.", "en")
        lexical = self.lexical.analyze(source)
        segmented = segment_document(self.lexical.analyze(other))
        with self.assertRaises(ValueError):
            DiscourseAnalyzer().analyze(lexical, segmented)


if __name__ == "__main__":
    unittest.main()
