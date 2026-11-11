"""Phase 6 Step 6.3 typed role/frame registry tests."""
import unittest
from tools.phase6_semantic_frames_v0_3_0.validate import validate_registry


class Phase6Step63FrameRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=validate_registry()

    def test_registry_is_candidate_only_and_does_not_enable_grammar(self):
        self.assertEqual(self.registry["status"],"CANDIDATE")
        self.assertTrue(all(frame["status"]=="CANDIDATE" for frame in self.registry["frames"]))
        for frame in self.registry["frames"]:
            self.assertTrue(all(binding["status"]=="CANDIDATE" for binding in frame["constructionBindings"]))

    def test_semantic_roles_are_typed_and_word_order_is_not_role_evidence(self):
        labels={role["label"] for role in self.registry["roleDefinitions"]}
        self.assertIn("AGENT",labels)
        self.assertIn("RECIPIENT",labels)
        self.assertIn("THEME",labels)
        self.assertFalse(self.registry["policy"]["wordOrderDeterminesSemanticRole"])

    def test_every_slot_resolves_to_a_compatible_role(self):
        roles={role["roleId"]:role for role in self.registry["roleDefinitions"]}
        for frame in self.registry["frames"]:
            for slot in frame["slots"]:
                self.assertIn(slot["roleRef"],roles)
                self.assertTrue(set(slot["allowedFillerSorts"]).issubset(set(roles[slot["roleRef"]]["compatibleFillerSorts"])))

    def test_all_four_benchmark_constructions_have_bilingual_frame_bindings(self):
        bindings={(b["language"],b["constructionId"]) for f in self.registry["frames"] for b in f["constructionBindings"]}
        self.assertEqual(len(bindings),8)


if __name__=="__main__":
    unittest.main()
