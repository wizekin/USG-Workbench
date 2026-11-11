"""Verify bundled resource assets are discoverable as installed package data."""
import unittest
from importlib.resources import files


class PackagedResourceTests(unittest.TestCase):
    def test_bundled_lexical_and_operator_assets_are_package_resources(self):
        root = files("resources")
        expected = (
            "lexical/v0.1.0/en-ar-foundation-lexicon.json",
            "lexical/v0.2.0/en-ar-operator-lexicon.json",
            "lexical/v0.3.0/en-ar-discourse-lexicon.json",
            "lexical/v0.4.0/en-core-starter-lexicon.json",
            "lexical/v0.5.0/en-core-starter-lexicon.json",
            "operators/v0.1.0/operators-en-ar.json",
        )
        for relative in expected:
            with self.subTest(resource=relative):
                item = root.joinpath(*relative.split("/"))
                self.assertTrue(item.is_file())
                self.assertGreater(item.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
