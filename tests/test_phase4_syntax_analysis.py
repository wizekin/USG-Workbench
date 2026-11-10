import unittest

from tools.usg_interpretation_v0_1_0 import (
    GrammarAnalyzer, LexicalAnalyzer, LexicalEntry, LexicalResource,
    initial_grammar_registry, ingest_source,
)


class SyntaxAnalysisTests(unittest.TestCase):
    def setUp(self):
        entries = (
            LexicalEntry("en", "Ada", "Ada", "PROPN", "en:ada"),
            LexicalEntry("en", "writes", "write", "VERB", "en:write"),
            LexicalEntry("en", "code", "code", "NOUN", "en:code"),
            LexicalEntry("ar", "كتب", "كتب", "VERB", "ar:write"),
            LexicalEntry("ar", "الطالب", "طالب", "NOUN", "ar:student"),
            LexicalEntry("ar", "الدرس", "درس", "NOUN", "ar:lesson"),
        )
        self.lex = LexicalAnalyzer(LexicalResource("syntax-fixture", 1, entries))
        self.parser = GrammarAnalyzer(initial_grammar_registry())

    def test_english_svo_pattern(self):
        lexical = self.lex.analyze(ingest_source("Ada writes code", "en"))
        result = self.parser.analyze(lexical)
        self.assertEqual(result.status, "PARSED")
        self.assertEqual(result.candidates[0].pattern_id, "en.svo.v1")
        self.assertEqual(dict(result.candidates[0].roles)["SUBJECT"], ("t0",))
        self.assertEqual(dict(result.candidates[0].roles)["OBJECT"], ("t2",))

    def test_arabic_vso_pattern(self):
        lexical = self.lex.analyze(ingest_source("كتب الطالب الدرس", "ar"))
        result = self.parser.analyze(lexical)
        self.assertEqual(result.status, "PARSED")
        self.assertEqual(result.candidates[0].pattern_id, "ar.vso.v1")

    def test_unknown_word_abstains_instead_of_guessing(self):
        lexical = self.lex.analyze(ingest_source("Ada invents code", "en"))
        result = self.parser.analyze(lexical)
        self.assertEqual(result.status, "INCOMPLETE")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.unresolved_token_ids, ("t1",))

    def test_unregistered_construction_is_unsupported(self):
        lexical = self.lex.analyze(ingest_source("Ada writes", "en"))
        self.assertEqual(self.parser.analyze(lexical).status, "UNSUPPORTED")

    def test_registry_rejects_duplicate_pattern_ids(self):
        from tools.usg_interpretation_v0_1_0.syntax import GrammarRegistry, initial_grammar_registry
        registry = initial_grammar_registry()
        with self.assertRaises(ValueError):
            GrammarRegistry("duplicate", 1, (registry.patterns[0], registry.patterns[0]))


if __name__ == "__main__":
    unittest.main()
