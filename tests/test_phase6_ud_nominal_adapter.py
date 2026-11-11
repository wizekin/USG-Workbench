import unittest

from tools.phase6_ud_nominal_candidate_v0_1.adapter import (
    adapt_sentence, align_token_spans, parse_ud_conllu,
)


class TestUDNominalAdapter(unittest.TestCase):

    def test_conllu_parser_preserves_dependency_and_source_text(self):
        payload = (
            "# sent_id = s1\n"
            "# text = red car\n"
            "1\tred\tred\tADJ\t_\t_\t2\tamod\t_\t_\n"
            "2\tcar\tcar\tNOUN\t_\t_\t0\troot\t_\t_\n\n"
        ).encode()
        parsed = parse_ud_conllu(payload)
        self.assertEqual(parsed[0]["meta"]["text"], "red car")
        self.assertEqual(parsed[0]["tokens"][0]["gold_head_index"], 1)
        self.assertEqual(parsed[0]["tokens"][0]["deprel"], "amod")
        self.assertTrue(parsed[0]["tokens"][1]["is_root"])

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


    def test_noun_compound_uses_head_and_compound_modifier_roles(self):
        sentence = {
            "meta": {"text": "school bus"},
            "tokens": [
                {"id": 1, "form": "school", "upos": "NOUN", "deprel": "compound", "gold_head_index": 1},
                {"id": 2, "form": "bus", "upos": "NOUN", "deprel": "root", "gold_head_index": 1},
            ],
        }
        result = adapt_sentence(sentence, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["relation_type"], "NOUN_COMPOUND")
        self.assertEqual(candidate["role_bindings"], {"HEAD": "bus", "COMPOUND_MODIFIER": "school"})

    def test_prepositional_modifier_preserves_case_marker(self):
        sentence = {
            "meta": {"text": "book on the table"},
            "tokens": [
                {"id": 1, "form": "book", "upos": "NOUN", "deprel": "root", "gold_head_index": 0},
                {"id": 2, "form": "on", "upos": "ADP", "deprel": "case", "gold_head_index": 3},
                {"id": 3, "form": "the", "upos": "DET", "deprel": "det", "gold_head_index": 4},
                {"id": 4, "form": "table", "upos": "NOUN", "deprel": "nmod", "gold_head_index": 0},
            ],
        }
        result = adapt_sentence(sentence, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["relation_type"], "PREPOSITIONAL_NOMINAL_MODIFIER")
        self.assertEqual(candidate["role_bindings"]["MODIFIER"], "on the table")
        self.assertEqual(candidate["grammatical_markers"][0]["surface"], "on")

    def test_temporal_adverb_has_modified_head_and_time_roles(self):
        sentence = {
            "meta": {"text": "arrived yesterday"},
            "tokens": [
                {"id": 1, "form": "arrived", "upos": "VERB", "deprel": "root", "gold_head_index": 0},
                {"id": 2, "form": "yesterday", "upos": "ADV", "deprel": "advmod", "gold_head_index": 0},
            ],
        }
        result = adapt_sentence(sentence, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["relation_type"], "TEMPORAL_MODIFIER")
        self.assertEqual(candidate["derivation"]["head_token_id"], 1)
        self.assertEqual(candidate["role_bindings"], {"MODIFIED": "arrived", "TIME": "yesterday"})

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
                {"id": 1, "form": "teacher", "upos": "NOUN", "deprel": "nmod:poss", "gold_head_index": 1},
                {"id": 2, "form": "book", "upos": "NOUN", "deprel": "root", "gold_head_index": 1},
            ],
        }
        result = adapt_sentence(possession, "en")
        candidate = result["candidates"][0]
        self.assertEqual(candidate["role_bindings"], {"POSSESSED": "book", "POSSESSOR": "teacher"})


if __name__ == "__main__":
    unittest.main()
