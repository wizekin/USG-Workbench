"""Repeatable fixture checks for the lexical subsystem's structural guarantees.

These tests do not claim that a regex pattern is a correct linguistic ontology.
They measure whether the subsystem preserves the declared evidence boundaries.
"""
from __future__ import annotations

from .analysis import analyze_bundle, classify_definition_pattern


PATTERN_FIXTURES = [
    {"definition": "A person who studies language.", "expected": "person_who"},
    {"definition": "The act of making something available.", "expected": "act_or_process_of"},
    {"definition": "A type of musical instrument.", "expected": "kind_or_type_of"},
    {"definition": "A vehicle with two wheels.", "expected": "initial_nominal_phrase"},
    {"definition": "To move quickly on foot.", "expected": "unclassified_definition"},
]


def run_structural_benchmark() -> dict:
    correct = 0
    observations = []
    for item in PATTERN_FIXTURES:
        actual = classify_definition_pattern(item["definition"])["pattern_type"]
        passed = actual == item["expected"]
        correct += int(passed)
        observations.append({
            "definition": item["definition"],
            "expected_pattern": item["expected"],
            "actual_pattern": actual,
            "passed": passed,
        })
    sample_bundle = {
        "schema_version": "usg-external-lexical/0.1.0",
        "queried_form": "bank",
        "sources": [{"provider": "fixture-provider", "license": "fixture-only"}],
        "entries": [
            {
                "entry_id": "fixture-bank-noun",
                "lemma": "bank",
                "language": "en",
                "part_of_speech": "noun",
                "provider": "fixture-provider",
                "forms": [{"form": "banks", "tags": ["plural"]}],
                "relations": [{
                    "relation_id": "fixture-entry-relation",
                    "type": "related_word",
                    "target_lemma": "shore",
                    "scope": "entry",
                    "source_sense_id": None,
                    "status": "source_asserted_unvalidated",
                }],
                "senses": [
                    {
                        "sense_id": "fixture-bank-river",
                        "definition": "The land alongside a river.",
                        "part_of_speech": "noun",
                        "relations": [{
                            "relation_id": "fixture-sense-relation",
                            "type": "synonym",
                            "target_lemma": "riverside",
                            "scope": "sense",
                            "source_sense_id": "fixture-bank-river",
                            "status": "source_asserted_unvalidated",
                        }],
                    },
                    {
                        "sense_id": "fixture-bank-finance",
                        "definition": "A financial institution.",
                        "part_of_speech": "noun",
                        "relations": [],
                    },
                ],
            }
        ],
    }
    analysis = analyze_bundle(sample_bundle)
    graph_edges = analysis["semantic_candidate_graph"]["edges"]
    entry_relation_preserved = any(
        edge.get("type") == "related_word" and edge.get("scope") == "entry"
        for edge in graph_edges
    )
    sense_relation_preserved = any(
        edge.get("type") == "synonym" and edge.get("scope") == "sense"
        for edge in graph_edges
    )
    distinct_senses_preserved = len({
        node["node_id"] for node in analysis["semantic_candidate_graph"]["nodes"]
        if node.get("node_type") == "lexical_sense_candidate"
    }) == 2
    structural_checks = {
        "pattern_fixture_accuracy": correct / len(PATTERN_FIXTURES),
        "all_expected_pattern_cases_passed": correct == len(PATTERN_FIXTURES),
        "entry_level_relation_scope_preserved": entry_relation_preserved,
        "sense_level_relation_scope_preserved": sense_relation_preserved,
        "homograph_senses_kept_separate": distinct_senses_preserved,
        "bundle_structural_validation": analysis["validation"]["status"],
    }
    checks_passed = (
        correct == len(PATTERN_FIXTURES)
        and entry_relation_preserved
        and sense_relation_preserved
        and distinct_senses_preserved
        and analysis["validation"]["status"] == "valid"
    )
    return {
        "benchmark_version": "usg-external-lexical-structural-benchmark/0.1.0",
        "status": "passed" if checks_passed else "failed",
        "fixture_count": len(PATTERN_FIXTURES),
        "checks": structural_checks,
        "pattern_cases": observations,
        "limitations": [
            "Fixture agreement measures parser and contract behavior, not general linguistic accuracy.",
            "Definition-pattern matches are unvalidated observations, not semantic facts.",
            "This benchmark makes no claim about broad lexical coverage or interpreter accuracy.",
        ],
    }
