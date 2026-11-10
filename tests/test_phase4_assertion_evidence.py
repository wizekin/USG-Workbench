import unittest

from tools.usg_interpretation_v0_1_0 import (
    GrammarAnalyzer, LexicalAnalyzer, LexicalEntry, LexicalResource,
    SemanticComposer, initial_grammar_registry, initial_semantic_frame_registry,
    ingest_source, project_assertions_and_evidence,
)


class AssertionEvidenceTests(unittest.TestCase):
    def setUp(self):
        lexicon = LexicalResource("assertion-fixture", 1, (
            LexicalEntry("en", "Ada", "Ada", "PROPN", "en:ada"),
            LexicalEntry("en", "writes", "write", "VERB", "en:write"),
            LexicalEntry("en", "code", "code", "NOUN", "en:code"),
        ))
        self.lexical = LexicalAnalyzer(lexicon)
        self.grammar = GrammarAnalyzer(initial_grammar_registry())
        self.composer = SemanticComposer(initial_semantic_frame_registry())

    def test_exact_quote_is_not_promoted_to_truth_or_author_commitment(self):
        source = ingest_source("Ada writes code.", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        composition = self.composer.compose(lexical, syntax)
        result = project_assertions_and_evidence(source, composition)
        self.assertEqual(len(result.assertions), 1)
        self.assertEqual(len(result.evidence), 1)
        assertion, evidence = result.assertions[0], result.evidence[0]
        self.assertEqual(assertion["epistemicStatus"], "UNKNOWN")
        self.assertEqual(assertion["commitment"], "NONE")
        self.assertEqual(assertion["lifecycleStage"], "DISCOVERED")
        self.assertEqual(evidence["alignmentStatus"], "EXACT")
        self.assertEqual(evidence["semanticSupportStatus"], "NOT_ESTABLISHED")
        span = evidence["span"]
        self.assertEqual(source.text[span["start"]:span["end"]], evidence["quote"])

    def test_unresolved_or_ambiguous_input_creates_no_assertion(self):
        source = ingest_source("Ada invents code", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        composition = self.composer.compose(lexical, syntax)
        result = project_assertions_and_evidence(source, composition)
        self.assertEqual(result.assertions, ())
        self.assertEqual(result.evidence, ())

    def test_mismatched_root_span_is_not_projected(self):
        from dataclasses import replace
        source = ingest_source("Ada writes code", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        composition = self.composer.compose(lexical, syntax)
        candidate = composition.candidates[0]
        root = replace(candidate.nodes[-1], source_span=(0, len(source.text) + 1))
        candidate = replace(candidate, nodes=(*candidate.nodes[:-1], root))
        composition = replace(composition, candidates=(candidate,))
        result = project_assertions_and_evidence(source, composition)
        self.assertEqual(result.assertions, ())


if __name__ == "__main__":
    unittest.main()
