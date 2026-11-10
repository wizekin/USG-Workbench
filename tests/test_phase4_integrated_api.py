import unittest

from tools.usg_interpretation_v0_1_0 import InterpretationService
from tools.usg_local_api_v1_0_0.application import USGApplication


class InterpretationServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = InterpretationService()

    def test_demo_english_interpretation_returns_canonical_document(self):
        result = self.service.interpret("Ada writes code.", "en")
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["document"]["profileId"], "USG-SEM/1.0")
        self.assertEqual(len(result["document"]["expressions"]), 3)
        self.assertEqual(result["document"]["assertions"][0]["commitment"], "NONE")
        self.assertEqual(result["document"]["evidence"][0]["semanticSupportStatus"], "NOT_ESTABLISHED")

    def test_arabic_demo_interpretation_preserves_source(self):
        text = "كتب الطالب الدرس"
        result = self.service.interpret(text, "ar")
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["document"]["sources"][0]["text"], text)

    def test_unknown_lexical_items_yield_partial_document(self):
        result = self.service.interpret("Ada invents code", "en")
        self.assertEqual(result["completion_status"], "PARTIAL")
        self.assertTrue(result["document"]["unresolvedItems"])
        self.assertEqual(result["document"]["expressions"], [])

    def test_multiple_sentences_are_explicitly_unsupported(self):
        result = self.service.interpret("Ada writes code. Ada writes code.", "en")
        self.assertEqual(result["completion_status"], "UNSUPPORTED")
        self.assertEqual(len(result["document"]["unresolvedItems"]), 2)


class InterpretationAPITests(unittest.TestCase):
    def setUp(self):
        self.app = USGApplication(":memory:")

    def tearDown(self):
        self.app.close()

    def test_interpret_endpoint_persists_canonical_document_in_shared_sqlite_store(self):
        status, result = self.app.dispatch("POST", "/v1/interpret", {
            "text": "Ada writes code.", "language": "en", "persist": True,
        })
        self.assertEqual(status, 200)
        self.assertEqual(result["completion_status"], "COMPLETE")
        self.assertEqual(result["persistence"]["status"], "STORED")
        stored = self.app.store.get_document(result["persistence"]["document_id"])
        self.assertEqual(stored.document["sources"][0]["text"], "Ada writes code.")

    def test_interpret_endpoint_can_return_without_persisting(self):
        status, result = self.app.dispatch("POST", "/v1/interpret", {
            "text": "unknown words", "language": "en", "persist": False,
        })
        self.assertEqual(status, 200)
        self.assertNotIn("persistence", result)
        self.assertEqual(result["completion_status"], "PARTIAL")

    def test_invalid_request_is_rejected(self):
        status, result = self.app.dispatch("POST", "/v1/interpret", {"text": 7, "language": "en"})
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "INTERPRET_REQUEST_INVALID")


if __name__ == "__main__":
    unittest.main()
