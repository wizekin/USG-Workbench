"""Conservative clause-local contextual lexical ranking tests."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0.contextual_lexical import ContextualLexicalRanker
from tools.usg_interpretation_v0_2_0.lexical import (
    LexicalAnalyzer, bundled_lexical_resource_v0_5_0,
)
from tools.usg_interpretation_v0_2_0.segmentation import segment_document


class ContextualLexicalRankerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexical = LexicalAnalyzer(bundled_lexical_resource_v0_5_0())
        cls.ranker = ContextualLexicalRanker()

    def analyze(self, text):
        source = ingest_source(text, "en")
        lexical = self.lexical.analyze(source)
        segmented = segment_document(lexical)
        return self.ranker.analyze(lexical, segmented)

    def test_determiner_context_ranks_plural_noun_above_verb(self):
        result = self.analyze("The changes are physical.")
        item = next(x for x in result.tokens if x.token.surface_text == "changes")
        self.assertEqual(item.status, "SELECTED")
        self.assertEqual(item.selected_candidate.part_of_speech, "NOUN")
        self.assertIn("LEFT_DETERMINER_SUPPORTS_NOUN",
                      item.candidates[0].evidence)

    def test_pronoun_and_object_context_rank_finite_verb(self):
        result = self.analyze("It changes matter.")
        item = next(x for x in result.tokens if x.token.surface_text == "changes")
        self.assertEqual(item.status, "SELECTED")
        self.assertEqual(item.selected_candidate.part_of_speech, "VERB")
        evidence = set(item.candidates[0].evidence)
        self.assertIn("LEFT_NOMINAL_SUPPORTS_VERB", evidence)
        self.assertIn("RIGHT_NOMINAL_SUPPORTS_TRANSITIVE_VERB", evidence)

    def test_context_does_not_collapse_two_noun_senses(self):
        result = self.analyze("The bank changes.")
        item = next(x for x in result.tokens if x.token.surface_text == "bank")
        self.assertEqual(item.status, "AMBIGUOUS")
        self.assertIsNone(item.selected_candidate)
        self.assertEqual(
            {x.candidate.sense_id for x in item.candidates},
            {"en:noun.bank.financial", "en:noun.bank.river"},
        )

    def test_unresolved_words_are_never_created_or_promoted(self):
        result = self.analyze("The flarble changes.")
        item = next(x for x in result.tokens if x.token.surface_text == "flarble")
        self.assertEqual(item.status, "UNRESOLVED")
        self.assertEqual(item.candidates, ())

    def test_context_does_not_leak_across_clause_boundaries(self):
        result = self.analyze("The changes are physical. It changes matter.")
        items = [x for x in result.tokens if x.token.surface_text == "changes"]
        self.assertEqual([x.status for x in items], ["SELECTED", "SELECTED"])
        self.assertEqual([x.selected_candidate.part_of_speech for x in items],
                         ["NOUN", "VERB"])

    def test_mismatched_source_artifacts_are_rejected(self):
        source_a = ingest_source("The changes are physical.", "en")
        source_b = ingest_source("It changes matter.", "en")
        lexical = self.lexical.analyze(source_a)
        segmented = segment_document(self.lexical.analyze(source_b))
        with self.assertRaises(ValueError):
            self.ranker.analyze(lexical, segmented)


if __name__ == "__main__":
    unittest.main()
