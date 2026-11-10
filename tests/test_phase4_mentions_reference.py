import unittest

from tools.usg_interpretation_v0_1_0 import LexicalAnalyzer, LexicalEntry, LexicalResource, MentionAnalyzer, ingest_source


class MentionReferenceTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = LexicalAnalyzer(LexicalResource("mentions", 1, (
            LexicalEntry("en", "Ada", "Ada", "PROPN", "person:ada"),
            LexicalEntry("en", "she", "she", "PRON", "pronoun:she"),
            LexicalEntry("en", "code", "code", "NOUN", "concept:code"),
            LexicalEntry("en", "writes", "write", "VERB", "verb:write"),
        )))

    def test_extracts_nominal_proper_and_pronoun_mentions_with_exact_spans(self):
        source = ingest_source("Ada writes code. She writes code.", "en")
        lexical = self.analyzer.analyze(source)
        result = MentionAnalyzer().analyze(lexical)
        self.assertEqual([x.mention_type for x in result.mentions],
                         ["PROPER", "NOMINAL", "PRONOUN", "NOMINAL"])
        for mention in result.mentions:
            self.assertEqual(source.text[mention.start:mention.end], mention.surface_text)

    def test_repeated_form_is_only_a_candidate_not_identity(self):
        source = ingest_source("Ada writes code. Ada writes code.", "en")
        result = MentionAnalyzer().analyze(self.analyzer.analyze(source))
        self.assertEqual(len(result.referent_candidates), 2)
        self.assertTrue(all(x.status == "CANDIDATE" for x in result.referent_candidates))
        self.assertEqual(result.unresolved_mention_ids, tuple(x.mention_id for x in result.mentions))

    def test_unknown_tokens_do_not_create_mentions(self):
        source = ingest_source("Unknown writes code.", "en")
        result = MentionAnalyzer().analyze(self.analyzer.analyze(source))
        self.assertEqual([x.surface_text for x in result.mentions], ["writes"] if False else ["code"])
        self.assertEqual(result.referent_candidates, ())


if __name__ == "__main__":
    unittest.main()
