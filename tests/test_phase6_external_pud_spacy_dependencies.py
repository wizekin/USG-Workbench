import unittest

from tools.phase6_external_pud_v0_8.spacy_dependencies import (
    evaluate_predictions, parse_dependency_conllu, convert_heads_to_ud_conventions,
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
            {"form": "Cats", "upos": "NOUN", "deprel": "nsubj", "gold_head_index": 1, "is_root": False},
            {"form": "run", "upos": "VERB", "deprel": "root", "gold_head_index": 1, "is_root": True},
        ]}]
        predictions = [[{"head_index": 1}, {"head_index": 1}]]
        result = evaluate_predictions(sentences, predictions)
        self.assertEqual(result["totals"]["tokens"], 2)
        self.assertEqual(result["totals"]["uas_hits"], 2)
        self.assertEqual(result["totals"]["raw_uas"], 1.0)
        self.assertEqual(result["totals"]["converted_uas"], 1.0)
        self.assertEqual(result["totals"]["root_tokens"], 1)
        self.assertEqual(result["totals"]["root_attachment_accuracy"], 1.0)


    def test_preposition_arcs_are_reoriented_to_ud_head_convention(self):
        heads = [1, 1, 2, 1]
        deprels = ["nsubj", "ROOT", "prep", "pobj"]
        self.assertEqual(
            convert_heads_to_ud_conventions(heads, deprels),
            [1, 1, 3, 1],
        )

    def test_coordination_cc_attaches_to_following_conjunct(self):
        heads = [0, 0, 0]
        deprels = ["ROOT", "cc", "conj"]
        self.assertEqual(
            convert_heads_to_ud_conventions(heads, deprels),
            [0, 2, 0],
        )

    def test_rejects_token_count_mismatch(self):
        sentences = [{"tokens": [{"form": "word", "upos": "NOUN", "deprel": "root", "gold_head_index": 0, "is_root": True}]}]
        with self.assertRaises(ValueError):
            evaluate_predictions(sentences, [[]])


if __name__ == "__main__":
    unittest.main()
