import unittest

from tools.phase6_external_pud_v0_3.hmm import train_hmm, viterbi, evaluate_fold


class TestPUDHMM(unittest.TestCase):
    def test_viterbi_returns_one_valid_tag_per_token(self):
        train = [
            {"tokens": [{"form": "the", "upos": "DET"}, {"form": "cat", "upos": "NOUN"}]},
            {"tokens": [{"form": "a", "upos": "DET"}, {"form": "dog", "upos": "NOUN"}]},
            {"tokens": [{"form": "run", "upos": "VERB"}, {"form": "fast", "upos": "ADV"}]},
        ]
        model = train_hmm(train, "en")
        result = viterbi(["the", "cat"], "en", model)
        self.assertEqual(len(result), 2)
        self.assertTrue(set(result).issubset(set(model["tags"])))

    def test_oov_sequence_is_handled_without_crashing(self):
        train = [{"tokens": [{"form": "known", "upos": "NOUN"}]}]
        model = train_hmm(train, "en")
        self.assertEqual(len(viterbi(["unseen", "word"], "en", model)), 2)

    def test_fold_evaluation_reports_both_baselines(self):
        train = [
            {"tokens": [{"form": "the", "upos": "DET"}, {"form": "cat", "upos": "NOUN"}]},
            {"tokens": [{"form": "a", "upos": "DET"}, {"form": "dog", "upos": "NOUN"}]},
        ]
        test = [{"tokens": [{"form": "the", "upos": "DET"}, {"form": "dog", "upos": "NOUN"}]}]
        report = evaluate_fold(train, test, "en")
        self.assertEqual(report["tokens"], 2)
        self.assertIn("hmm_correct", report)
        self.assertIn("unigram_correct", report)


if __name__ == "__main__":
    unittest.main()
