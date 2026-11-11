import unittest

from tools.phase6_external_pud_v0_8.spacy_dependencies import (
    evaluate_predictions, parse_dependency_conllu,
)


class TestSpacyDependencyEvaluation(unittest.TestCase):
    def test_parser_preserves_gold_head_indices(self):
        payload = (
            "# sent_id = s1\n"
            "1\tCats\tcat\tNOUN\t_\tNumber=Plur\t2\tnsubj\t_\t_\n"
            "2\trun\trun\tVERB\t_\tVerbForm=Fin\t0\troot\t_\t_\n\n"
        ).encode()
        parsed = parse_dependency_conllu(payload)
        self.assertEqual(parsed[0]["tokens"][0]["gold_head_index"], 1)
        self.assertEqual(parsed[0]["tokens"][1]["gold_head_index"], 1)
        self.assertTrue(parsed[0]["tokens"][1]["is_root"])

    def test_unlabeled_attachment_accuracy(self):
        sentences = [{"tokens": [
            {"form": "Cats", "upos": "NOUN", "deprel": "nsubj", "gold_head_index": 1},
            {"form": "run", "upos": "VERB", "deprel": "root", "gold_head_index": 1},
        ]}]
        predictions = [[{"head_index": 1}, {"head_index": 1}]]
        result = evaluate_predictions(sentences, predictions)
        self.assertEqual(result["totals"]["tokens"], 2)
        self.assertEqual(result["totals"]["uas_hits"], 2)
        self.assertEqual(result["totals"]["uas"], 1.0)
        self.assertEqual(result["totals"]["root_tokens"], 1)
        self.assertEqual(result["totals"]["root_attachment_accuracy"], 1.0)

    def test_rejects_token_count_mismatch(self):
        sentences = [{"tokens": [{"form": "word", "upos": "NOUN", "deprel": "root", "gold_head_index": 0}]}]
        with self.assertRaises(ValueError):
            evaluate_predictions(sentences, [[]])


if __name__ == "__main__":
    unittest.main()
