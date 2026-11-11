"""Real Chromium smoke checks for the USG Semantic Workbench browser UI."""
from __future__ import annotations

import os
import unittest

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("USG_WORKBENCH_URL", "http://127.0.0.1:8765/")


class WorkbenchBrowserSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(BASE_URL, wait_until="networkidle")

    def tearDown(self):
        self.context.close()

    def test_local_interpretation_renders_inspectable_candidate(self):
        self.page.locator('button[data-view="interpret"]').click()
        source = self.page.locator("#source-text")
        source.fill("A sparrow is a kind of bird.")
        self.page.locator("#analyze-button").click()
        results = self.page.locator("#interpret-results")
        results.wait_for(state="visible")
        self.assertIn("Candidate semantic interpretation", results.inner_text())
        self.page.locator('button[data-result-tab="raw"]').click()
        raw = self.page.locator("#raw-json").inner_text()
        self.assertIn("SUBCLASS_OF", raw)
        self.assertIn("sparrow", raw.lower())

    def test_navigation_and_demo_knowledge_render(self):
        self.page.locator('button[data-view="knowledge"]').click()
        self.page.locator("#view-knowledge").wait_for(state="visible")
        count = self.page.locator("#metric-claims").inner_text()
        self.assertTrue(count.strip().isdigit())
        self.assertGreater(int(count), 0)
        self.page.locator('button[data-view="patterns"]').click()
        self.page.locator("#view-patterns").wait_for(state="visible")

    def test_reasoning_engine_exposes_derived_claims_and_export(self):
        self.page.locator('button[data-view="reasoning"]').click()
        self.page.locator("#run-reasoning-button").click()
        derived = self.page.locator("#derived-list")
        derived.wait_for(state="visible")
        self.assertIn("Tweety", derived.inner_text())
        self.assertIn("Animal", derived.inner_text())
        with self.page.expect_download() as download_info:
            self.page.locator("#export-button").click()
        download = download_info.value
        self.assertTrue(download.suggested_filename.startswith("usg-workbench-backup-"))
        self.assertTrue(download.suggested_filename.endswith(".json"))


if __name__ == "__main__":
    unittest.main()
