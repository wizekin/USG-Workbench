import unittest

from tools.phase6_external_pud_v0_1.run import parse_conllu, extract_gold, evaluate


SAMPLE_EN = """# sent_id = sample-1
# text = the bright star
1	the	the	DET	DT	_	3	det	3:det	_
2	bright	bright	ADJ	JJ	_	3	amod	3:amod	_
3	star	star	NOUN	NN	_	0	root	0:root	_

"""

SAMPLE_EN_GENITIVE = """# sent_id = sample-2
# text = book of science
1	book	book	NOUN	NN	_	0	root	0:root	_
2	of	of	ADP	IN	_	3	case	3:case	_
3	science	science	NOUN	NN	_	1	nmod	1:nmod	_

"""


class TestExternalPUDAdapter(unittest.TestCase):
    def test_conllu_parser_keeps_text_and_syntactic_words(self):
        parsed = parse_conllu(SAMPLE_EN.encode("utf-8"))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["meta"]["text"], "the bright star")
        self.assertEqual([t["form"] for t in parsed[0]["tokens"]], ["the", "bright", "star"])

    def test_gold_extraction_comes_from_ud_dependencies(self):
        parsed = parse_conllu(SAMPLE_EN.encode("utf-8"))
        cases = extract_gold(parsed, "en")
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["construction"], "en.nominal.adjective_modifier")
        self.assertEqual(cases[0]["expected_roles"], {"MODIFIER": "bright", "HEAD": "star"})

    def test_of_genitive_is_extracted_from_ud_case_and_nmod(self):
        parsed = parse_conllu(SAMPLE_EN_GENITIVE.encode("utf-8"))
        cases = extract_gold(parsed, "en")
        genitives = [c for c in cases if c["construction"] == "en.genitive.of_phrase"]
        self.assertEqual(len(genitives), 1)
        self.assertEqual(genitives[0]["expected_roles"], {
            "GENITIVE_HEAD": "book", "GENITIVE_DEPENDENT": "science"
        })

    def test_report_never_claims_precision_or_promotion(self):
        report = evaluate([])
        self.assertFalse(report["precision_measured"])
        self.assertFalse(report["construction_promotion_allowed"])
        self.assertEqual(report["runtime_capability_state"], "CANDIDATE_ONLY")


if __name__ == "__main__":
    unittest.main()
