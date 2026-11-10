from __future__ import annotations

import unittest

from tools.usg_interpretation_v0_1_0 import (
    LexicalAnalyzer, LexicalEntry, LexicalResource, ingest_source, tokenize,
)


class TokenizerTests(unittest.TestCase):
    def test_exact_spans_for_english_unicode_numbers_and_punctuation(self):
        text = "John's café costs 12.5 USD!"
        source = ingest_source(text, "en")
        tokens = tokenize(source)
        self.assertEqual([x.surface_text for x in tokens],
                         ["John's", "café", "costs", "12", ".", "5", "USD", "!"])
        for token in tokens:
            self.assertEqual(text[token.start:token.end], token.surface_text)

    def test_arabic_diacritics_remain_inside_word_tokens(self):
        text = "زَارَ الجَرّاحُ المريضَ؟"
        source = ingest_source(text, "ar")
        tokens = tokenize(source)
        words = [x.surface_text for x in tokens if x.kind == "WORD"]
        self.assertEqual(words, ["زَارَ", "الجَرّاحُ", "المريضَ"])
        for token in tokens:
            self.assertEqual(text[token.start:token.end], token.surface_text)

    def test_whitespace_is_not_a_token_and_source_is_unchanged(self):
        text = " A\tB\r\nC "
        source = ingest_source(text, "en")
        self.assertEqual([x.surface_text for x in tokenize(source)], ["A", "B", "C"])
        self.assertEqual(source.text, text)

    def test_symbols_and_punctuation_are_distinct(self):
        tokens = tokenize(ingest_source("A😀, B.", "en"))
        self.assertEqual([(x.surface_text, x.kind) for x in tokens], [
            ("A", "WORD"), ("😀", "SYMBOL"), (",", "PUNCTUATION"),
            ("B", "WORD"), (".", "PUNCTUATION")
        ])


class LexicalAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.resource = LexicalResource("fixture-lexicon", 1, (
            LexicalEntry("en", "Apple", "apple", "NOUN", "sense:fruit",
                         (("Number", "Singular"),), "concept:fruit"),
            LexicalEntry("en", "Apple", "Apple", "PROPN", "sense:company",
                         (("Number", "Singular"),), "concept:company"),
            LexicalEntry("ar", "الجَرّاحُ", "جَرّاح", "NOUN", "sense:surgeon",
                         (("Number", "Singular"),), "concept:doctor"),
        ))

    def test_unknown_words_remain_unresolved_without_guessed_lemmas(self):
        result = LexicalAnalyzer(self.resource).analyze(ingest_source("unknown", "en"))
        self.assertEqual(result.tokens[0].status, "UNRESOLVED")
        self.assertEqual(result.tokens[0].candidates, ())

    def test_ambiguous_lexical_senses_are_retained(self):
        result = LexicalAnalyzer(self.resource).analyze(ingest_source("APPLE", "en"))
        item = result.tokens[0]
        self.assertEqual(item.status, "AMBIGUOUS")
        self.assertEqual({x.sense_id for x in item.candidates},
                         {"sense:fruit", "sense:company"})

    def test_unique_english_and_arabic_entries_preserve_morphology(self):
        analyzer = LexicalAnalyzer(self.resource)
        en = analyzer.analyze(ingest_source("Apple", "en"))
        ar = analyzer.analyze(ingest_source("الجَرّاحُ", "ar"))
        self.assertEqual(en.tokens[0].status, "AMBIGUOUS")
        self.assertEqual(ar.tokens[0].status, "RESOLVED")
        self.assertEqual(ar.tokens[0].candidates[0].lemma, "جَرّاح")
        self.assertEqual(ar.tokens[0].candidates[0].morphology, (("Number", "Singular"),))

    def test_non_words_have_not_applicable_status(self):
        result = LexicalAnalyzer(self.resource).analyze(ingest_source("12!", "en"))
        self.assertEqual([x.status for x in result.tokens],
                         ["NOT_APPLICABLE", "NOT_APPLICABLE"])

    def test_resource_rejects_duplicate_entry_identity(self):
        entry = LexicalEntry("en", "cat", "cat", "NOUN", "sense:cat")
        with self.assertRaises(ValueError):
            LexicalResource("bad", 1, (entry, entry))


if __name__ == "__main__":
    unittest.main()
