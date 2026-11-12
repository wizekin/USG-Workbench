import copy
import unittest

from tools.phase6_independent_gold_v1_0.validate import EXPECTED, validate_manifest


def valid_manifest():
    profiles = []
    for language, construction in sorted(EXPECTED):
        profiles.append({
            "language": language,
            "construction_id": construction,
            "positive": 20,
            "negative": 20,
            "ambiguous": 10,
            "independent_annotator_ids": ["annotator-a", "annotator-b"],
            "adjudicator_id": "adjudicator-c",
            "agreement_report": "agreement-report.json",
        })
    return {
        "manifest_id": "usg-phase6-independent-semantic-gold",
        "version": "1.0.0",
        "contract": "USG-INTERPRET/0.3.0",
        "status": "FROZEN_INDEPENDENT_GOLD",
        "source": {
            "dataset_name": "Example independently annotated dataset",
            "release": "1.0",
            "source_url": "https://example.org/dataset",
            "source_license": "CC-BY-4.0",
            "source_item_ids_pinned": True,
            "acquisition_method": "official_public_release",
        },
        "rights": {
            "license_verified": True,
            "public_redistribution_allowed": True,
            "automated_evaluation_allowed": True,
            "attribution_text": "Dataset attribution statement.",
        },
        "annotation": {
            "guideline_version": "1.0",
            "annotation_method": "independent_human_annotation",
            "independent_annotators_per_case": 2,
            "adjudication": {
                "status": "complete",
                "method": "third_annotator",
                "separate_adjudicator": True,
                "disagreements_preserved": True,
            },
            "model_labels_used": False,
            "development_fixture_independence": True,
            "raw_independent_labels_preserved": True,
        },
        "profiles": profiles,
        "cases": {
            "case_count": 500,
            "case_file": "cases.json",
            "sha256": "a" * 64,
            "exact_source_spans_verified": True,
            "development_overlap_count": 0,
        },
        "leakage_audit": {
            "candidate_predictions_hidden_during_annotation": True,
            "source_ids_checked": True,
            "normalized_text_checked": True,
            "result": "NO_DEVELOPMENT_LEAKAGE",
        },
    }


class TestPhase6IndependentGoldGate(unittest.TestCase):
    def test_schema_and_ten_profile_inventory(self):
        result = validate_manifest(valid_manifest())
        self.assertEqual(result["profile_count"], 10)
        self.assertEqual(result["case_count"], 500)
        self.assertEqual(result["benchmark_enabled_constructions"], [])

    def test_rejects_missing_profile(self):
        data = valid_manifest()
        data["profiles"].pop()
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_model_generated_gold(self):
        data = valid_manifest()
        data["annotation"]["model_labels_used"] = True
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_unverified_redistribution_rights(self):
        data = valid_manifest()
        data["rights"]["public_redistribution_allowed"] = False
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_insufficient_profile_denominator(self):
        data = valid_manifest()
        data["profiles"][0]["ambiguous"] = 9
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_adjudicator_overlap(self):
        data = valid_manifest()
        data["profiles"][0]["adjudicator_id"] = "annotator-a"
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_duplicate_profile(self):
        data = valid_manifest()
        data["profiles"][1] = copy.deepcopy(data["profiles"][0])
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_incomplete_third_annotator_process(self):
        data = valid_manifest()
        data["annotation"]["adjudication"]["separate_adjudicator"] = False
        with self.assertRaises(ValueError):
            validate_manifest(data)


if __name__ == "__main__":
    unittest.main()
