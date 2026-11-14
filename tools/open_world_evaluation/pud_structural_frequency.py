"""Reproducible structural-frequency diagnostics for pinned bilingual PUD.

Counts are syntactic Universal Dependencies proxies over the complete pinned
PUD source files. They are not USG semantic gold, semantic-role labels, or
measures of interpreter correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable
from urllib.request import Request, urlopen

from .pud_naturalistic_pilot import LICENSE, LICENSE_URL, SOURCES, select_sentences

REPORT_CONTRACT = "USG-PUD-STRUCTURAL-FREQUENCY/0.1.0"
MAX_SOURCE_BYTES = 4_000_000
DOWNLOAD_TIMEOUT_SECONDS = 45


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "USG-PUD-Structural-Frequency/0.1.0"})
    with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"PUD source download failed ({response.status}): {url}")
        payload = response.read(MAX_SOURCE_BYTES + 1)
    if len(payload) > MAX_SOURCE_BYTES:
        raise ValueError(f"PUD source exceeds the {MAX_SOURCE_BYTES}-byte safety limit")
    return payload


def parse_conllu_structures(payload: str) -> list[dict[str, Any]]:
    """Parse sentence metadata and integer-ID syntactic tokens from CoNLL-U."""
    rows: list[dict[str, Any]] = []
    for block in re.split(r"\n\s*\n", payload.strip()):
        metadata: dict[str, str] = {}
        tokens: list[dict[str, Any]] = []
        for line in block.splitlines():
            if not line:
                continue
            if line.startswith("#"):
                if "=" in line:
                    key, value = line[1:].split("=", 1)
                    metadata[key.strip()] = value.strip()
                continue
            columns = line.split("\t")
            if len(columns) < 8 or not columns[0].isdigit():
                # Skip multiword-token ranges and empty nodes; retain only words.
                continue
            try:
                token_id = int(columns[0])
                head = int(columns[6])
            except ValueError as exc:
                raise ValueError(f"invalid integer token/head ID in CoNLL-U row: {line}") from exc
            tokens.append({
                "id": token_id,
                "form": columns[1],
                "lemma": columns[2],
                "upos": columns[3],
                "head": head,
                "deprel": columns[7],
            })
        sentence_id = metadata.get("sent_id")
        text = metadata.get("text")
        if sentence_id and text is not None:
            rows.append({"sentence_id": sentence_id, "text": text, "tokens": tokens})
    return rows


def _rate(count: int, denominator: int) -> float | None:
    return (count / denominator) if denominator else None


def analyze_language(
    payload: bytes,
    *,
    language: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    """Count sentence-level UD construction proxies after the pilot's screen."""
    decoded = payload.decode("utf-8", errors="strict")
    parsed = parse_conllu_structures(decoded)
    selectable = [{"sentence_id": row["sentence_id"], "text": row["text"]} for row in parsed]
    selected, selection_stats = select_sentences(
        selectable,
        language=language,
        sample_count=len(selectable),
        seed="USG-PUD-STRUCTURAL-FREQUENCY-0.1.0",
    )
    sentence_ids = [row["sentence_id"] for row in parsed]
    if len(set(sentence_ids)) != len(sentence_ids):
        raise ValueError("duplicate sent_id values in pinned CoNLL-U source")
    selected_ids = {row["sentence_id"] for row in selected}
    selected_rows = [row for row in parsed if row["sentence_id"] in selected_ids]

    metric_names = (
        "relative_clause_anywhere",
        "active_transitive_root",
        "copular_predicate_root",
        "clause_complement_root",
        "clause_complement_anywhere",
        "passive_verb_root",
        "adverbial_clause_root",
        "adverbial_clause_anywhere",
        "coordination_root",
        "coordination_anywhere",
    )
    counts = {name: 0 for name in metric_names}
    order_counts = {"SVO": 0, "VSO": 0, "VOS": 0, "OTHER": 0}
    invalid_root_count = 0
    analyzed_sentence_count = 0

    for row in selected_rows:
        tokens = row["tokens"]
        roots = [token for token in tokens if token["head"] == 0]
        if len(roots) != 1:
            invalid_root_count += 1
            continue
        analyzed_sentence_count += 1
        root = roots[0]
        root_children = [token for token in tokens if token["head"] == root["id"]]
        root_deprels = {token["deprel"] for token in root_children}
        all_deprels = {token["deprel"] for token in tokens}

        if "acl:relcl" in all_deprels:
            counts["relative_clause_anywhere"] += 1

        subjects = [
            token for token in root_children
            if token["deprel"] in {"nsubj", "nsubj:outer"}
        ]
        objects = [token for token in root_children if token["deprel"] == "obj"]
        active_transitive = root["upos"] == "VERB" and bool(subjects) and bool(objects)
        if active_transitive:
            counts["active_transitive_root"] += 1
            subject = min(subjects, key=lambda token: token["id"])
            obj = min(objects, key=lambda token: token["id"])
            if subject["id"] < root["id"] < obj["id"]:
                order_counts["SVO"] += 1
            elif root["id"] < subject["id"] < obj["id"]:
                order_counts["VSO"] += 1
            elif root["id"] < obj["id"] < subject["id"]:
                order_counts["VOS"] += 1
            else:
                order_counts["OTHER"] += 1

        if "cop" in root_deprels:
            counts["copular_predicate_root"] += 1
        if root_deprels.intersection({"ccomp", "xcomp"}):
            counts["clause_complement_root"] += 1
        if all_deprels.intersection({"ccomp", "xcomp"}):
            counts["clause_complement_anywhere"] += 1

        passive_root = root["upos"] == "VERB" and bool(
            root_deprels.intersection({"nsubj:pass", "csubj:pass", "aux:pass"})
        )
        if passive_root:
            counts["passive_verb_root"] += 1

        if "advcl" in root_deprels:
            counts["adverbial_clause_root"] += 1
        if "advcl" in all_deprels:
            counts["adverbial_clause_anywhere"] += 1
        if "conj" in root_deprels:
            counts["coordination_root"] += 1
        if "conj" in all_deprels:
            counts["coordination_anywhere"] += 1

    constructions = {
        name: {
            "count": count,
            "denominator": analyzed_sentence_count,
            "rate": _rate(count, analyzed_sentence_count),
        }
        for name, count in counts.items()
    }
    order_total = sum(order_counts.values())
    surface_order = {
        name: {
            "count": count,
            "denominator": order_total,
            "rate": _rate(count, order_total),
        }
        for name, count in order_counts.items()
    }
    return {
        "language": language,
        "source": {
            "repository": source["repository"],
            "commit": source["commit"],
            "file": source["file"],
            "blob_sha": source["blob_sha"],
            "content_sha256": _sha256(payload),
            "source_url": (
                f"https://github.com/{source['repository']}/blob/"
                f"{source['commit']}/{source['file']}"
            ),
            "sentence_count_declared": source.get("sentence_count"),
        },
        "population": {
            "kind": "full_pinned_pud_source",
            "genre": ["news", "wikipedia"],
            "source_sentence_count": selection_stats["source_sentence_count"],
            "privacy_rejected_count": selection_stats["privacy_rejected_count"],
            "duplicate_count": selection_stats["duplicate_count"],
            "unique_screened_sentence_count": selection_stats["unique_after_deduplication"],
            "analyzed_sentence_count": analyzed_sentence_count,
            "invalid_root_count": invalid_root_count,
        },
        "construction_counts": constructions,
        "active_transitive_surface_order": surface_order,
    }


def build_report(
    source_manifest_path: Path,
    *,
    fetcher: Callable[[str], bytes] = _download,
) -> dict[str, Any]:
    manifest_bytes = source_manifest_path.read_bytes()
    source_manifest = json.loads(manifest_bytes.decode("utf-8"))
    if source_manifest.get("license") != LICENSE:
        raise ValueError("source manifest does not declare the expected CC BY-SA 3.0 license")
    if source_manifest.get("semantic_gold", {}).get("available") is not False:
        raise ValueError("PUD structural diagnostics require explicit no-semantic-gold status")
    if source_manifest.get("privacy_review", {}).get("status") != "approved_for_bounded_internal_evaluation":
        raise ValueError("PUD source manifest lacks the bounded privacy-review status")

    manifest_sources = source_manifest.get("sources", {})
    languages: dict[str, Any] = {}
    for language in ("en", "ar"):
        expected = SOURCES[language]
        observed = manifest_sources.get(language)
        if not isinstance(observed, dict):
            raise ValueError(f"source manifest is missing {language} provenance")
        for key in ("repository", "commit", "file", "blob_sha"):
            if observed.get(key) != expected[key]:
                raise ValueError(f"{language} source manifest mismatch for {key}")
        url = (
            f"https://raw.githubusercontent.com/{expected['repository']}/"
            f"{expected['commit']}/{expected['file']}"
        )
        payload = fetcher(url)
        actual_blob = git_blob_sha1(payload)
        if actual_blob != expected["blob_sha"]:
            raise ValueError(f"{language} PUD Git blob SHA mismatch: {actual_blob}")
        actual_sha256 = _sha256(payload)
        if observed.get("content_sha256") != actual_sha256:
            raise ValueError(f"{language} PUD content SHA-256 differs from source manifest")
        result = analyze_language(payload, language=language, source={
            **expected,
            "sentence_count": observed.get("sentence_count"),
        })
        declared = observed.get("sentence_count")
        if declared is not None and result["population"]["source_sentence_count"] != declared:
            raise ValueError(f"{language} PUD sentence count differs from source manifest")
        languages[language] = result

    return {
        "contract": REPORT_CONTRACT,
        "evidence_type": "ud_syntactic_proxy_not_semantic_gold",
        "dataset_id": source_manifest.get("dataset_id"),
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "attribution": "Universal Dependencies contributors; see each pinned upstream README for full attribution.",
        "source_manifest_sha256": _sha256(manifest_bytes),
        "analysis_scope": (
            "Full pinned English and Arabic PUD source files after the same email/URL "
            "screening and within-language deduplication used by the naturalistic pilot; "
            "not limited to the campaign's sampled sentences."
        ),
        "interpretation_boundary": (
            "Dependency/POS construction counts are descriptive syntactic proxies. "
            "They are not USG semantic roles, semantic frames, semantic gold, or "
            "evidence of interpreter correctness."
        ),
        "methods": {
            "relative_clause_anywhere": "At least one token has DEPREL=acl:relcl.",
            "active_transitive_root": (
                "The single root has UPOS=VERB and direct children with DEPREL=nsubj "
                "or nsubj:outer and DEPREL=obj."
            ),
            "copular_predicate_root": "The single root has a direct cop child.",
            "clause_complement_root": "The single root has a direct ccomp or xcomp child.",
            "clause_complement_anywhere": "At least one ccomp or xcomp token occurs anywhere.",
            "passive_verb_root": (
                "The single root has UPOS=VERB and a direct nsubj:pass, "
                "csubj:pass, or aux:pass child."
            ),
            "adverbial_clause_root": "The single root has a direct advcl child.",
            "adverbial_clause_anywhere": "At least one advcl token occurs anywhere.",
            "coordination_root": "The single root has a direct conj child.",
            "coordination_anywhere": "At least one conj token occurs anywhere.",
            "active_transitive_surface_order": (
                "Order of the first direct nsubj/nsubj:outer child, root, and first direct obj child."
            ),
        },
        "languages": languages,
        "privacy_limitations": [
            "The pilot's email and URL pattern screen is reused; it is not a comprehensive personal-data detector.",
            "Public proper names and public-event references remain in the source treebanks.",
            "No sentence text or token-level examples are written to this report.",
        ],
        "translation_caveat": source_manifest.get("translation_profile", {}),
        "semantic_gold": {
            "available": False,
            "reason": "PUD UPOS/dependency annotations are not independent USG semantic-frame or role gold.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.source_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_CONTRACT} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
