"""Tests for OW-7 scheduled, release, and on-demand campaign budgets."""

from __future__ import annotations

import unittest

from tools.open_world_evaluation.campaign_profiles import (
    CONTROLLED_DIAGNOSTIC_COUNT,
    MANUAL_MAX,
    resolve_campaign_profile,
)


class OpenWorldCampaignProfileTests(unittest.TestCase):
    def test_daily_profile_uses_small_bounded_smoke_budget(self):
        profile = resolve_campaign_profile(
            "schedule", schedule="15 2 * * *"
        )
        self.assertEqual(profile["cadence"], "daily")
        self.assertEqual(profile["prompt_count"], 20)
        self.assertEqual(profile["random_target_case_count"], 60)
        self.assertEqual(profile["total_case_count"], 60 + CONTROLLED_DIAGNOSTIC_COUNT)

    def test_weekly_profile_increases_exploration_budget(self):
        profile = resolve_campaign_profile(
            "schedule", schedule="30 3 * * 1"
        )
        self.assertEqual(profile["cadence"], "weekly")
        self.assertEqual(profile["prompt_count"], 100)
        self.assertEqual(profile["random_target_case_count"], 300)

    def test_release_profile_runs_deeper_matrix(self):
        profile = resolve_campaign_profile("release")
        self.assertEqual(profile["cadence"], "release")
        self.assertEqual(profile["prompt_count"], 250)
        self.assertEqual(profile["total_case_count"], 856)

    def test_manual_profile_uses_default_and_custom_budget(self):
        self.assertEqual(
            resolve_campaign_profile("workflow_dispatch")["prompt_count"], 100
        )
        self.assertEqual(
            resolve_campaign_profile("workflow_dispatch", prompt_count="7")["prompt_count"],
            7,
        )

    def test_manual_profile_enforces_upper_and_lower_bounds(self):
        for count in ("0", str(MANUAL_MAX + 1), "not-a-number"):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    resolve_campaign_profile("workflow_dispatch", prompt_count=count)

    def test_unknown_schedule_and_event_are_rejected(self):
        with self.assertRaises(ValueError):
            resolve_campaign_profile("schedule", schedule="0 0 * * *")
        with self.assertRaises(ValueError):
            resolve_campaign_profile("push")


if __name__ == "__main__":
    unittest.main()
