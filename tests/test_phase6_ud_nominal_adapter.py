import unittest

from tools.phase6_ud_nominal_candidate_v0_1.adapter import (
    adapt_sentence, align_token_spans,
)


class TestUDNominalAdapter(unittest.TestCase):
    def test_english_adjective_modifier_has_exact_source_spans(self):
        sentence = {
            "meta": {"text": "the red car"},
            "tokens": [
                {"id": 1, "form": "the", "upos": "DET", "deprel": "det", "gold_head_index": 2},
                {"id": 2, "form": "red", "upos": "ADJ", "deprel": "amod", "gold_head_index": 2},
                {"id": 3, "form": "car", "upos": "NOUN", "deprel": "root", "gold_head_index": 2},
            ],
        }
        result = adapt_sentence(sentence, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["construction_id"], "nominal.attribute_modifier")
        self.assertEqual(candidate["role_bindings"], {"HEAD": "car", "ATTRIBUTE": "red"})
        self.assertEqual(candidate["role_spans"]["ATTRIBUTE"], {"start": 4, "end": 7})

    def test_english_of_genitive_keeps_semantics_unspecified(self):
        sentence = {
            "meta": {"text": "book of poems"},
            "tokens": [
                {"id": 1, "form": "book", "upos": "NOUN", "deprel": "root", "gold_head_index": 0},
                {"id": 2, "form": "of", "upos": "ADP", "deprel": "case", "gold_head_index": 2},
                {"id": 3, "form": "poems", "upos": "NOUN", "deprel": "nmod", "gold_head_index": 0},
            ],
        }
        result = adapt_sentence(sentence, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["relation_type"], "GENITIVE_UNSPECIFIED")
        self.assertEqual(candidate["semantic_status"], "UNSPECIFIED")
        self.assertEqual(candidate["grammatical_markers"][0]["surface"], "of")

    def test_arabic_unmarked_nmod_is_ambiguous_not_forced_possession(self):
        sentence = {
            "meta": {"text": "كتاب الطالب"},
            "tokens": [
                {"id": 1, "form": "كتاب", "upos": "NOUN", "deprel": "root", "gold_head_index": 0},
                {"id": 2, "form": "الطالب", "upos": "NOUN", "deprel": "nmod", "gold_head_index": 0},
            ],
        }
        result = adapt_sentence(sentence, "ar")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["status"], "AMBIGUOUS")
        self.assertEqual(len(candidate["alternatives"]), 2)
        self.assertTrue(all(item["semantic_status"] == "UNSPECIFIED" for item in candidate["alternatives"]))

    def test_arabic_diacritics_align_to_original_codepoint_spans(self):
        text = "كِتاب الطّالب"
        tokens = [{"id": 1, "form": "كتاب"}, {"id": 2, "form": "الطالب"}]
        spans, failed = align_token_spans(text, tokens, "ar")
        self.assertEqual(failed, [])
        self.assertEqual(text[spans[0]["start"]:spans[0]["end"]], "كِتاب")
        self.assertEqual(text[spans[1]["start"]:spans[1]["end"]], "الطّالب")

    def test_possession_and_compound_have_explicit_role_direction(self):
        possession = {
            "meta": {"text": "the teacher's book"},
            "tokens": [
                {"id": 1, "form": "teacher", "upos": "NOUN", "deprel": "nmod:poss", "gold_head_index": 2},
                {"id": 2, "form": "book", "upos": "NOUN", "deprel": "root", "gold_head_index": 1},
            ],
        }
        result = adapt_sentence(possession, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["role_bindings"], {"POSSESSED": "book", "POSSESSOR": "teacher"})


if __name__ == "__main__":
    unittest.main()
