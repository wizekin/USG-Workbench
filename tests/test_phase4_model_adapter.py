import unittest

from tools.usg_interpretation_v0_1_0 import (
    ModelAssistedAnalyzer, ModelCandidate, ModelProposalBatch,
    ingest_source, validate_model_proposals,
)


def batch(source, candidates):
    return ModelProposalBatch(source.sha256, source.language, "local-model",
                              "1.2.3", "config-sha", "prompt-sha", tuple(candidates))


class FakeGenerator:
    def __init__(self, proposal):
        self.proposal = proposal
    def generate(self, source):
        return self.proposal


class ModelAdapterTests(unittest.TestCase):
    def test_valid_source_grounded_candidate_retains_model_provenance(self):
        source = ingest_source("Ada writes code", "en")
        candidate = ModelCandidate("c1", 0, 3, "Ada", "Ada", "PROPN",
                                   "person:ada", 1, "MODEL_LEXICAL_PROPOSAL")
        result = validate_model_proposals(source, batch(source, [candidate]))
        self.assertEqual(result.status, "ACCEPTED_CANDIDATES")
        self.assertEqual(result.candidates[0].grounding_status, "EXACT_SOURCE_SPAN")
        self.assertEqual(result.candidates[0].model_version, "1.2.3")

    def test_wrong_source_hash_rejects_batch(self):
        source = ingest_source("Ada writes code", "en")
        other = ingest_source("Eve writes code", "en")
        candidate = ModelCandidate("c1", 0, 3, "Eve", "Eve", "PROPN", None, 1, "MODEL")
        result = validate_model_proposals(source, batch(other, [candidate]))
        self.assertEqual(result.status, "REJECTED_BATCH")
        self.assertEqual(result.diagnostics, ("SOURCE_HASH_MISMATCH",))

    def test_mismatched_surface_or_out_of_range_span_rejects_batch(self):
        source = ingest_source("Ada writes code", "en")
        bad = ModelCandidate("c1", 0, 3, "Eve", "Eve", "PROPN", None, 1, "MODEL")
        self.assertEqual(validate_model_proposals(source, batch(source, [bad])).diagnostics,
                         ("SPAN_SURFACE_MISMATCH",))
        bad_range = ModelCandidate("c2", 0, 99, "Ada", "Ada", "PROPN", None, 1, "MODEL")
        self.assertEqual(validate_model_proposals(source, batch(source, [bad_range])).diagnostics,
                         ("SPAN_OUT_OF_RANGE",))

    def test_optional_generator_wrapper_rejects_wrong_return_type(self):
        source = ingest_source("Ada writes code", "en")
        result = ModelAssistedAnalyzer(FakeGenerator({})).analyze(source)
        self.assertEqual(result.status, "REJECTED_BATCH")
        self.assertEqual(result.diagnostics, ("INVALID_PROPOSAL_BATCH_TYPE",))


if __name__ == "__main__":
    unittest.main()
