"""Phase 5 versioned lexical resource and morphology tests."""
import unittest

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0.lexical import (
    LexicalAnalyzer, LexicalEntry, LexicalResource, MorphologyRule,
    bundled_lexical_resource,
)


class Phase5LexicalResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource = bundled_lexical_resource()
        cls.analyzer = LexicalAnalyzer(cls.resource)

    def test_bundled_resource_has_provenance_and_reproducible_digest(self):
        self.assertIn("Project-authored", self.resource.provenance)
        self.assertEqual(self.resource.digest(), self.resource.digest())
        self.assertEqual(len(self.resource.digest()), 64)
        self.assertEqual(self.resource.manifest()["sha256"], self.resource.digest())

    def test_every_positive_benchmark_sentence_has_lexical_candidates(self):
        from tools.phase5_interpretation_benchmark_v0_2_0.run import load_and_validate
        corpus = load_and_validate()
        positives = [x for x in corpus["cases"] if x["gold_class"] == "POSITIVE"]
        for case in positives:
            result = self.analyzer.analyze(ingest_source(case["text"], case["language"]))
            unresolved = [x.token.surface_text for x in result.tokens
                          if x.token.kind == "WORD" and x.status == "UNRESOLVED"]
            self.assertEqual(unresolved, [], case["id"])

    def test_english_third_person_and_plural_rules_are_explicit(self):
        result = self.analyzer.analyze(ingest_source("Mira writes reports.", "en"))
        words = {x.token.surface_text: x for x in result.tokens if x.token.kind == "WORD"}
        verb = words["writes"].candidates[0]
        noun = words["reports"].candidates[0]
        self.assertEqual(verb.lemma, "write")
        self.assertEqual(dict(verb.features)["Person"], "Third")
        self.assertEqual(dict(verb.features)["Tense"], "Present")
        self.assertEqual(noun.lemma, "report")
        self.assertEqual(dict(noun.features)["Number"], "Plural")

    def test_arabic_definite_article_is_a_morphology_candidate_not_source_rewrite(self):
        text = "كتب الطالب الرسالة"
        result = self.analyzer.analyze(ingest_source(text, "ar"))
        student = next(x for x in result.tokens if x.token.surface_text == "الطالب")
        self.assertEqual(student.status, "RESOLVED")
        self.assertEqual(student.candidates[0].lemma, "طالب")
        self.assertEqual(dict(student.candidates[0].features)["Definiteness"], "Definite")
        self.assertEqual(text[student.token.start:student.token.end], "الطالب")

    def test_ambiguous_english_and_arabic_senses_are_retained(self):
        for text, language in (("bank", "en"), ("عين", "ar")):
            item = self.analyzer.analyze(ingest_source(text, language)).tokens[0]
            self.assertEqual(item.status, "AMBIGUOUS")
            self.assertGreaterEqual(len(item.candidates), 2)

    def test_unknown_forms_are_not_guessed(self):
        for text, language in (("flibbertigibbet", "en"), ("كلمةغيرمسجلة", "ar")):
            item = self.analyzer.analyze(ingest_source(text, language)).tokens[0]
            self.assertEqual(item.status, "UNRESOLVED")
            self.assertEqual(item.candidates, ())

    def test_morphology_does_not_infer_a_stem_absent_from_resource(self):
        item = self.analyzer.analyze(ingest_source("cats", "en")).tokens[0]
        self.assertEqual(item.status, "UNRESOLVED")

    def test_language_specific_lookup_does_not_cross_languages(self):
        item = self.analyzer.analyze(ingest_source("bank", "ar")).tokens[0]
        self.assertEqual(item.status, "UNRESOLVED")

    def test_source_offsets_remain_exact_for_diacritics_and_punctuation(self):
        text = "زَارَ الطالبُ، ثم كتب الرسالة."
        result = self.analyzer.analyze(ingest_source(text, "ar"))
        for item in result.tokens:
            self.assertEqual(text[item.token.start:item.token.end], item.token.surface_text)

    def test_duplicate_entry_and_rule_id_are_rejected(self):
        entry = LexicalEntry("en", "cat", "cat", "NOUN", "en:noun.cat")
        with self.assertRaises(ValueError):
            LexicalResource("duplicate", "1.0.0", "test", (entry, entry), ())
        rule = MorphologyRule("r", "en", "suffix", "s", "NOUN", (("Number", "Plural"),))
        with self.assertRaises(ValueError):
            LexicalResource("duplicate-rule", "1.0.0", "test", (entry,), (rule, rule))


if __name__ == "__main__":
    unittest.main()
