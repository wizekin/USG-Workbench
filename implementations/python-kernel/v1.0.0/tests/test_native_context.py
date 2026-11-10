import unittest

from usg_context_v10 import (
    MODEL_VERSION, ContextKind, NativeContextV10, ReferenceSpace,
    TypedReference, same_context,
)


class NativeContextV10Tests(unittest.TestCase):
    def setUp(self):
        self.parent = TypedReference(ReferenceSpace.CONTEXT, "opaque/context-parent")
        self.source = TypedReference(ReferenceSpace.SOURCE, "opaque/source")
        self.agent = TypedReference(ReferenceSpace.REFERENT, "opaque/referent")

    def make_context(self, **changes):
        values = dict(
            external_id="opaque/context-A",
            kind=ContextKind.WORLD,
        )
        values.update(changes)
        return NativeContextV10(**values)

    def test_version(self):
        self.assertEqual(MODEL_VERSION, "1.0.0")

    def test_all_contract_context_kinds_are_preserved(self):
        self.assertEqual({x.value for x in ContextKind}, {
            "WORLD", "FICTION", "HYPOTHETICAL", "HISTORICAL_BELIEF",
            "DOMAIN_MODEL", "ATTITUDE", "CONDITIONAL", "NEGATED", "UNKNOWN",
        })

    def test_required_opaque_identity(self):
        with self.assertRaises(ValueError):
            self.make_context(external_id="")

    def test_kind_is_explicit_enum(self):
        with self.assertRaises(TypeError):
            self.make_context(kind="WORLD")

    def test_parent_reference_requires_context_space(self):
        item = self.make_context(parent_ref=self.parent)
        self.assertEqual(item.parent_ref, self.parent)
        with self.assertRaises(ValueError):
            self.make_context(parent_ref=self.source)

    def test_source_reference_requires_source_space(self):
        self.assertEqual(self.make_context(source_ref=self.source).source_ref, self.source)
        with self.assertRaises(ValueError):
            self.make_context(source_ref=self.agent)

    def test_agent_reference_requires_referent_space(self):
        self.assertEqual(self.make_context(agent_ref=self.agent).agent_ref, self.agent)
        with self.assertRaises(ValueError):
            self.make_context(agent_ref=self.source)

    def test_typed_reference_rejects_string_space(self):
        with self.assertRaises(TypeError):
            TypedReference("SOURCE", "source-A")

    def test_typed_reference_requires_nonempty_opaque_id(self):
        with self.assertRaises(ValueError):
            TypedReference(ReferenceSpace.SOURCE, "")

    def test_optional_fields_remain_absent(self):
        item = self.make_context()
        self.assertIsNone(item.parent_ref)
        self.assertIsNone(item.source_ref)
        self.assertIsNone(item.agent_ref)
        self.assertIsNone(item.name)
        self.assertIsNone(item.metadata)

    def test_name_is_preserved_without_normalization(self):
        name = "  nested / hypothetical context  "
        self.assertEqual(self.make_context(name=name).name, name)

    def test_metadata_preserves_nested_values(self):
        metadata = {"source": {"kind": "quoted", "tags": ["a", "b"]}, "flag": False}
        self.assertEqual(self.make_context(metadata=metadata).metadata, metadata)

    def test_metadata_must_be_mapping(self):
        with self.assertRaises(TypeError):
            self.make_context(metadata=["not", "an", "object"])

    def test_metadata_keys_must_be_strings(self):
        with self.assertRaises(ValueError):
            self.make_context(metadata={1: "invalid"})

    def test_metadata_is_copied_from_input(self):
        metadata = {"nested": {"items": [1, 2]}}
        item = self.make_context(metadata=metadata)
        metadata["nested"]["items"].append(3)
        self.assertEqual(item.metadata, {"nested": {"items": [1, 2]}})

    def test_identity_uses_only_opaque_record_id(self):
        left = self.make_context(name="first")
        same = self.make_context(name="different", kind=ContextKind.FICTION)
        other = self.make_context(external_id="opaque/context-B")
        self.assertTrue(same_context(left, same))
        self.assertFalse(same_context(left, other))

    def test_unknown_context_kind_is_distinct(self):
        self.assertNotEqual(ContextKind.UNKNOWN, ContextKind.WORLD)

    def test_context_does_not_infer_parent_or_agent(self):
        item = self.make_context(kind=ContextKind.ATTITUDE)
        self.assertIsNone(item.parent_ref)
        self.assertIsNone(item.agent_ref)


if __name__ == "__main__":
    unittest.main()
