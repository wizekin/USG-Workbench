"""Tokenization contract tests for English and MSA Arabic."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_1_0.lexical import tokenize


class TokenizationNormalizationTests(unittest.TestCase):
    def assert_exact_spans(self, text, language):
        source = ingest_source(text, language)
        tokens = tokenize(source)
        for token in tokens:
            self.assertEqual(text[token.start:token.end], token.surface_text)
        return tokens

    def test_contractions_are_preserved_without_expansion(self):
        text = "doesn't don’t"
        tokens = self.assert_exact_spans(text, "en")
        self.assertEqual([(x.surface_text, x.kind) for x in tokens], [
            ("doesn't", "WORD"), ("don’t", "WORD")
        ])

    def test_hyphenated_compounds_remain_separate_surface_units(self):
        text = "electron-cloud"
        tokens = self.assert_exact_spans(text, "en")
        self.assertEqual([(x.surface_text, x.kind) for x in tokens], [
            ("electron", "WORD"), ("-", "PUNCTUATION"), ("cloud", "WORD")
        ])

    def test_scientific_notation_boundaries_are_explicit(self):
        text = "CO₂ ΔG 1.5"
        tokens = self.assert_exact_spans(text, "en")
        self.assertEqual([(x.surface_text, x.kind) for x in tokens], [
            ("CO", "WORD"), ("₂", "NUMBER"), ("ΔG", "WORD"),
            ("1", "NUMBER"), (".", "PUNCTUATION"), ("5", "NUMBER")
        ])

    def test_arabic_diacritics_and_question_mark_keep_exact_spans(self):
        text = "زَارَ الجَرّاحُ المريضَ؟"
        tokens = self.assert_exact_spans(text, "ar")
        self.assertEqual([x.surface_text for x in tokens if x.kind == "WORD"],
                         ["زَارَ", "الجَرّاحُ", "المريضَ"])
        self.assertEqual(tokens[-1].surface_text, "؟")
        self.assertEqual(tokens[-1].kind, "PUNCTUATION")

    def test_offsets_are_unicode_code_point_offsets(self):
        text = "café زَارَ"
        tokens = self.assert_exact_spans(text, "en")
        self.assertEqual(tokens[0].start, 0)
        self.assertEqual(tokens[0].end, 4)
        self.assertEqual(text[tokens[1].start:tokens[1].end], "زَارَ")


if __name__ == "__main__":
    unittest.main()
