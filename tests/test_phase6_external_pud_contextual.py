import unittest
from types import SimpleNamespace

from tools.phase6_external_pud_v0_6.contextual import (
    AveragedStructuredPerceptron, _best_for_upos, token_features,
    prepare_sentences,
)


class TestContextualMorphology(unittest.TestCase):
    def test_token_features_include_context_and_morphology(self):
        tokens = [{"form": "الكتاب"}, {"form": "قرأ"}, {"form": "الطالب"}]
        analyses = [
            [{"analysis": {"lex": "كتاب", "ud": "NOUN", "gen": "m"}}],
            [{"analysis": {"lex": "قرأ", "ud": "VERB", "asp": "p"}}],
            [{"analysis": {"lex": "طالب", "ud": "NOUN", "num": "s"}}],
        ]
        features = token_features(tokens, analyses, 1)
        self.assertIn("W-1=الكتاب", features)
        self.assertIn("W+1=الطالب", features)
        self.assertIn("CAMEL_UD=VERB", features)
        self.assertIn("CAMEL_ASP=p", features)

    def test_structured_perceptron_learns_simple_context(self):
        samples = [
            {"features": [("W=هو",), ("W=قرأ",), ("W=كتاب",)], "gold": ["PRON", "VERB", "NOUN"]},
            {"features": [("W=هي",), ("W=كتبت",), ("W=رسالة",)], "gold": ["PRON", "VERB", "NOUN"]},
            {"features": [("W=ال",), ("W=بيت",)], "gold": ["DET", "NOUN"]},
        ]
        model = AveragedStructuredPerceptron(epochs=8).fit(samples)
        self.assertEqual(model.predict(samples[0]["features"]), samples[0]["gold"])
        self.assertEqual(model.predict(samples[1]["features"]), samples[1]["gold"])


    def test_full_analyzer_candidates_are_separate_from_mle_top1(self):
        sentence = {"meta": {"sent_id": "s1"}, "tokens": [
            {"form": "الكتاب", "lemma": "كتاب", "upos": "NOUN"},
        ]}
        class FakeDisambiguator:
            def disambiguate(self, forms):
                return [SimpleNamespace(analyses=[
                    SimpleNamespace(analysis={"lex": "كتاب", "ud": "NOUN"})
                ])]
        class FakeAnalyzer:
            def analyze(self, form):
                return [
                    {"lex": "كتاب", "ud": "NOUN", "pos_lex_logprob": -1},
                    {"lex": "كتب", "ud": "VERB", "pos_lex_logprob": -2},
                ]
        prepared = prepare_sentences([sentence], FakeDisambiguator(), FakeAnalyzer())
        self.assertEqual(len(prepared[0]["analyses"][0]), 2)
        self.assertEqual(prepared[0]["mle_top1"][0]["lex"], "كتاب")


    def test_decoder_is_constrained_by_morphology_pos_candidates(self):
        model = AveragedStructuredPerceptron(epochs=1)
        model.tags = ["NOUN", "VERB"]
        self.assertEqual(
            model.predict([("BIAS",)], candidate_tags=[["VERB"]]),
            ["VERB"],
        )

    def test_candidate_selection_respects_predicted_upos(self):
        candidates = [
            {"analysis": {"lex": "كتب", "ud": "NOUN"}, "pos_lex_logprob": -2, "lex_logprob": -1},
            {"analysis": {"lex": "كتب", "ud": "VERB"}, "pos_lex_logprob": -1, "lex_logprob": -1},
            {"analysis": {"lex": "كتاب", "ud": "NOUN"}, "pos_lex_logprob": -1, "lex_logprob": -1},
        ]
        selected = _best_for_upos(candidates, "NOUN")
        self.assertEqual(selected["analysis"]["lex"], "كتاب")
        self.assertIsNone(_best_for_upos(candidates, "ADJ"))


if __name__ == "__main__":
    unittest.main()
