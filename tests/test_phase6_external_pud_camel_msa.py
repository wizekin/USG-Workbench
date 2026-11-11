import unittest

from tools.phase6_external_pud_v0_5.camel_msa import (
    extract_candidates, normalize_arabic, evaluate,
)


class FakeAnalyzer:
    def analyze(self, form):
        return {
            "الكتاب": [
                {"lex": "كِتَاب", "ud": "NOUN"},
                {"lex": "كِتَاب", "ud": "NOUN"},
                {"lex": "كُتُب", "ud": "NOUN"},
            ],
            "قرأ": [{"lex": "قَرَأَ", "ud": "VERB"}],
            "غيرمعروف": [],
        }.get(form, [])


class TestCamelMSAAdapter(unittest.TestCase):
    def test_arabic_normalization_matches_camel_default_map(self):
        self.assertEqual(normalize_arabic("إِلَى"), "الي")
        self.assertEqual(normalize_arabic("الـمَدْرَسَة"), "المدرسه")

    def test_extracts_unique_lemma_upos_candidates(self):
        candidates = extract_candidates([
            {"lex": "كِتَاب", "ud": "NOUN"},
            {"lex": "كِتَاب", "ud": "NOUN"},
            {"lex": "كُتُب", "ud": "NOUN"},
            {"lex": None, "ud": "NOUN"},
            {"lex": "word", "ud": "_"},
        ])
        self.assertEqual(candidates, {("كتاب", "NOUN"), ("كتب", "NOUN")})

    def test_evaluation_reports_coverage_and_ambiguity(self):
        sentences = [{"tokens": [
            {"form": "الكتاب", "lemma": "كتاب", "upos": "NOUN"},
            {"form": "قرأ", "lemma": "قرأ", "upos": "VERB"},
            {"form": "غيرمعروف", "lemma": "شيء", "upos": "NOUN"},
        ]}]
        result = evaluate(sentences, FakeAnalyzer())
        self.assertEqual(result["tokens"], 3)
        self.assertEqual(result["lemma_pos_candidate_hit"], 2)
        self.assertEqual(result["no_analysis_tokens"], 1)
        self.assertEqual(result["ambiguous_tokens"], 1)
        self.assertEqual(result["arabic_script_tokens"], 3)


if __name__ == "__main__":
    unittest.main()
