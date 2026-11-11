import unittest
from tools.phase6_benchmark_v0_4_0.validate import validate

class TestPhase6BenchmarkV040(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = validate()

    def test_total_fixture_count(self):
        self.assertEqual(len(self.data["cases"]), 500)

    def test_ten_candidate_profiles(self):
        self.assertEqual(sum(len(x) for x in self.data["construction_inventory"].values()), 10)

    def test_each_profile_has_exact_20_20_10(self):
        for lang, constructions in self.data["construction_inventory"].items():
            for item in constructions:
                cases = [c for c in self.data["cases"] if c["language"] == lang and c["target_construction"] == item["construction_id"]]
                self.assertEqual([sum(c["gold_class"] == label for c in cases) for label in ("POSITIVE", "NEGATIVE", "AMBIGUOUS")], [20, 20, 10])

    def test_role_sets_match_construction_family(self):
        expected = {
            "ADJECTIVE_MODIFIER": {"HEAD", "MODIFIER"},
            "POSSESSION": {"POSSESSED", "POSSESSOR"},
            "NOUN_COMPOUND": {"HEAD", "MODIFIER"},
            "PREPOSITIONAL_MODIFIER": {"HEAD", "LOCATION"},
            "TEMPORAL_MODIFIER": {"EVENT", "TIME"},
        }
        for case in self.data["cases"]:
            if case["gold_class"] == "POSITIVE":
                family = next(x["family"] for x in self.data["construction_inventory"][case["language"]] if x["construction_id"] == case["target_construction"])
                self.assertEqual(set(case["expected_roles"]), expected[family])

    def test_all_constructions_remain_candidate_only(self):
        self.assertTrue(all(not c["enabled"] for items in self.data["construction_inventory"].values() for c in items))

if __name__ == "__main__":
    unittest.main()
