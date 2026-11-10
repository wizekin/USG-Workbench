import unittest

from tools.usg_interpretation_v0_1_0 import (
    GrammarAnalyzer, LexicalAnalyzer, LexicalEntry, LexicalResource,
    SemanticComposer, initial_grammar_registry, initial_semantic_frame_registry,
    ingest_source,
)


class SemanticCompositionTests(unittest.TestCase):
    def setUp(self):
        entries = (
            LexicalEntry("en", "Ada", "Ada", "PROPN", "en:ada"),
            LexicalEntry("en", "writes", "write", "VERB", "en:write"),
            LexicalEntry("en", "code", "code", "NOUN", "en:code"),
            LexicalEntry("ar", "كتب", "كتب", "VERB", "ar:write"),
            LexicalEntry("ar", "الطالب", "طالب", "NOUN", "ar:student"),
            LexicalEntry("ar", "الدرس", "درس", "NOUN", "ar:lesson"),
        )
        self.lexical = LexicalAnalyzer(LexicalResource("compose-fixture", 1, entries))
        self.grammar = GrammarAnalyzer(initial_grammar_registry())
        self.composer = SemanticComposer(initial_semantic_frame_registry())

    def test_english_svo_composes_typed_predicate_and_roles(self):
        source = ingest_source("Ada writes code", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        result = self.composer.compose(lexical, syntax)
        self.assertEqual(result.status, "COMPOSED")
        candidate = result.candidates[0]
        self.assertEqual(candidate.status, "RESOLVED")
        root = candidate.nodes[-1]
        self.assertEqual(root.op, "PREDICATE_APP")
        self.assertEqual(root.sort, "PROP")
        self.assertEqual(dict(root.params)["predicate"], "predicate:write")
        self.assertEqual([x.op for x in candidate.nodes], ["REF", "REF", "PREDICATE_APP"])

    def test_arabic_vso_composition_preserves_semantic_subject_object_roles(self):
        source = ingest_source("كتب الطالب الدرس", "ar")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        result = self.composer.compose(lexical, syntax)
        self.assertEqual(result.status, "COMPOSED")
        root = result.candidates[0].nodes[-1]
        self.assertEqual(dict(root.params)["predicate"], "predicate:write")
        role_bindings = dict(dict(root.params)["roleBindings"])
        self.assertNotEqual(role_bindings["SUBJECT"], role_bindings["OBJECT"])

    def test_missing_frame_is_unsupported_not_guessed(self):
        source = ingest_source("Ada writes code", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        from tools.usg_interpretation_v0_1_0.compose import SemanticComposer, SemanticFrameRegistry
        result = SemanticComposer(SemanticFrameRegistry("empty", 1, ())).compose(lexical, syntax)
        self.assertEqual(result.status, "UNSUPPORTED")
        self.assertEqual(result.candidates[0].diagnostics, ("NO_REGISTERED_SEMANTIC_FRAME",))

    def test_unknown_word_never_becomes_a_semantic_expression(self):
        source = ingest_source("Ada invents code", "en")
        lexical = self.lexical.analyze(source)
        syntax = self.grammar.analyze(lexical)
        result = self.composer.compose(lexical, syntax)
        self.assertEqual(result.status, "UNRESOLVED")
        self.assertEqual(result.candidates, ())


if __name__ == "__main__":
    unittest.main()
