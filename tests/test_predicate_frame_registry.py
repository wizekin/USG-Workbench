"""Source-backed tests for USG-PFR/1.0 (no runtime dependencies)."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "interoperability/predicate-frame-registry/v1.0.0.json"
FRAME_PATH = ROOT / "implementations/python-kernel/v0.4.0/usg/foundation/frames.py"
WORKBENCH_CORE_PATH = ROOT / "implementations/semantic-workbench-js/v0.5.4/semantic-core.js"
WORKBENCH_COMPOSER_PATH = ROOT / "implementations/semantic-workbench-js/v0.5.4/semantic-composer.js"


def load_registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def source_vocab(registry):
    return set().union(*(set(items) for items in registry["sourceVocabulary"].values()))


def frame_catalog(source):
    """Read the compact FrameDef catalogue declarations and their specializations."""
    matches = list(re.finditer(r'FrameDef\(\s*"([A-Z_]+)"\s*,\s*(\d+)', source))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        block = source[match.start():end]
        roles = {}
        for role_match in re.finditer(r'\bt([12])\(\s*"([A-Z_]+)"([^)]*)\)', block, re.S):
            helper, role_name, tail = role_match.groups()
            args = [part.strip() for part in tail.split(",")]
            required_index = 0 if helper == "1" else 1
            required = len(args) > required_index and args[required_index] == "True"
            class_match = re.search(r'\bcls\s*=\s*"([^"]+)"', tail)
            roles[role_name] = {
                "required": required,
                "class": class_match.group(1) if class_match else None,
            }
        parent_match = re.search(r'parents\s*=\s*spec_of\("([A-Z_]+)"', block)
        result[match.group(1)] = {
            "version": int(match.group(2)),
            "parent": parent_match.group(1) if parent_match else None,
            "roles": roles,
        }
    return result


def resolved_roles(catalog, frame_name, seen=None):
    seen = set() if seen is None else set(seen)
    if frame_name in seen or frame_name not in catalog:
        raise AssertionError(f"invalid or cyclic frame ancestry at {frame_name}")
    seen.add(frame_name)
    frame = catalog[frame_name]
    roles = {}
    if frame["parent"]:
        roles.update(resolved_roles(catalog, frame["parent"], seen))
    for name, declaration in frame["roles"].items():
        old = roles.get(name, {"required": False, "class": None})
        roles[name] = {
            "required": old["required"] or declaration["required"],
            "class": declaration["class"] or old["class"],
        }
    return roles


def quoted_set(source, constant_name):
    match = re.search(
        rf"const {re.escape(constant_name)} = new Set\(\[(.*?)\]\);",
        source,
        re.S,
    )
    if not match:
        raise AssertionError(f"Could not find {constant_name} in Workbench source")
    return set(re.findall(r"'([A-Z_]+)'", match.group(1)))


class PredicateFrameRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()
        cls.frame_source = FRAME_PATH.read_text(encoding="utf-8")
        cls.core_source = WORKBENCH_CORE_PATH.read_text(encoding="utf-8")
        cls.composer_source = WORKBENCH_COMPOSER_PATH.read_text(encoding="utf-8")
        cls.catalog = frame_catalog(cls.frame_source)

    def test_registry_identity_and_baseline_pins(self):
        self.assertEqual(self.registry["registryId"], "USG-PFR/1.0")
        self.assertEqual(self.registry["registryVersion"], "1.0.0")
        self.assertEqual(self.registry["baselines"]["workbench"]["version"], "0.5.4")
        self.assertEqual(self.registry["baselines"]["pythonKernel"]["version"], "0.4.0")
        self.assertEqual(self.registry["baselines"]["pythonKernel"]["grammarVersion"], "1.0")

    def test_every_vocabulary_predicate_has_exactly_one_disposition(self):
        vocabulary = source_vocab(self.registry)
        mapped = []
        for entry in self.registry["mappings"]:
            mapped.extend(entry["source"]["predicateIds"])
        unmapped = []
        for entry in self.registry["nonMappings"]:
            unmapped.extend(entry["sourcePredicateIds"])
        accounted = mapped + unmapped
        self.assertEqual(len(accounted), len(set(accounted)), "A predicate has multiple registry dispositions")
        self.assertEqual(set(accounted), vocabulary, "A source predicate is missing a registry disposition")

    def test_mapping_references_a_real_versioned_frame(self):
        for mapping in self.registry["mappings"]:
            target = mapping["target"]
            self.assertIn(target["frame"], self.catalog)
            self.assertEqual(self.catalog[target["frame"]]["version"], target["frameVersion"])

    def test_target_roles_exist_after_frame_inheritance(self):
        for mapping in self.registry["mappings"]:
            target = mapping["target"]
            roles = resolved_roles(self.catalog, target["frame"])
            for item in mapping["roleMap"]:
                self.assertIn(item["targetRole"], roles)
            actual_required = {name for name, item in roles.items() if item["required"]}
            self.assertTrue(set(mapping["requiredTargetRoles"]).issubset(actual_required))
            mapped_target_roles = {item["targetRole"] for item in mapping["roleMap"]}
            self.assertTrue(set(mapping["requiredTargetRoles"]).issubset(mapped_target_roles))

    def test_close_mapping_matches_inherited_role_constraints(self):
        mapping = next(m for m in self.registry["mappings"] if m["mappingId"] == "WB054-CLOSES-to-PYK040-CLOSE-v1")
        roles = resolved_roles(self.catalog, "CLOSE")
        role_map = {item["sourceRole"]: item["targetRole"] for item in mapping["roleMap"]}
        self.assertEqual(role_map, {"subject": "AGENT", "object": "UNDERGOER"})
        self.assertTrue(roles["UNDERGOER"]["required"])
        self.assertEqual(roles["AGENT"]["class"], "Agent")
        self.assertEqual(roles["UNDERGOER"]["class"], "Artifact")
        declared_constraints = {item["targetRole"]: item["requiredSemanticClass"] for item in mapping["targetRoleConstraints"]}
        self.assertEqual(declared_constraints, {"AGENT": "Agent", "UNDERGOER": "Artifact"})

    def test_workbench_declares_close_predicates_as_events_and_transitives(self):
        events = quoted_set(self.core_source, "EVENT_PREDICATES")
        transitives = quoted_set(self.core_source, "TRANSITIVE_PREDICATES")
        self.assertTrue({"CLOSES", "CLOSED"}.issubset(events))
        self.assertTrue({"CLOSES", "CLOSED"}.issubset(transitives))
        self.assertRegex(self.composer_source, r"predicate\s*:\s*'CLOSES'")

    def test_all_active_mappings_are_fail_closed_and_conditional(self):
        for mapping in self.registry["mappings"]:
            self.assertIn(mapping["status"], {"CONDITIONAL_EXACT", "EXACT"})
            self.assertTrue(mapping["applicabilityConditions"])
            self.assertTrue(mapping["evidence"])
            self.assertTrue(mapping["requiredSourceRoles"])
            self.assertTrue(mapping["requiredTargetRoles"])
            role_map = {item["sourceRole"]: item["targetRole"] for item in mapping["roleMap"]}
            self.assertTrue(set(mapping["requiredSourceRoles"]).issubset(role_map))

    def test_unlisted_predicates_default_to_unsupported(self):
        self.assertEqual(self.registry["policy"]["defaultForUnlistedPredicate"], "UNSUPPORTED")
        self.assertIn("never", self.registry["policy"]["unknownPredicateBehavior"].lower())

    def test_non_mappings_do_not_claim_a_target_frame(self):
        for entry in self.registry["nonMappings"]:
            self.assertTrue(entry["sourcePredicateIds"])
            self.assertTrue(entry["reason"])
            self.assertNotIn("target", entry)
            self.assertNotIn("targetFrame", entry)

    def test_every_active_mapping_is_backed_by_workbench_predicate_sets(self):
        events = quoted_set(self.core_source, "EVENT_PREDICATES")
        transitives = quoted_set(self.core_source, "TRANSITIVE_PREDICATES")
        for mapping in self.registry["mappings"]:
            for predicate in mapping["source"]["predicateIds"]:
                self.assertIn(predicate, events)
                self.assertIn(predicate, transitives)


if __name__ == "__main__":
    unittest.main()
