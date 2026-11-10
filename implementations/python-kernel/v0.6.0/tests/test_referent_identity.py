import unittest

from usg_identity_v06 import (
    IdentityStatus, IdentityScope, ReferenceSpace, IntroductionKind,
    TypedReference, ReferentIdentity, IntroductionContext,
    NativeReferentV06, same_referent, MODEL_VERSION,
)


class ReferentIdentityModelTests(unittest.TestCase):
    def test_version_is_separate_from_kernel_050(self):
        self.assertEqual(MODEL_VERSION, "0.6.0")

    def test_status_and_scope_are_independent_axes(self):
        value = ReferentIdentity(IdentityStatus.AMBIGUOUS, IdentityScope.GLOBAL)
        self.assertEqual(value.status, IdentityStatus.AMBIGUOUS)
        self.assertEqual(value.scope, IdentityScope.GLOBAL)

    def test_all_identity_statuses_and_scopes_are_distinct(self):
        self.assertEqual(len(set(IdentityStatus)), 6)
        self.assertEqual(len(set(IdentityScope)), 4)

    def test_same_label_does_not_merge_distinct_referents(self):
        a = NativeReferentV06("r-a", "Alex")
        b = NativeReferentV06("r-b", "Alex")
        self.assertFalse(same_referent(a, b))

    def test_labels_and_aliases_do_not_define_identity(self):
        a = NativeReferentV06("r-a", "Alex", aliases=("Alexander",))
        b = NativeReferentV06("r-a", "A. Smith", aliases=("Al",))
        self.assertTrue(same_referent(a, b))

    def test_concept_refs_and_equivalence_refs_use_distinct_spaces(self):
        concept = TypedReference(ReferenceSpace.CONCEPT, "c-1")
        other = TypedReference(ReferenceSpace.REFERENT, "r-2")
        value = NativeReferentV06(
            "r-1", "object", concept_refs=(concept,),
            identity=ReferentIdentity(equivalence_refs=(other,)),
        )
        self.assertEqual(value.concept_refs[0].space, ReferenceSpace.CONCEPT)
        self.assertEqual(value.identity.equivalence_refs[0].space, ReferenceSpace.REFERENT)

    def test_equivalence_links_are_preserved_without_merging(self):
        link = TypedReference(ReferenceSpace.REFERENT, "r-2")
        a = NativeReferentV06("r-1", "same", identity=ReferentIdentity(equivalence_refs=(link,)))
        b = NativeReferentV06("r-2", "same")
        self.assertEqual(a.identity.equivalence_refs, (link,))
        self.assertFalse(same_referent(a, b))

    def test_world_context_has_no_reference(self):
        self.assertEqual(IntroductionContext(), IntroductionContext(IntroductionKind.WORLD))

    def test_non_world_context_requires_typed_context_reference(self):
        with self.assertRaises(ValueError):
            IntroductionContext(IntroductionKind.HYPOTHETICAL)
        context = IntroductionContext(
            IntroductionKind.HYPOTHETICAL,
            TypedReference(ReferenceSpace.NODE, "expr-1"),
        )
        self.assertEqual(context.context_ref.space, ReferenceSpace.NODE)

    def test_unknown_or_unprovided_status_is_not_defaulted(self):
        self.assertIsNone(ReferentIdentity().status)
        self.assertEqual(ReferentIdentity(IdentityStatus.UNKNOWN).status, IdentityStatus.UNKNOWN)

    def test_identity_scope_is_not_introduction_context(self):
        value = NativeReferentV06(
            "r-1", "person",
            identity=ReferentIdentity(scope=IdentityScope.DOCUMENT),
            introduced_in=IntroductionContext(
                IntroductionKind.NEGATED,
                TypedReference(ReferenceSpace.INSTANCE, "inst-1"),
            ),
        )
        self.assertEqual(value.identity.scope, IdentityScope.DOCUMENT)
        self.assertEqual(value.introduced_in.kind, IntroductionKind.NEGATED)

    def test_source_span_uses_non_negative_code_point_offsets(self):
        NativeReferentV06("r-1", "emoji", source_span=(2, 3))
        with self.assertRaises(ValueError):
            NativeReferentV06("r-2", "bad", source_span=(4, 3))

    def test_invalid_reference_spaces_are_rejected(self):
        with self.assertRaises(ValueError):
            ReferentIdentity(equivalence_refs=(
                TypedReference(ReferenceSpace.CONCEPT, "c-1"),
            ))
        with self.assertRaises(ValueError):
            NativeReferentV06(
                "r-1", "x",
                concept_refs=(TypedReference(ReferenceSpace.REFERENT, "r-2"),),
            )


if __name__ == "__main__":
    unittest.main()
