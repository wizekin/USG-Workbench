import unittest
from types import SimpleNamespace

from tools.phase6_stanza_nominal_e2e_v0_1.evaluation import (
    stanza_sentence_to_ud, evaluate_parser_outputs, evaluate_candidate_sets,
)


class TestStanzaArabicNominalEvaluation(unittest.TestCase):
    def test_stanza_heads_are_converted_to_zero_based_indices(self):
        sentence = SimpleNamespace(words=[
            SimpleNamespace(id=1, text="كتاب", lemma="كتاب", upos="NOUN", head=0, deprel="root"),
            SimpleNamespace(id=2, text="الطالب", lemma="طالب", upos="NOUN", head=1, deprel="nmod"),
        ])
        result = stanza_sentence_to_ud(sentence, "كتاب الطالب")
        self.assertEqual(result["tokens"][0]["gold_head_index"], 0)
        self.assertEqual(result["tokens"][1]["gold_head_index"], 0)
        self.assertTrue(result["tokens"][0]["is_root"])

    def test_parser_metrics_report_pos_and_uas(self):
        gold = [{"tokens": [
            {"upos": "NOUN", "gold_head_index": 1, "is_root": False},
            {"upos": "VERB", "gold_head_index": 1, "is_root": True},
        ]}]
        predicted = [{"tokens": [
            {"upos": "NOUN", "gold_head_index": 1, "is_root": False},
            {"upos": "VERB", "gold_head_index": 1, "is_root": True},
        ]}]
        result = evaluate_parser_outputs(predicted, gold)["totals"]
        self.assertEqual(result["upos_accuracy"], 1.0)
        self.assertEqual(result["uas"], 1.0)
        self.assertEqual(result["root_attachment_accuracy"], 1.0)

    def test_candidate_metrics_are_sentence_scoped(self):
        candidate = {
            "status": "CANDIDATE",
            "construction_id": "nominal.attribute_modifier",
            "derivation": {"head_token_id": 2, "dependent_token_id": 1},
            "role_spans": {
                "HEAD": {"start": 4, "end": 7},
                "ATTRIBUTE": {"start": 0, "end": 3},
            },
            "grammatical_markers": [],
        }
        sentence = {"candidates": [candidate]}
        result = evaluate_candidate_sets([sentence, sentence], [sentence, sentence])
        self.assertEqual(result["exact_candidate_and_span_metrics"]["true_positive"], 2)


if __name__ == "__main__":
    unittest.main()
