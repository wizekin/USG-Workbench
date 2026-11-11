import unittest

from tools.phase6_external_pud_v0_7.spacy_english import (
    evaluate_predictions, normalize_english,
)


class TestSpacyEnglishEvaluation(unittest.TestCase):
    def test_normalization_is_case_insensitive(self):
        self.assertEqual(normalize_english("Running"), "running")

    def test_joint_lemma_pos_metrics(self):
        sentences = [{"tokens": [
            {"form": "Dogs", "lemma": "dog", "upos": "NOUN"},
            {"form": "run", "lemma": "run", "upos": "VERB"},
        ]}]
        predictions = [[
            {"lemma": "dog", "upos": "NOUN"},
            {"lemma": "run", "upos": "NOUN"},
        ]]
        result = evaluate_predictions(sentences, predictions)
        self.assertEqual(result["totals"]["tokens"], 2)
        self.assertEqual(result["totals"]["lemma_hits"], 2)
        self.assertEqual(result["totals"]["upos_hits"], 1)
        self.assertEqual(result["totals"]["lemma_upos_hits"], 1)
        self.assertEqual(result["totals"]["lemma_upos_joint_accuracy"], 0.5)
        self.assertEqual(result["totals"]["content_tokens"], 2)
        self.assertEqual(result["totals"]["content_lemma_upos_joint_accuracy"], 0.5)
        self.assertEqual(result["totals"]["nonpunct_lemma_upos_joint_accuracy"], 0.5)

    def test_rejects_token_count_mismatch(self):
        sentences = [{"tokens": [{"form": "word", "lemma": "word", "upos": "NOUN"}]}]
        with self.assertRaises(ValueError):
            evaluate_predictions(sentences, [[]])


if __name__ == "__main__":
    unittest.main()
