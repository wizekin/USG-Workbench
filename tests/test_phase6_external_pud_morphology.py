import unittest

from tools.phase6_external_pud_v0_4.morphology import (
    _features, _rule_for, analyze_token, cross_validate, parse_morph_conllu,
)


class TestPUDMorphology(unittest.TestCase):
    def test_parse_preserves_lemma_pos_and_features(self):
        payload = (
            "# sent_id = x\n"
            "1\tcats\tcat\tNOUN\t_\tNumber=Plur\t0\troot\t_\t_\n\n"
        ).encode()
        parsed = parse_morph_conllu(payload)
        self.assertEqual(parsed[0]["tokens"][0]["lemma"], "cat")
        self.assertEqual(parsed[0]["tokens"][0]["feats"], (("Number", "Plur"),))

    def test_prefix_rule_generates_arabic_lemma_candidate(self):
        rule = ("NOUN", "prefix", "", "ال", (("Definite", "Def"),))
        candidates = analyze_token("الكتاب", "ar", {rule: 4})
        self.assertIn(("كتاب", "NOUN", (("Definite", "Def"),), "MORPHOLOGY_RULE"), candidates)

    def test_suffix_rule_generates_english_plural_candidate(self):
        rule = ("NOUN", "suffix", "", "s", (("Number", "Plur"),))
        candidates = analyze_token("books", "en", {rule: 4})
        self.assertIn(("book", "NOUN", (("Number", "Plur"),), "MORPHOLOGY_RULE"), candidates)

    def test_consonant_doubling_rule_is_stem_conditioned(self):
        token = {"form": "running", "lemma": "run", "upos": "VERB", "feats": (("VerbForm", "Ger"),)}
        rule = _rule_for(token, "en")
        self.assertEqual(rule[2:], ("n", "nning", (("VerbForm", "Ger"),)))
        candidates = analyze_token("running", "en", {rule: 3})
        self.assertIn(("run", "VERB", (("VerbForm", "Ger"),), "MORPHOLOGY_RULE"), candidates)
        self.assertNotIn(("walk", "VERB", (("VerbForm", "Ger"),), "MORPHOLOGY_RULE"), candidates)


    def test_morphology_candidates_require_registered_lemma_when_lexicon_supplied(self):
        rule = ("NOUN", "suffix", "", "s", (("Number", "Plur"),))
        rules = {rule: 5}
        self.assertEqual(
            analyze_token("books", "en", rules, {("book", "NOUN")}),
            {("book", "NOUN", (("Number", "Plur"),), "MORPHOLOGY_RULE")},
        )
        self.assertEqual(analyze_token("cars", "en", rules, {("book", "NOUN")}), set())

    def test_internal_stem_change_is_not_guessed(self):
        token = {"form": "went", "lemma": "go", "upos": "VERB", "feats": (("Tense", "Past"),)}
        self.assertIsNone(_rule_for(token, "en"))

    def test_feature_parser_is_stable(self):
        self.assertEqual(_features("Tense=Past|Number=Sing"), (("Number", "Sing"), ("Tense", "Past")))
        self.assertEqual(_features("_"), ())

    def test_cross_validation_reports_oov_and_candidate_metrics(self):
        sentences = [
            {"meta": {"sent_id": "a"}, "tokens": [{"form": "cats", "lemma": "cat", "upos": "NOUN", "feats": (("Number", "Plur"),)}]},
            {"meta": {"sent_id": "b"}, "tokens": [{"form": "cats", "lemma": "cat", "upos": "NOUN", "feats": (("Number", "Plur"),)}]},
            {"meta": {"sent_id": "c"}, "tokens": [{"form": "cat", "lemma": "cat", "upos": "NOUN", "feats": (("Number", "Sing"),)}]},
            {"meta": {"sent_id": "d"}, "tokens": [{"form": "cat", "lemma": "cat", "upos": "NOUN", "feats": (("Number", "Sing"),)}]},
        ]
        report = cross_validate(sentences, "en", folds=2)
        self.assertEqual(report["totals"]["tokens"], 4)
        self.assertIn("morphology_rescue", report["totals"])
        self.assertIn("lemma_pos_candidate_recall", report["totals"])


if __name__ == "__main__":
    unittest.main()
