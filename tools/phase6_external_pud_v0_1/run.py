"""Independent structural evaluation against Universal Dependencies PUD.

UD annotations select gold syntactic configurations; USG's own analyzer never
creates or filters gold cases. This is a structural proxy benchmark, not a
human-adjudicated semantic-role gold set. Results cannot enable constructions.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha1
from pathlib import Path
from urllib.request import urlopen
import json

from tools.phase6_nominal_candidate_v0_4_1.analyzer import analyze

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "phase6-step-6.6-pud-report.json"
DATASETS = {
    "en": {
        "repo": "UD_English-PUD",
        "file": "en_pud-ud-test.conllu",
        "commit": "a697bab43d4111073356de0df5802488bca3de7e",
        "blob_sha": "828f827759e7a9f89a8c42bfe79402dd65db71c3",
        "sentences": 1000,
    },
    "ar": {
        "repo": "UD_Arabic-PUD",
        "file": "ar_pud-ud-test.conllu",
        "commit": "c606299bc9eb8baa6c61c8dd3efc9a0fbf73aa87",
        "blob_sha": "075361d5425ea0d43ff6b4f5459a306e26df6fbf",
        "sentences": 1000,
    },
}


def download_dataset(language: str) -> bytes:
    spec = DATASETS[language]
    url = (
        "https://raw.githubusercontent.com/UniversalDependencies/"
        f"{spec['repo']}/{spec['commit']}/{spec['file']}"
    )
    with urlopen(url, timeout=60) as response:
        payload = response.read()
    actual = sha1(f"blob {len(payload)}\\0".encode("ascii") + payload).hexdigest()
    if actual != spec["blob_sha"]:
        raise ValueError(f"{language} PUD Git blob hash mismatch: {actual}")
    return payload


def parse_conllu(payload: bytes) -> list[dict]:
    source = payload.decode("utf-8")
    sentences = []
    for block in source.strip().split("\\n\\n"):
        meta, tokens = {}, []
        for line in block.splitlines():
            if line.startswith("# "):
                key, sep, value = line[2:].partition(" = ")
                if sep:
                    meta[key] = value
                continue
            if not line or line.startswith("#"):
                continue
            cols = line.split("\\t")
            # Multiword-token and empty-node rows are not syntactic words.
            if len(cols) != 10 or not cols[0].isdigit():
                continue
            tokens.append({
                "id": int(cols[0]), "form": cols[1], "lemma": cols[2],
                "upos": cols[3], "head": int(cols[6]), "deprel": cols[7],
                "misc": cols[9],
            })
        if tokens:
            sentences.append({"meta": meta, "tokens": tokens})
    return sentences


def _contiguous(tokens: list[dict]) -> bool:
    return bool(tokens) and all(
        b["id"] == a["id"] + 1 for a, b in zip(tokens, tokens[1:])
    )


def _case_child(tokens: list[dict], head_id: int) -> dict | None:
    return next((t for t in tokens if t["head"] == head_id
                 and t["deprel"] == "case" and t["upos"] == "ADP"), None)


def _det_child(tokens: list[dict], head_id: int) -> dict | None:
    return next((t for t in tokens if t["head"] == head_id
                 and t["deprel"] == "det" and t["upos"] == "DET"), None)


def _gold(lang: str, con: str, tokens: list[dict], roles: dict) -> dict:
    phrase = " ".join(t["form"] for t in tokens)
    return {"language": lang, "construction": con, "text": phrase,
            "expected_roles": roles}


def extract_gold(sentences: list[dict], lang: str) -> list[dict]:
    cases, seen = [], set()
    for sentence in sentences:
        ts = sentence["tokens"]
        by_id = {t["id"]: t for t in ts}

        def add(con: str, ordered: list[dict], roles: dict):
            if not _contiguous(ordered):
                return
            key = (con, tuple(t["id"] for t in ordered))
            if key in seen:
                return
            seen.add(key)
            cases.append(_gold(lang, con, ordered, roles))

        for dep in ts:
            head = by_id.get(dep["head"])
            if not head:
                continue

            if lang == "en" and dep["upos"] == "ADJ" and dep["deprel"] == "amod" and head["upos"] in {"NOUN", "PROPN"}:
                det = _det_child(ts, head["id"])
                ordered = [x for x in (det, dep, head) if x]
                ordered.sort(key=lambda x: x["id"])
                if [x["id"] for x in ordered][-2:] == [dep["id"], head["id"]]:
                    add("en.nominal.adjective_modifier", ordered,
                        {"MODIFIER": dep["form"], "HEAD": head["form"]})

            if lang == "ar" and dep["upos"] == "ADJ" and dep["deprel"] == "amod" and head["upos"] == "NOUN":
                ordered = [head, dep]
                add("ar.nominal.adjective_modifier", ordered,
                    {"HEAD": head["form"], "MODIFIER": dep["form"]})

            if lang == "en" and dep["upos"] in {"NOUN", "PROPN"} and dep["deprel"] == "compound" and head["upos"] in {"NOUN", "PROPN"} and dep["id"] < head["id"]:
                add("en.compound.noun_noun", [dep, head],
                    {"MODIFIER": dep["form"], "HEAD": head["form"]})

            if lang == "en" and dep["upos"] in {"NOUN", "PROPN"} and dep["deprel"] == "nmod:of" and head["upos"] in {"NOUN", "PROPN"}:
                adp = _case_child(ts, dep["id"])
                if adp and adp["form"].casefold() == "of" and head["id"] < adp["id"] < dep["id"]:
                    dh, dd = _det_child(ts, head["id"]), _det_child(ts, dep["id"])
                    ordered = [x for x in (dh, head, adp, dd, dep) if x]
                    ordered.sort(key=lambda x: x["id"])
                    add("en.genitive.of_phrase", ordered,
                        {"GENITIVE_HEAD": head["form"], "GENITIVE_DEPENDENT": dep["form"]})

            if lang == "ar" and dep["upos"] == "NOUN" and dep["deprel"].startswith("nmod") and head["upos"] == "NOUN":
                if head["id"] + 1 == dep["id"]:
                    add("ar.genitive.idafa", [head, dep],
                        {"GENITIVE_HEAD": head["form"], "GENITIVE_DEPENDENT": dep["form"]})

            if dep["upos"] == "NOUN" and dep["deprel"].startswith(("nmod", "obl")) and head["upos"] in {"NOUN", "PROPN"}:
                adp = _case_child(ts, dep["id"])
                if adp and adp["form"].casefold() != "of" and head["id"] < adp["id"] < dep["id"]:
                    dh, dd = _det_child(ts, head["id"]), _det_child(ts, dep["id"])
                    ordered = [x for x in (dh, head, adp, dd, dep) if x]
                    ordered.sort(key=lambda x: x["id"])
                    con = f"{lang}.prepositional.nominal_modifier"
                    add(con, ordered, {"HEAD": head["form"],
                                       "LOCATION": adp["form"] + " " + dep["form"]})

        # Temporal profile: gold UD subject + adverbial modifier attached to one verb.
        for verb in ts:
            if verb["upos"] != "VERB":
                continue
            subjects = [t for t in ts if t["head"] == verb["id"]
                        and t["deprel"].startswith("nsubj")
                        and t["upos"] == ("PROPN" if lang == "en" else "NOUN")]
            adverbs = [t for t in ts if t["head"] == verb["id"]
                       and t["deprel"].startswith("advmod") and t["upos"] == "ADV"]
            for subject in subjects:
                for adv in adverbs:
                    ordered = [subject, verb, adv] if lang == "en" else [verb, subject, adv]
                    con = f"{lang}.temporal.adverbial_modifier"
                    event = subject["form"] + " " + verb["form"] if lang == "en" else verb["form"] + " " + subject["form"]
                    add(con, ordered, {"EVENT": event, "TIME": adv["form"]})
    return cases


def evaluate(cases: list[dict]) -> dict:
    by_profile = defaultdict(lambda: {"gold_cases": 0, "exact_matches": 0,
                                       "abstentions": 0, "wrong_candidates": 0})
    for case in cases:
        key = f"{case['language']}/{case['construction']}"
        row = by_profile[key]
        row["gold_cases"] += 1
        result = analyze(case["text"], case["language"])
        if (result.get("status") == "CANDIDATE"
                and result.get("construction_id") == case["construction"]
                and result.get("role_bindings") == case["expected_roles"]):
            row["exact_matches"] += 1
        elif result.get("status") == "ABSTAIN":
            row["abstentions"] += 1
        else:
            row["wrong_candidates"] += 1
    for row in by_profile.values():
        n = row["gold_cases"]
        row["exact_recall"] = row["exact_matches"] / n if n else None
    return {
        "evaluation_type": "INDEPENDENT_UD_STRUCTURAL_PROXY_RECALL",
        "precision_measured": False,
        "semantic_role_gold": False,
        "construction_promotion_allowed": False,
        "runtime_capability_state": "CANDIDATE_ONLY",
        "profiles": dict(sorted(by_profile.items())),
        "gold_case_count": len(cases),
    }


def run() -> dict:
    dataset_meta, all_cases = {}, []
    for lang, spec in DATASETS.items():
        payload = download_dataset(lang)
        sentences = parse_conllu(payload)
        if len(sentences) != spec["sentences"]:
            raise ValueError(f"{lang} expected 1000 sentences, got {len(sentences)}")
        cases = extract_gold(sentences, lang)
        all_cases.extend(cases)
        dataset_meta[lang] = {
            "repository": f"UniversalDependencies/{spec['repo']}",
            "commit": spec["commit"], "file": spec["file"],
            "git_blob_sha1": spec["blob_sha"], "license": "CC BY-SA 3.0",
            "sentences": len(sentences),
            "syntactic_words": sum(len(s["tokens"]) for s in sentences),
            "eligible_structural_cases": len(cases),
        }
    report = evaluate(all_cases)
    report["datasets"] = dataset_meta
    report["limitations"] = [
        "UD dependency labels are independent syntactic annotations, not USG semantic-role gold labels.",
        "Arabic PUD UPOS and dependency relations were converted to UD from prior annotation; conversion is not a fresh independent semantic adjudication.",
        "The current candidate lexicon is closed and derived from USG development fixtures; unseen vocabulary is not tested.",
        "Only explicitly mapped structural profiles are scored; Arabic lexicalized compound semantics are not inferable from UD syntax alone.",
        "Recall is measured on eligible gold structures; precision and full-sentence coverage are not measured.",
        "All outputs remain candidate-only; this report cannot satisfy semantic benchmark acceptance by itself.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
