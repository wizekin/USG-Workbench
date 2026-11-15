"""Frozen tests for UD-proxy PUD structural-frequency diagnostics."""
from __future__ import annotations

import unittest

from tools.open_world_evaluation.pud_structural_frequency import (
    CONTRACT,
    parse_conllu_structure,
    summarize_language,
)

CONLLU = """# sent_id = en-1
# text = The scientist who measured the sample published results.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\tscientist\tscientist\tNOUN\tNN\t_\t7\tnsubj\t_\t_
3\twho\twho\tPRON\tWP\t_\t4\tnsubj\t_\t_
4\tmeasured\tmeasure\tVERB\tVBD\t_\t2\tacl:relcl\t_\t_
5\tthe\tthe\tDET\tDT\t_\t6\tdet\t_\t_
6\tsample\tsample\tNOUN\tNN\t_\t4\tobj\t_\t_
7\tpublished\tpublish\tVERB\tVBD\t_\t0\troot\t_\t_
8\tresults\tresult\tNOUN\tNNS\t_\t7\tobj\t_\t_

# sent_id = en-2
# text = The report was approved.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\treport\treport\tNOUN\tNN\t_\t4\tnsubj:pass\t_\t_
3\twas\tbe\tAUX\tVBD\t_\t4\taux:pass\t_\t_
4\tapproved\tapprove\tVERB\tVBN\tVoice=Pass\t0\troot\t_\t_

# sent_id = en-3
# text = The report is useful.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\treport\treport\tNOUN\tNN\t_\t3\tnsubj\t_\t_
3\tuseful\tuseful\tADJ\tJJ\t_\t0\troot\t_\t_
4\tis\tbe\tAUX\tVBZ\t_\t3\tcop\t_\t_

# sent_id = en-4
# text = They said that the test worked.
1\tThey\tthey\tPRON\tPRP\t_\t2\tnsubj\t_\t_
2\tsaid\tsay\tVERB\tVBD\t_\t0\troot\t_\t_
3\tthat\tthat\tSCONJ\tIN\t_\t6\tmark\t_\t_
4\tthe\tthe\tDET\tDT\t_\t5\tdet\t_\t_
5\ttest\ttest\tNOUN\tNN\t_\t6\tnsubj\t_\t_
6\tworked\twork\tVERB\tVBD\t_\t2\tccomp\t_\t_

# sent_id = en-5
# text = They left because it rained.
1\tThey\tthey\tPRON\tPRP\t_\t2\tnsubj\t_\t_
2\tleft\tleave\tVERB\tVBD\t_\t0\troot\t_\t_
3\tbecause\tbecause\tSCONJ\tIN\t_\t5\tmark\t_\t_
4\tit\tit\tPRON\tPRP\t_\t5\tnsubj\t_\t_
5\trained\train\tVERB\tVBD\t_\t2\tadvcl\t_\t_

# sent_id = en-6
# text = The team and the coach agreed.
1\tThe\tthe\tDET\tDT\t_\t2\tdet\t_\t_
2\tteam\tteam\tNOUN\tNN\t_\t6\tnsubj\t_\t_
3\tand\tand\tCCONJ\tCC\t_\t4\tcc\t_\t_
4\tcoach\tcoach\tNOUN\tNN\t_\t2\tconj\t_\t_
5\tthe\tthe\tDET\tDT\t_\t4\tdet\t_\t_
6\tagreed\tagree\tVERB\tVBD\t_\t0\troot\t_\t_

# sent_id = en-7
# text = They read the report.
1\tThey\tthey\tPRON\tPRP\t_\t2\tnsubj\t_\t_
2\tread\tread\tVERB\tVBD\t_\t0\troot\t_\t_
3\tthe\tthe\tDET\tDT\t_\t4\tdet\t_\t_
4\treport\treport\tNOUN\tNN\t_\t2\tobj\t_\t_
"""


class PudStructuralFrequencyTests(unittest.TestCase):
    def test_parser_preserves_sentence_ids_and_skips_multiword_and_empty_nodes(self):
        payload = """# sent_id = s1
# text = Can't stop.
1-2\tCan't\t_\t_\t_\t_\t_\t_\t_\t_
1\tCan\tcan\tAUX\tMD\t_\t2\taux\t_\t_
2\tnot\tnot\tPART\tRB\t_\t3\tadvmod\t_\t_
2.1\tghost\tghost\tX\tXX\t_\t_\t_\t_\t_
3\tstop\tstop\tVERB\tVB\t_\t0\troot\t_\t_
"""
        sentences = parse_conllu_structure(payload)
        self.assertEqual(len(sentences), 1)
        self.assertEqual(sentences[0]["sentence_id"], "s1")
        self.assertEqual([token["id"] for token in sentences[0]["tokens"]], [1, 2, 3])

    def test_construction_counts_keep_sentence_and_instance_denominators_separate(self):
        summary = summarize_language(parse_conllu_structure(CONLLU))
        self.assertEqual(summary["sentence_count"], 7)
        self.assertEqual(summary["token_count"], 37)
        c = summary["constructions"]
        self.assertEqual(c["relative_clause_attachment"]["sentence_count"], 1)
        self.assertEqual(c["relative_clause_attachment"]["instance_count"], 1)
        self.assertEqual(c["active_transitive_root"]["sentence_count"], 2)
        self.assertEqual(c["active_transitive_root"]["instance_count"], 2)
        self.assertEqual(c["passive_root"]["sentence_count"], 1)
        self.assertEqual(c["copular_predicate"]["sentence_count"], 1)
        self.assertEqual(c["clause_complement"]["instance_count"], 1)
        self.assertEqual(c["adverbial_clause"]["instance_count"], 1)
        self.assertEqual(c["coordination"]["instance_count"], 1)
        self.assertAlmostEqual(c["relative_clause_attachment"]["per_1000_sentences"], 1000 / 7)

    def test_passive_root_is_not_counted_as_active_transitive(self):
        summary = summarize_language(parse_conllu_structure(CONLLU))
        self.assertEqual(summary["constructions"]["passive_root"]["instance_count"], 1)
        self.assertEqual(summary["constructions"]["active_transitive_root"]["instance_count"], 2)

    def test_malformed_conllu_rows_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_conllu_structure("1\tbad\trow\n")

    def test_empty_population_is_not_reported_as_zero_frequency(self):
        with self.assertRaises(ValueError):
            summarize_language([])

    def test_report_contract_is_explicitly_syntactic_not_semantic_gold(self):
        self.assertEqual(CONTRACT, "USG-PUD-STRUCTURAL-FREQUENCY/0.1.0")


if __name__ == "__main__":
    unittest.main()
