import unittest

from tools.phase4_exit_acceptance_v0_1_0 import evaluate


class Phase4ExitAcceptanceTests(unittest.TestCase):
    def test_bounded_demonstrator_exit_acceptance(self):
        report = evaluate()
        self.assertEqual(report["result"], "ACCEPTED_BOUNDED_DEMONSTRATOR", report)
        self.assertTrue(all(report["checks"].values()))
        self.assertIn("not a claim of unrestricted language understanding or truth determination",
                      report["limitations"][-1])


if __name__ == "__main__":
    unittest.main()
