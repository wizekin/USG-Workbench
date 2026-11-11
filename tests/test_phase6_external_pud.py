import unittest

from tools.phase6_external_pud_v0_1.run import parse_conllu, extract_gold, evaluate


SAMPLE_EN = """# sent_id = sample-1
# text = the bright star
1\tthe\tthe\tDET\tDT\t_\t3\tdet\t3:det\t_
2\tbright\tbright\tADJ\tJJ\t_\t3\tamod\t3:amod\t_
3\tstar\tstar\tNOUN\tNN\t_\t0\troot\t0:root\t_

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

    def test_report_never_claims_precision_or_promotion(self):
        report = evaluate([])
        self.assertFalse(report["precision_measured"])
        self.assertFalse(report["construction_promotion_allowed"])
        self.assertEqual(report["runtime_capability_state"], "CANDIDATE_ONLY")


if __name__ == "__main__":
    unittest.main()
