import unittest

from tools.phase6_external_pud_v0_6.contextual import (
    AveragedStructuredPerceptron, _best_for_upos, token_features,
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
