import unittest

from tools.phase6_spacy_nominal_e2e_v0_1.evaluation import (
    spacy_parse_to_ud_sentence, evaluate_candidate_sets,
)
from tools.phase6_ud_nominal_candidate_v0_1.adapter import adapt_sentence


class TestSpacyNominalEndToEnd(unittest.TestCase):
    def test_preposition_parse_is_converted_to_ud_case_nmod(self):
        sentence = spacy_parse_to_ud_sentence(
            forms=["book", "of", "poems"],
            lemmas=["book", "of", "poem"],
            upos=["NOUN", "ADP", "NOUN"],
            heads=[0, 0, 1],
            deprels=["ROOT", "prep", "pobj"],
            text="book of poems",
        )
        self.assertEqual(
            [token["deprel"] for token in sentence["tokens"]],
            ["root", "case", "nmod"],
        )
        self.assertEqual(
            [token["gold_head_index"] for token in sentence["tokens"]],
            [0, 2, 0],
        )
        adapted = adapt_sentence(sentence, "en")
        self.assertEqual(adapted["candidates"][0]["relation_type"], "GENITIVE_UNSPECIFIED")

    def test_possessive_parse_maps_to_possession_candidate(self):
        sentence = spacy_parse_to_ud_sentence(
            forms=["teacher", "book"],
            lemmas=["teacher", "book"],
            upos=["NOUN", "NOUN"],
            heads=[1, 1],
            deprels=["poss", "ROOT"],
            text="teacher book",
        )
        adapted = adapt_sentence(sentence, "en")
        self.assertEqual(adapted["candidates"][0]["relation_type"], "POSSESSION")


    def test_sentence_identity_prevents_cross_sentence_candidate_collisions(self):
        sentence = {
            "status": "CANDIDATE",
            "candidates": [{
                "status": "CANDIDATE",
                "construction_id": "nominal.attribute_modifier",
                "derivation": {"head_token_id": 2, "dependent_token_id": 1},
                "role_spans": {
                    "HEAD": {"start": 4, "end": 7},
                    "ATTRIBUTE": {"start": 0, "end": 3},
                },
                "grammatical_markers": [],
            }],
        }
        result = evaluate_candidate_sets([sentence, sentence], [sentence, sentence])
        self.assertEqual(result["predicted_candidate_count"], 2)
        self.assertEqual(result["gold_candidate_count"], 2)
        self.assertEqual(result["structural_edge_metrics_ignoring_spans"]["true_positive"], 2)
        self.assertEqual(result["exact_candidate_and_span_metrics"]["true_positive"], 2)
        self.assertEqual(result["exact_span_rate_given_structural_match"], 1.0)

    def test_candidate_metrics_require_exact_structure_and_spans(self):
        sentence = {
            "status": "CANDIDATE",
            "candidates": [{
                "status": "CANDIDATE",
                "construction_id": "nominal.attribute_modifier",
                "derivation": {
                    "head_token_id": 2, "dependent_token_id": 1,
                },
                "role_spans": {
                    "HEAD": {"start": 4, "end": 7},
                    "ATTRIBUTE": {"start": 0, "end": 3},
                },
                "grammatical_markers": [],
            }],
        }
        result = evaluate_candidate_sets([sentence], [sentence])
        self.assertEqual(result["exact_candidate_and_span_metrics"]["precision"], 1.0)
        self.assertEqual(result["exact_candidate_and_span_metrics"]["recall"], 1.0)
        self.assertEqual(result["exact_span_rate_given_structural_match"], 1.0)


if __name__ == "__main__":
    unittest.main()
