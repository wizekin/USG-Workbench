import unittest
from types import SimpleNamespace

from tools.phase6_stanza_nominal_e2e_v0_1.evaluation import (
    parse_in_batches,
    stanza_sentence_to_ud_sentence,
)


def word(text, upos, head, deprel, lemma=None):
    return SimpleNamespace(
        text=text, upos=upos, head=head, deprel=deprel, lemma=lemma or text
    )


class FakeDocument:
    def __init__(self, sentences):
        self.sentences = [SimpleNamespace(words=items) for items in sentences]


class FakePipeline:
    def __init__(self, parsed_batches):
        self.parsed_batches = iter(parsed_batches)

    def __call__(self, inputs):
        return FakeDocument(next(self.parsed_batches))


class TestStanzaNominalE2E(unittest.TestCase):
    def setUp(self):
        self.gold = {
            "meta": {"text": "الكتاب الجديد"},
            "tokens": [
                {"id": 1, "form": "الكتاب", "lemma": "كتاب", "upos": "NOUN"},
                {"id": 2, "form": "الجديد", "lemma": "جديد", "upos": "ADJ"},
            ],
        }

    def test_predicted_heads_are_converted_to_zero_based_graph(self):
        parsed = SimpleNamespace(words=[
            word("الكتاب", "NOUN", 0, "root", "كتاب"),
            word("الجديد", "ADJ", 1, "amod", "جديد"),
        ])
        result = stanza_sentence_to_ud_sentence(self.gold, parsed)
        self.assertEqual([t["gold_head_index"] for t in result["tokens"]], [0, 0])
        self.assertEqual([t["deprel"] for t in result["tokens"]], ["root", "amod"])
        self.assertEqual(result["meta"]["text"], "الكتاب الجديد")

    def test_pretokenized_word_mismatch_is_rejected(self):
        parsed = SimpleNamespace(words=[
            word("ال", "DET", 2, "det"),
            word("كتاب", "NOUN", 0, "root"),
            word("الجديد", "ADJ", 2, "amod"),
        ])
        with self.assertRaisesRegex(ValueError, "word count changed"):
            stanza_sentence_to_ud_sentence(self.gold, parsed)

    def test_invalid_head_is_rejected(self):
        parsed = SimpleNamespace(words=[
            word("الكتاب", "NOUN", 3, "root"),
            word("الجديد", "ADJ", 1, "amod"),
        ])
        with self.assertRaisesRegex(ValueError, "invalid Stanza head"):
            stanza_sentence_to_ud_sentence(self.gold, parsed)

    def test_batch_parser_records_alignment_failure_and_abstains(self):
        parsed = [[
            word("الكتاب", "NOUN", 0, "root"),
            word("الجديد", "ADJ", 1, "amod"),
        ], [
            word("ال", "DET", 2, "det"),
            word("كتاب", "NOUN", 0, "root"),
            word("الجديد", "ADJ", 2, "amod"),
        ]]
        pipeline = FakePipeline([parsed])
        sentences = [self.gold, self.gold]
        graphs, failures = parse_in_batches(pipeline, sentences, batch_size=2)
        self.assertEqual(failures, 1)
        self.assertEqual(len(graphs[0]["tokens"]), 2)
        self.assertEqual(graphs[1]["tokens"], [])

    def test_batch_size_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "batch_size"):
            parse_in_batches(FakePipeline([]), [self.gold], batch_size=0)


if __name__ == "__main__":
    unittest.main()
