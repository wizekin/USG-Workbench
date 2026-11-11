import unittest

from tools.phase6_external_pud_v0_2.crossval import cross_validate, normalize


class TestPUDPOSCrossValidation(unittest.TestCase):
    def test_language_normalization_is_deterministic(self):
        self.assertEqual(normalize("Apple", "en"), "apple")
        self.assertEqual(normalize("مَدْرَسَة", "ar"), "مَدْرَسَة")

    def test_heldout_sentences_are_not_in_their_fold_lexicon(self):
        sentences = [
            {"tokens": [{"form": "alpha", "upos": "NOUN"}]},
            {"tokens": [{"form": "beta", "upos": "VERB"}]},
        ]
        report = cross_validate(sentences, "en", folds=2)
        self.assertEqual(report["totals"]["tokens"], 2)
        self.assertEqual(report["totals"]["seen_tokens"], 0)
        self.assertEqual(report["totals"]["oov_tokens"], 2)

    def test_repeated_form_contributes_a_pos_candidate(self):
        sentences = [
            {"tokens": [{"form": "run", "upos": "VERB"}]},
            {"tokens": [{"form": "run", "upos": "VERB"}]},
            {"tokens": [{"form": "run", "upos": "NOUN"}]},
            {"tokens": [{"form": "run", "upos": "NOUN"}]},
        ]
        report = cross_validate(sentences, "en", folds=2)
        self.assertEqual(report["totals"]["seen_tokens"], 4)
        self.assertEqual(report["totals"]["gold_tag_in_candidates"], 4)
        self.assertEqual(report["totals"]["ambiguous_seen_tokens"], 4)

    def test_requires_valid_fold_count(self):
        with self.assertRaises(ValueError):
            cross_validate([{"tokens": []}], "en", folds=1)


if __name__ == "__main__":
    unittest.main()
