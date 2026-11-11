"""Reusable Phase 5 lexical foundation and held-out coverage tests."""
from __future__ import annotations

import unittest
from pathlib import Path

from tools.usg_interpretation_v0_1_0.source import ingest_source
from tools.usg_interpretation_v0_2_0.lexical import (
    LexicalAnalyzer,
    bundled_lexical_resource_v0_3_0,
    bundled_lexical_resource_v0_4_0,
    compose_lexical_resources,
    load_lexical_resource,
)
from tools.usg_interpretation_v0_2_0.integration import Phase5InterpretationService
from tools.usg_interpretation_v0_2_0.catalogue import bundled_resource_descriptors


class Phase5LexicalFoundationTests(unittest.TestCase):
    def setUp(self):
        self.resource = bundled_lexical_resource_v0_4_0()
        self.analyzer = LexicalAnalyzer(self.resource)

    def analyze(self, text: str):
        source = ingest_source(text, "en")
        return self.analyzer.analyze(source)

    def test_composite_resource_contains_existing_and_starter_resources(self):
        prior = bundled_lexical_resource_v0_3_0()
        starter = load_lexical_resource(
            Path(__file__).resolve().parents[1]
            / "resources" / "lexical" / "v0.4.0" / "en-core-starter-lexicon.json"
        )
        composite = compose_lexical_resources((prior, starter))
        self.assertEqual(composite.resource_id, "usg-en-ar-composite-lexicon")
        self.assertGreater(len(composite.entries), len(prior.entries))
        self.assertEqual(composite.digest(), self.resource.digest())
        self.assertIn("usg-en-ar-discourse-lexicon@0.3.0", composite.provenance)
        self.assertIn("usg-en-core-starter-lexicon@0.4.0", composite.provenance)

    def test_common_function_words_are_resolved(self):
        result = self.analyze("The atom is a part of matter and energy.")
        by_form = {item.token.surface_text.casefold(): item for item in result.tokens
                   if item.token.kind == "WORD"}
        for form in ("the", "atom", "is", "a", "part", "of", "matter", "and", "energy"):
            with self.subTest(form=form):
                self.assertIn(by_form[form].status, {"RESOLVED", "AMBIGUOUS"})
                self.assertGreater(len(by_form[form].candidates), 0)

    def test_introductory_science_vocabulary_and_regular_plural_are_supported(self):
        result = self.analyze(
            "Chemistry contains atoms, molecules, elements, compounds, "
            "chemical reactions, electrons, energy, and matter."
        )
        by_form = {item.token.surface_text.casefold(): item for item in result.tokens
                   if item.token.kind == "WORD"}
        for form in ("chemistry", "contains", "atoms", "molecules", "elements",
                     "compounds", "chemical", "reactions", "electrons", "energy", "matter"):
            with self.subTest(form=form):
                self.assertGreater(len(by_form[form].candidates), 0)
        atoms = by_form["atoms"].candidates[0]
        self.assertEqual(atoms.lemma, "atom")
        self.assertEqual(dict(atoms.features).get("Number"), "Plural")
        self.assertEqual(atoms.derived_by_rule, "en.noun.regular-plural.s")

    def test_morphological_derivation_is_explicit_and_traceable(self):
        result = self.analyze("The system understands containing matter physically.")
        by_form = {item.token.surface_text.casefold(): item for item in result.tokens
                   if item.token.kind == "WORD"}
        self.assertEqual(by_form["understands"].candidates[0].lemma, "understand")
        self.assertEqual(by_form["understands"].candidates[0].derived_by_rule,
                         "en.verb.third-person-singular.s")
        self.assertEqual(by_form["containing"].candidates[0].lemma, "contain")
        self.assertEqual(by_form["containing"].candidates[0].derived_by_rule,
                         "en.verb.participle.ing")
        self.assertEqual(by_form["physically"].candidates[0].lemma, "physical")
        self.assertEqual(by_form["physically"].candidates[0].derived_by_rule,
                         "en.adverb.derived.ly")

    def test_ambiguity_is_preserved_instead_of_forced(self):
        result = self.analyze("The bank changes.")
        bank = next(item for item in result.tokens if item.token.surface_text == "bank")
        self.assertEqual(bank.status, "AMBIGUOUS")
        self.assertEqual({item.sense_id for item in bank.candidates},
                         {"en:noun.bank.financial", "en:noun.bank.river"})

    def test_unknown_words_remain_unresolved(self):
        result = self.analyze("The flarble atom is zentropic.")
        unknown = {item.token.surface_text: item for item in result.tokens
                   if item.token.kind == "WORD"}
        self.assertEqual(unknown["flarble"].status, "UNRESOLVED")
        self.assertEqual(unknown["zentropic"].status, "UNRESOLVED")

    def test_phase5_uses_composite_resource_and_exposes_hash_semantics(self):
        result = Phase5InterpretationService().interpret(
            "The atom is a part of matter.", "en", resource_manifest_digest="a" * 64
        )
        lexical = result["stages"]["lexical"]
        self.assertEqual(lexical["resource_id"], "usg-en-ar-composite-lexicon")
        self.assertEqual(lexical["resource_version"], "0.4.0")
        self.assertEqual(lexical["resource_sha256_kind"],
                         "canonical_composite_resource_content")
        self.assertIn("usg-en-core-starter-lexicon@0.4.0",
                      lexical["resource_provenance"])
        self.assertIn("usg-en-core-starter-lexicon",
                      {item["resource_id"] for item in result["resource_versions"]})


    def test_scoped_negation_and_modality_are_not_projected_as_bare_svo(self):
        from tools.phase5_interpretation_benchmark_v0_2_0.run import run_pipeline

        cases = [
            {"id": "negative.negation", "language": "en",
             "text": "Ada does not write code."},
            {"id": "negative.modality", "language": "en",
             "text": "Ada may write code."},
            {"id": "negative.future", "language": "en",
             "text": "Ada will write code."},
        ]
        predictions, _ = run_pipeline({"cases": cases})
        for prediction in predictions["predictions"]:
            with self.subTest(case=prediction["case_id"]):
                self.assertIsNone(prediction["construction_id"])
                self.assertEqual(prediction["role_bindings"], {})
                self.assertEqual(prediction["role_spans"], {})

    def test_resource_catalogue_contains_starter_asset(self):
        descriptors = bundled_resource_descriptors()
        descriptor = next(item for item in descriptors
                          if item.resource_id == "usg-en-core-starter-lexicon")
        self.assertEqual(descriptor.version, "0.4.0")
        self.assertEqual(len(descriptor.sha256), 64)


if __name__ == "__main__":
    unittest.main()
