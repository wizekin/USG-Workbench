from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from usg_discourse_v07 import (
    MODEL_VERSION, MentionResolutionStatus, NativeMentionV07,
    ReferenceSpace, TypedReference, same_mention,
)


class NativeMentionV07Tests(unittest.TestCase):
    def ref(self, space, external_id):
        return TypedReference(space, external_id)

    def test_model_version_and_required_occurrence_fields(self):
        mention = NativeMentionV07(
            "doc:mention:1", "she", MentionResolutionStatus.UNRESOLVED
        )
        self.assertEqual(MODEL_VERSION, "0.7.0")
        self.assertEqual(mention.surface_text, "she")
        self.assertIsNone(mention.referent_ref)

    def test_mention_identity_is_not_surface_text(self):
        left = NativeMentionV07("m:1", "Alex", MentionResolutionStatus.LINKED)
        right = NativeMentionV07("m:2", "Alex", MentionResolutionStatus.LINKED)
        self.assertFalse(same_mention(left, right))
        self.assertTrue(same_mention(left, replace(right, external_id="m:1")))

    def test_multiple_mentions_can_link_to_same_referent(self):
        referent = self.ref(ReferenceSpace.REFERENT, "r:person")
        first = NativeMentionV07("m:1", "Alex", MentionResolutionStatus.LINKED,
                                 referent_ref=referent)
        second = NativeMentionV07("m:2", "they", MentionResolutionStatus.RESOLVED,
                                  referent_ref=referent)
        self.assertNotEqual(first.external_id, second.external_id)
        self.assertEqual(first.referent_ref, second.referent_ref)

    def test_antecedent_mention_and_referent_are_distinct_typed_links(self):
        mention = NativeMentionV07(
            "m:2", "she", MentionResolutionStatus.RESOLVED,
            antecedent_mention_ref=self.ref(ReferenceSpace.MENTION, "m:1"),
            antecedent_referent_ref=self.ref(ReferenceSpace.REFERENT, "r:1"),
        )
        self.assertEqual(mention.antecedent_mention_ref.space, ReferenceSpace.MENTION)
        self.assertEqual(mention.antecedent_referent_ref.space, ReferenceSpace.REFERENT)

    def test_unresolved_mention_is_valid_without_guessed_links(self):
        mention = NativeMentionV07(
            "m:unknown", "it", MentionResolutionStatus.UNRESOLVED
        )
        self.assertIsNone(mention.referent_ref)
        self.assertIsNone(mention.antecedent_mention_ref)
        self.assertIsNone(mention.antecedent_referent_ref)

    def test_ambiguous_and_unknown_statuses_remain_distinct(self):
        ambiguous = NativeMentionV07("m:a", "that", MentionResolutionStatus.AMBIGUOUS)
        unknown = NativeMentionV07("m:u", "that", MentionResolutionStatus.UNKNOWN)
        self.assertNotEqual(ambiguous.resolution_status, unknown.resolution_status)

    def test_surface_text_and_mention_type_are_not_identity_keys(self):
        first = NativeMentionV07("m:1", "Alex", MentionResolutionStatus.LINKED,
                                 mention_type="PROPER_NOUN")
        second = NativeMentionV07("m:2", "Alex", MentionResolutionStatus.LINKED,
                                  mention_type="PROPER_NOUN")
        self.assertFalse(same_mention(first, second))

    def test_source_span_uses_explicit_source_and_codepoint_pair(self):
        mention = NativeMentionV07(
            "m:1", "😀", MentionResolutionStatus.LINKED,
            source_ref=self.ref(ReferenceSpace.SOURCE, "s:1"),
            source_span=(0, 1),
        )
        self.assertEqual(mention.source_span, (0, 1))

    def test_span_without_source_is_rejected(self):
        with self.assertRaises(ValueError):
            NativeMentionV07("m:1", "x", MentionResolutionStatus.UNKNOWN,
                             source_span=(0, 1))

    def test_wrong_reference_spaces_are_rejected(self):
        with self.assertRaises(ValueError):
            NativeMentionV07("m:1", "x", MentionResolutionStatus.LINKED,
                             referent_ref=self.ref(ReferenceSpace.MENTION, "m:2"))
        with self.assertRaises(ValueError):
            NativeMentionV07("m:1", "x", MentionResolutionStatus.LINKED,
                             antecedent_mention_ref=self.ref(ReferenceSpace.REFERENT, "r:2"))
        with self.assertRaises(ValueError):
            NativeMentionV07("m:1", "x", MentionResolutionStatus.LINKED,
                             source_ref=self.ref(ReferenceSpace.REFERENT, "r:2"))

    def test_resolution_status_does_not_force_a_link(self):
        # The canonical contract does not define a link-presence implication
        # for each status; the model must not invent one.
        linked_status_without_target = NativeMentionV07(
            "m:1", "she", MentionResolutionStatus.LINKED
        )
        self.assertIsNone(linked_status_without_target.referent_ref)

    def test_invalid_codepoint_span_is_rejected(self):
        with self.assertRaises(ValueError):
            NativeMentionV07(
                "m:1", "x", MentionResolutionStatus.UNKNOWN,
                source_ref=self.ref(ReferenceSpace.SOURCE, "s:1"),
                source_span=(3, 2),
            )


if __name__ == "__main__":
    unittest.main()
