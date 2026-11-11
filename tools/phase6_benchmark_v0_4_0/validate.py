"""Validate the Phase 6 v0.4.0 nominal/modifier candidate gold corpus."""
from pathlib import Path
import json
from collections import Counter
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "benchmarks/phase6-interpretation-v0.4.0"
ROLE_KEYS = {
    "ADJECTIVE_MODIFIER": {"HEAD", "MODIFIER"},
    "POSSESSION": {"POSSESSED", "POSSESSOR"},
    "NOUN_COMPOUND": {"HEAD", "MODIFIER"},
    "PREPOSITIONAL_MODIFIER": {"HEAD", "LOCATION"},
    "TEMPORAL_MODIFIER": {"EVENT", "TIME"},
}

def _slice(text, span):
    if span["start"] < 0 or span["end"] <= span["start"]:
        raise ValueError("invalid span bounds")
    return "".join(list(text)[span["start"]:span["end"]])

def validate():
    schema = json.loads((BASE / "corpus.schema.json").read_text(encoding="utf-8"))
    data = json.loads((BASE / "corpus.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors[:12]))

    inventory = {}
    for language, constructions in data["construction_inventory"].items():
        for construction in constructions:
            key = (language, construction["construction_id"])
            if key in inventory:
                raise ValueError(f"duplicate construction inventory entry: {key}")
            if construction["enabled"] is not False:
                raise ValueError(f"candidate construction unexpectedly enabled: {key}")
            if construction["family"] not in ROLE_KEYS:
                raise ValueError(f"unknown construction family: {key}")
            inventory[key] = construction["family"]

    ids = set()
    counts = Counter()
    for case in data["cases"]:
        case_id = case["id"]
        if case_id in ids:
            raise ValueError("duplicate fixture id: " + case_id)
        ids.add(case_id)
        key = (case["language"], case["target_construction"])
        if key not in inventory:
            raise ValueError(f"fixture refers to unknown construction: {case_id}")
        family = inventory[key]
        counts[(key[0], key[1], case["gold_class"])] += 1

        roles = case["expected_roles"]
        role_spans = case["expected_role_spans"]
        if set(roles) != set(role_spans):
            raise ValueError("role/span keys mismatch: " + case_id)
        for role, span in role_spans.items():
            surface = _slice(case["text"], span)
            if surface != span["surface"]:
                raise ValueError(f"invalid exact role span: {case_id}/{role}")
            if roles[role] != span["surface"]:
                raise ValueError(f"role binding differs from source span: {case_id}/{role}")

        evidence_spans = list(case["expected_grammatical_markers"])
        if case["expected_predicate_span"] is not None:
            evidence_spans.append(case["expected_predicate_span"])
        for span in evidence_spans:
            if _slice(case["text"], span) != span["surface"]:
                raise ValueError("invalid predicate/marker span: " + case_id)

        if case["gold_class"] == "POSITIVE":
            if case["gold_construction"] != case["target_construction"]:
                raise ValueError("positive gold construction mismatch: " + case_id)
            if set(roles) != ROLE_KEYS[family]:
                raise ValueError(f"wrong semantic role inventory for {case_id}: {sorted(roles)}")
            if case["expected_completion_status"] != "COMPLETE" or case["ambiguity_reason"] is not None:
                raise ValueError("invalid positive status/ambiguity: " + case_id)
            if family == "TEMPORAL_MODIFIER" and case["expected_predicate_span"] is None:
                raise ValueError("temporal modifier requires predicate evidence: " + case_id)
            if family != "TEMPORAL_MODIFIER" and case["expected_predicate_span"] is not None:
                raise ValueError("nominal relation must not invent predicate evidence: " + case_id)
        else:
            if case["gold_construction"] is not None or roles or role_spans:
                raise ValueError("non-positive case contains a unique semantic graph: " + case_id)
            if case["expected_completion_status"] is not None or case["expected_predicate_span"] is not None or case["expected_grammatical_markers"]:
                raise ValueError("non-positive case contains unique completion/evidence: " + case_id)
            is_ambiguous = case["gold_class"] == "AMBIGUOUS"
            if is_ambiguous != (case["ambiguity_reason"] is not None):
                raise ValueError("ambiguity reason mismatch: " + case_id)

    required = data["minimums_per_language_and_construction"]
    for language, construction in inventory:
        for label, minimum in (("POSITIVE", required["positive"]), ("NEGATIVE", required["negative"]), ("AMBIGUOUS", required["ambiguous"])):
            actual = counts[(language, construction, label)]
            if actual != minimum:
                raise ValueError(f"fixture count mismatch for {language}/{construction}/{label}: {actual} != {minimum}")
    if len(ids) != 500:
        raise ValueError(f"expected 500 unique fixtures, got {len(ids)}")
    return data

if __name__ == "__main__":
    corpus = validate()
    print(f"validated {len(corpus['cases'])} fixtures across {sum(map(len, corpus['construction_inventory'].values()))} candidate profiles; role semantics and Unicode spans checked")
