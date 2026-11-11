"""Fail-closed reproducibility and integrity gate for the lexical PUD report."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

EXPECTED = {
    "pud_repository": "UniversalDependencies/UD_English-PUD",
    "pud_commit": "a697bab43d4111073356de0df5802488bca3de7e",
    "pud_file": "en_pud-ud-test.conllu",
    "pud_git_blob_sha1": "828f827759e7a9f89a8c42bfe79402dd65db71c3",
    "pud_sentences": 1000,
}


def _ratio(numerator: int, denominator: int):
    return numerator / denominator if denominator else None


def validate_report(report: dict) -> dict:
    errors: list[str] = []
    checks: dict[str, bool] = {}

    def check(name: str, condition: bool, message: str):
        checks[name] = bool(condition)
        if not condition:
            errors.append(message)

    check("evaluation_type", report.get("evaluation_type") == "EXTERNAL_CRAWL_LEXICAL_GENERALIZATION_PUD",
          "unexpected evaluation_type")
    check("pinned_pud_dataset", all(report.get(k) == v for k, v in EXPECTED.items()),
          "PUD dataset identity does not match the pinned snapshot")
    check("candidate_only_boundary",
          report.get("lexical_source_is_candidate_only") is True
          and report.get("runtime_promotion_allowed") is False
          and report.get("source_text_persisted") is False,
          "candidate-only, no-promotion, or source-text boundary is violated")
    check("nonempty_evidence",
          isinstance(report.get("lexical_shard_count"), int) and report["lexical_shard_count"] > 0
          and isinstance(report.get("mapped_dictionary_entry_count"), int)
          and report["mapped_dictionary_entry_count"] > 0,
          "lexical evidence is empty or missing")

    totals = report.get("totals")
    check("totals_shape", isinstance(totals, dict), "missing totals object")
    if isinstance(totals, dict):
        required = ("tokens", "seen_tokens", "oov_tokens", "gold_tag_in_candidates",
                    "ambiguous_seen_tokens", "single_candidate_seen_tokens",
                    "multi_candidate_seen_tokens", "candidate_label_total",
                    "gold_lemma_seen", "gold_lemma_and_upos_hit", "tokens_with_gold_lemma")
        check("nonnegative_integer_totals",
              all(isinstance(totals.get(k), int) and totals[k] >= 0 for k in required),
              "required totals must be non-negative integers")
        if all(isinstance(totals.get(k), int) and totals[k] >= 0 for k in required):
            check("token_partition", totals["seen_tokens"] + totals["oov_tokens"] == totals["tokens"],
                  "seen and OOV counts do not sum to tokens")
            check("ambiguity_partition",
                  totals["single_candidate_seen_tokens"] + totals["multi_candidate_seen_tokens"] == totals["seen_tokens"]
                  and totals["multi_candidate_seen_tokens"] == totals["ambiguous_seen_tokens"],
                  "candidate ambiguity counts do not reconcile")
            check("gold_count_bounds",
                  totals["gold_tag_in_candidates"] <= totals["seen_tokens"]
                  and totals["gold_lemma_and_upos_hit"] <= totals["gold_lemma_seen"]
                  and totals["gold_lemma_seen"] <= totals["tokens_with_gold_lemma"] <= totals["tokens"],
                  "gold candidate counts exceed their denominators")
            check("coverage_ratios",
                  math.isclose(totals.get("token_coverage", -1), _ratio(totals["seen_tokens"], totals["tokens"]), abs_tol=1e-12)
                  and math.isclose(totals.get("oov_rate", -1), _ratio(totals["oov_tokens"], totals["tokens"]), abs_tol=1e-12),
                  "token coverage or OOV ratio does not match raw counts")

    ambiguity = report.get("candidate_ambiguity")
    check("ambiguity_shape", isinstance(ambiguity, dict), "missing candidate_ambiguity object")
    if isinstance(ambiguity, dict) and isinstance(totals, dict):
        histogram = ambiguity.get("candidate_label_count_distribution")
        valid_hist = isinstance(histogram, dict) and all(
            str(int(k)) == k and int(k) >= 1 and isinstance(v, int) and v >= 0
            for k, v in histogram.items()
        )
        check("ambiguity_histogram_shape", valid_hist, "invalid candidate-count histogram")
        if valid_hist:
            check("ambiguity_histogram_total", sum(histogram.values()) == totals["seen_tokens"],
                  "candidate-count histogram does not sum to seen tokens")
            weighted = sum(int(k) * v for k, v in histogram.items())
            check("candidate_count_reconciliation", weighted == totals["candidate_label_total"],
                  "candidate-count histogram does not reconcile with candidate_label_total")
        check("precision_not_misrepresented",
              ambiguity.get("candidate_precision_measured") is False,
              "unordered lexical candidate inventory must not claim prediction precision")

    morphology = report.get("morphology_evaluation")
    check("morphology_evaluation_present", isinstance(morphology, dict),
          "missing pinned-annotation morphology evaluation")
    if isinstance(morphology, dict):
        mt = morphology.get("totals", {})
        required_m = ("tokens", "gold_feature_instances", "candidate_feature_instances", "matched_feature_instances")
        check("morphology_totals_shape",
              isinstance(mt, dict) and all(isinstance(mt.get(k), int) and mt[k] >= 0 for k in required_m),
              "morphology totals are missing or invalid")
        if isinstance(mt, dict) and all(isinstance(mt.get(k), int) and mt[k] >= 0 for k in required_m):
            check("morphology_count_bounds",
                  mt["matched_feature_instances"] <= mt["candidate_feature_instances"]
                  and mt["matched_feature_instances"] <= mt["gold_feature_instances"],
                  "morphology matched counts exceed candidate or gold counts")
            expected_precision = _ratio(mt["matched_feature_instances"], mt["candidate_feature_instances"])
            expected_recall = _ratio(mt["matched_feature_instances"], mt["gold_feature_instances"])
            check("morphology_ratio_reconciliation",
                  (mt.get("candidate_pool_precision") is None and expected_precision is None
                   or isinstance(mt.get("candidate_pool_precision"), (int, float))
                   and expected_precision is not None
                   and math.isclose(mt["candidate_pool_precision"], expected_precision, abs_tol=1e-12))
                  and (mt.get("candidate_recall") is None and expected_recall is None
                       or isinstance(mt.get("candidate_recall"), (int, float))
                       and expected_recall is not None
                       and math.isclose(mt["candidate_recall"], expected_recall, abs_tol=1e-12)),
                  "morphology candidate precision/recall do not reconcile with counts")

    check("quality_thresholds_not_invented", True,
          "this gate intentionally applies no arbitrary lexical-quality thresholds")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "acceptance_type": "REPRODUCIBLE_REPORT_INTEGRITY_ONLY",
        "status": "passed",
        "checks": checks,
        "quality_thresholds_applied": False,
        "runtime_promotion_allowed": False,
        "limitations": [
            "Passing validates report identity, boundaries, and internal arithmetic only.",
            "It does not establish lexical completeness, POS accuracy, contextual disambiguation, or semantic correctness.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", default="artifacts/external-lexical-pud-acceptance.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    acceptance = validate_report(report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(acceptance, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
