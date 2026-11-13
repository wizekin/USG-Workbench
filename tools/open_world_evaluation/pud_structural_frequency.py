"""Aggregate pinned PUD structural cases without treating UD labels as semantic gold."""
from __future__ import annotations

from collections import Counter
from typing import Any

PUD_STRUCTURAL_FREQUENCY_CONTRACT = "USG-PUD-STRUCTURAL-FREQUENCY/0.1.0"

PROFILE_FAMILIES = {
    "nominal_adjective_modifier": {
        "en": "en.nominal.adjective_modifier",
        "ar": "ar.nominal.adjective_modifier",
    },
    "genitive_surface_pattern": {
        "en": "en.genitive.of_phrase",
        "ar": "ar.genitive.idafa",
    },
    "prepositional_nominal_modifier": {
        "en": "en.prepositional.nominal_modifier",
        "ar": "ar.prepositional.nominal_modifier",
    },
    "temporal_adverbial_modifier": {
        "en": "en.temporal.adverbial_modifier",
        "ar": "ar.temporal.adverbial_modifier",
    },
}


def build_structural_frequency_report(
    *,
    cases_by_language: dict[str, list[dict[str, Any]]],
    dataset_metadata: dict[str, dict[str, Any]],
    generated_at: str,
    selected_candidate_family: str = "nominal_adjective_modifier",
) -> dict[str, Any]:
    """Count eligible extractor cases and select an annotation candidate only.

    The input cases come from the existing Phase 6 external-PUD structural
    extractor. Only language and construction IDs are retained in this report;
    sentence text and case-level examples are deliberately omitted.
    """
    languages = {"en", "ar"}
    if set(cases_by_language) != languages:
        raise ValueError("cases_by_language must contain exactly en and ar")
    if set(dataset_metadata) != languages:
        raise ValueError("dataset_metadata must contain exactly en and ar")
    if selected_candidate_family not in PROFILE_FAMILIES:
        raise ValueError(f"unknown candidate family: {selected_candidate_family}")

    profiles: dict[str, Any] = {}
    for language in ("en", "ar"):
        cases = cases_by_language[language]
        counts: Counter[str] = Counter()
        for index, case in enumerate(cases):
            if case.get("language") != language:
                raise ValueError(f"{language} case {index} has a mismatched language")
            construction = case.get("construction")
            if not isinstance(construction, str) or not construction:
                raise ValueError(f"{language} case {index} has no construction ID")
            counts[construction] += 1

        metadata = dataset_metadata[language]
        profiles[language] = {
            "source": {
                key: metadata[key]
                for key in (
                    "repository",
                    "commit",
                    "file",
                    "git_blob_sha1",
                    "readme_sha1",
                    "license_blob_sha1",
                    "git_blob_sha1_verified",
                    "readme_blob_sha1_verified",
                    "license_blob_sha1_verified",
                    "content_sha256",
                    "license",
                )
                if key in metadata
            },
            "sentence_count": int(metadata["sentence_count"]),
            "syntactic_word_count": int(metadata["syntactic_word_count"]),
            "eligible_structural_case_count": len(cases),
            "construction_counts": dict(sorted(counts.items())),
        }

    family_counts: dict[str, Any] = {}
    for family, construction_ids in PROFILE_FAMILIES.items():
        en_count = profiles["en"]["construction_counts"].get(construction_ids["en"], 0)
        ar_count = profiles["ar"]["construction_counts"].get(construction_ids["ar"], 0)
        family_counts[family] = {
            "construction_ids": dict(construction_ids),
            "language_counts": {"en": en_count, "ar": ar_count},
            "balanced_floor": min(en_count, ar_count),
            "total_eligible_cases": en_count + ar_count,
        }

    selected = family_counts[selected_candidate_family]
    if not all(selected["language_counts"][language] > 0 for language in ("en", "ar")):
        selection_status = "insufficient_bilingual_structural_evidence"
    else:
        selection_status = "candidate_for_SYS09_independent_annotation"

    rationale = (
        "Nominal adjective modification is the selected annotation candidate because the same "
        "UD amod dependency configuration links an ADJ dependent to a nominal head in both "
        "languages, while language-specific order remains testable. The family already exists "
        "in the Phase 6 candidate inventory. This selection prioritizes an annotation study; "
        "it does not enable or promote a runtime rule."
        if selected_candidate_family == "nominal_adjective_modifier"
        else "Candidate selection is for independent annotation only; no runtime rule is enabled."
    )

    return {
        "contract": PUD_STRUCTURAL_FREQUENCY_CONTRACT,
        "generated_at": generated_at,
        "source_population": "full_pinned_pud_treebanks",
        "population_kind": "naturalistic_news_wikipedia_source_structure",
        "source_profiles": profiles,
        "cross_language_family_counts": family_counts,
        "candidate_selection": {
            "construction_family": selected_candidate_family,
            "construction_ids": dict(PROFILE_FAMILIES[selected_candidate_family]),
            "evidence": {
                "language_counts": dict(selected["language_counts"]),
                "balanced_floor": selected["balanced_floor"],
                "total_eligible_cases": selected["total_eligible_cases"],
            },
            "status": selection_status,
            "selection_method": "supervisor_reviewed_frequency_plus_boundedness",
            "rationale": rationale,
        },
        "interpretation_boundary": {
            "label_kind": "UD_syntactic_dependency_proxy",
            "ud_annotations_are_usg_semantic_gold": False,
            "semantic_gold_available": False,
            "counts_are_all_raw_occurrences": False,
            "count_definition": (
                "Eligible contiguous structural cases extracted by the existing Phase 6 external PUD "
                "extractor from the full pinned source treebanks."
            ),
            "naturalistic_campaign_outcomes_included": False,
            "runtime_promotion_allowed": False,
        },
        "limitations": [
            "UD UPOS/dependency labels and token order are syntactic proxies, not USG semantic-role or semantic-frame gold.",
            "Counts cover only eligible contiguous structures selected by the existing extractor, not every occurrence in the source treebanks.",
            "PUD is news/Wikipedia text, not conversational user requests.",
            "All Arabic PUD sentences are translations and do not represent a native-MSA distribution.",
            "Frequency does not establish semantic correctness, precision, attachment accuracy, or runtime capability.",
        ],
    }
