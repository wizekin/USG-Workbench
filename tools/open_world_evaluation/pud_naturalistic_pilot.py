"""Generate a small, provenance-preserving naturalistic PUD evaluation population.

The PUD treebanks are used only as unlabeled input text for evaluation. Their
UPOS/dependency annotations are not treated as USG semantic gold or training
labels. The source files are pinned to immutable Git commits and carry
CC BY-SA 3.0 attribution/share-alike requirements.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import unicodedata
from typing import Any
from urllib.request import Request, urlopen

from .generate_scenarios import ROOT, _read_targets
from .validate_protocol import validate_instance

GENERATOR_ID = "usg-naturalistic-pud-pilot"
GENERATOR_VERSION = "0.1.0"
SEED = "USG-NATURALISTIC-PUD-PILOT-0.1.0"
LICENSE = "CC BY-SA 3.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/"
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")

SOURCES = {
    "en": {
        "repository": "UniversalDependencies/UD_English-PUD",
        "commit": "a697bab43d4111073356de0df5802488bca3de7e",
        "file": "en_pud-ud-test.conllu",
        "blob_sha": "828f827759e7a9f89a8c42bfe79402dd65db71c3",
        "readme_sha": "15ab0c810de4c223663e25f956c9225e34d376fc",
        "license_blob_sha": "a0bd8baeb667daae1407869f3152489fab3001de",
        "treebank": "UD_English-PUD",
        "language": "en",
    },
    "ar": {
        "repository": "UniversalDependencies/UD_Arabic-PUD",
        "commit": "c606299bc9eb8baa6c61c8dd3efc9a0fbf73aa87",
        "file": "ar_pud-ud-test.conllu",
        "blob_sha": "075361d5425ea0d43ff6b4f5459a306e26df6fbf",
        "readme_sha": "4ea76ca71d04fe03c7da6a1afa94833d837e89a7",
        "license_blob_sha": "a0bd8baeb667daae1407869f3152489fab3001de",
        "treebank": "UD_Arabic-PUD",
        "language": "ar",
    },
}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _download(url: str, timeout: int = 45) -> bytes:
    request = Request(url, headers={"User-Agent": "USG-Naturalistic-Pilot/0.1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"download failed ({response.status}): {url}")
        return response.read()


def parse_conllu_sentences(payload: str) -> list[dict[str, str]]:
    sentences: list[dict[str, str]] = []
    for block in re.split(r"\n\s*\n", payload.strip()):
        metadata: dict[str, str] = {}
        for line in block.splitlines():
            if not line.startswith("#") or "=" not in line:
                continue
            key, value = line[1:].split("=", 1)
            metadata[key.strip()] = value.strip()
        sentence_id = metadata.get("sent_id")
        text = metadata.get("text")
        if sentence_id and text:
            sentences.append({"sentence_id": sentence_id, "text": text})
    return sentences


def _normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def screen_public_sentence(text: str) -> tuple[bool, str | None]:
    if not _normalized_text(text):
        return False, "empty_text"
    if EMAIL_RE.search(text):
        return False, "email_pattern"
    if URL_RE.search(text):
        return False, "url_pattern"
    return True, None


def select_sentences(
    sentences: list[dict[str, str]],
    *,
    language: str,
    sample_count: int,
    seed: str = SEED,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    deduplicated: dict[str, dict[str, str]] = {}
    duplicate_count = 0
    rejected: dict[str, int] = {}
    for item in sentences:
        text = item.get("text", "")
        allowed, reason = screen_public_sentence(text)
        if not allowed:
            rejected[reason or "unknown"] = rejected.get(reason or "unknown", 0) + 1
            continue
        key = _normalized_text(text)
        if key in deduplicated:
            duplicate_count += 1
            continue
        deduplicated[key] = item
    ranked = sorted(
        deduplicated.values(),
        key=lambda item: hashlib.sha256(
            f"{seed}:{language}:{item['sentence_id']}".encode("utf-8")
        ).hexdigest(),
    )
    selected = ranked[:sample_count]
    return selected, {
        "source_sentence_count": len(sentences),
        "unique_after_deduplication": len(deduplicated),
        "duplicate_count": duplicate_count,
        "selected_count": len(selected),
        "privacy_rejected_count": sum(rejected.values()),
        "privacy_rejection_reasons": rejected,
    }


def build_naturalistic_cases(
    sentence_groups: dict[str, list[dict[str, str]]],
    *,
    targets: list[dict[str, Any]],
    sample_per_language: int,
    created_at: str,
    retrieved_at: str,
    source_file_digests: dict[str, str],
    seed: str = SEED,
    target_matrix: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 1 <= sample_per_language <= 1000:
        raise ValueError("sample_per_language must be between 1 and 1000")
    master_seed = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    selected_by_language: dict[str, list[dict[str, str]]] = {}
    selection_stats: dict[str, Any] = {}
    for language in ("en", "ar"):
        selected, stats = select_sentences(
            sentence_groups.get(language, []),
            language=language,
            sample_count=sample_per_language,
            seed=seed,
        )
        if not selected:
            raise ValueError(f"no privacy-screened PUD sentences available for {language}")
        selected_by_language[language] = selected
        selection_stats[language] = stats

    cases: list[dict[str, Any]] = []
    for language in ("en", "ar"):
        source = SOURCES[language]
        source_url = (
            f"https://github.com/{source['repository']}/blob/{source['commit']}/{source['file']}"
        )
        attribution = (
            f"{source['treebank']} contributors, Universal Dependencies; "
            f"news/Wikipedia text; licensed under {LICENSE}; see upstream README and LICENSE.txt."
        )
        for sentence in selected_by_language[language]:
            for target_index, target in enumerate(targets if target_matrix else targets[:1]):
                sentence_id = sentence["sentence_id"]
                text = sentence["text"]
                suffix = hashlib.sha256(
                    f"{seed}:{language}:{sentence_id}:{target['component_id']}".encode("utf-8")
                ).hexdigest()[:12].upper()
                case_id = f"OW-NAT-PUD-{language.upper()}-{suffix}"
                case_seed = hashlib.sha256(
                    f"{master_seed}:{language}:{sentence_id}:{target['component_id']}".encode("utf-8")
                ).hexdigest()
                source_info = {
                    "kind": "open_license_dataset",
                    "source_id": f"{source['treebank']}:{sentence_id}",
                    "source_url": source_url,
                    "retrieved_at": retrieved_at,
                    "license_status": "approved",
                    "redistribution_allowed": True,
                    "privacy_review_status": "approved",
                    "attribution": attribution,
                    "content_digest": source_file_digests[language],
                    "transformations": [
                        "extract the CoNLL-U # text field verbatim",
                        "select deterministically by SHA-256 rank from the pinned source file",
                        "deduplicate by Unicode NFKC plus whitespace normalization",
                        "exclude sentences matching email or URL direct-contact patterns",
                        "do not use UD annotation columns as USG semantic gold or training labels",
                    ],
                }
                case = {
                    "schema_version": "1.0.0",
                    "case_id": case_id,
                    "population": "naturalistic",
                    "created_at": created_at,
                    "generator": {
                        "id": GENERATOR_ID,
                        "version": GENERATOR_VERSION,
                        "seed_mode": "explicit",
                        "master_seed": master_seed,
                        "case_seed": case_seed,
                        "generation_trace": [
                            f"population=naturalistic",
                            f"source={source['treebank']}",
                            f"source_commit={source['commit']}",
                            f"sentence_id={sentence_id}",
                            f"target={target['component_id']}",
                        ],
                        "mutation_ops": [],
                    },
                    "source": source_info,
                    "input": {
                        "text": text,
                        "utf8_sha256": _sha256(text.encode("utf-8")),
                        "language_hint": language,
                        "prior_turns": [],
                    },
                    "target": {
                        "component_id": target["component_id"],
                        "component_version": target["component_version"],
                        "entry_point": target["entry_point"],
                        "interface": target["interface"],
                        "contract_versions": target.get("contract_versions", []),
                        **(
                            {"resource_manifest_sha256": target["resource_manifest_sha256"]}
                            if target.get("resource_manifest_sha256") else {}
                        ),
                    },
                    "taxonomy": {
                        "labels": ["naturalistic_news_wiki"],
                        "unclassified": True,
                    },
                    "oracle": {"type": "none", "independent": False},
                    "resource_limits": {
                        "wall_time_seconds": float(target.get("resource_limits", {}).get("wall_time_seconds", 15)),
                        "memory_megabytes": int(target.get("resource_limits", {}).get("memory_megabytes", 512)),
                        "max_input_bytes": 100_000,
                        "network_access": False,
                    },
                }
                errors = validate_instance("scenario", case)
                if errors:
                    raise ValueError(f"invalid naturalistic case {case_id}: " + "; ".join(errors))
                cases.append(case)

    source_manifest = {
        "contract": "USG-NATURALISTIC-CORPUS-MANIFEST/0.1.0",
        "dataset_id": "UD-PUD-EN-AR",
        "population": "naturalistic",
        "usage": "evaluation_only_unlabeled_input",
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "retrieved_at": retrieved_at,
        "sample_per_language_requested": sample_per_language,
        "target_matrix": target_matrix,
        "target_ids": [item["component_id"] for item in targets if target_matrix] or [targets[0]["component_id"]],
        "sources": {
            language: {
                **SOURCES[language],
                "source_url": (
                    f"https://github.com/{SOURCES[language]['repository']}/blob/"
                    f"{SOURCES[language]['commit']}/{SOURCES[language]['file']}"
                ),
                "license_url": LICENSE_URL,
                "content_sha256": source_file_digests[language],
                "attribution": "Universal Dependencies contributors; see the pinned upstream README for full contributor attribution.",
                "genre": ["news", "wikipedia"],
                "sentence_count": 1000,
            }
            for language in ("en", "ar")
        },
        "selection": selection_stats,
        "privacy_review": {
            "status": "approved_for_bounded_internal_evaluation",
            "scope": "Public news/Wikipedia treebank text only; no user-submitted or private chat data is included.",
            "checks": [
                "source repositories and CC BY-SA 3.0 license files were inspected",
                "email and URL direct-contact patterns are screened and excluded",
                "deduplication is applied within each language",
                "no sensitive-attribute inference or user profiling is performed",
            ],
            "known_limitations": [
                "Public proper names and public-event references are retained as part of the source text.",
                "The pattern screen is not a comprehensive personal-data detector.",
                "This is an internal evaluation pilot, not a general-purpose personal-data corpus.",
            ],
        },
        "semantic_gold": {
            "available": False,
            "reason": "PUD POS/dependency annotations are not independent USG semantic-frame or semantic-role gold.",
        },
        "translation_profile": {
            "english": "PUD contains news/Wikipedia sentences; 750 are originally English and 250 are translations from other European languages.",
            "arabic": "PUD is a parallel news/Wikipedia set; a substantial portion is translated via English and is not representative of all native MSA usage.",
        },
        "case_count": len(cases),
        "cases_jsonl_sha256": None,
        "redistribution_notice": (
            "The verbatim sentence excerpts and scenario artifacts derived from them are distributed under CC BY-SA 3.0 "
            "with attribution and share-alike terms. See ATTRIBUTION.md and LICENSE.txt."
        ),
    }
    return cases, source_manifest


def generate_pilot(
    *,
    sample_per_language: int,
    output_dir: Path,
    target_ids: list[str] | None = None,
    target_matrix: bool = True,
    created_at: str | None = None,
) -> dict[str, Any]:
    retrieved_at = _utc_now()
    created_at = created_at or retrieved_at
    targets = _read_targets(ROOT / "tools/open_world_evaluation/target_profiles.json")
    if target_ids:
        unknown = set(target_ids) - {item["component_id"] for item in targets}
        if unknown:
            raise ValueError("unknown target IDs: " + ", ".join(sorted(unknown)))
        targets = [item for item in targets if item["component_id"] in set(target_ids)]
    if not targets:
        raise ValueError("at least one target must be selected")

    sentence_groups: dict[str, list[dict[str, str]]] = {}
    source_digests: dict[str, str] = {}
    license_text = ""
    for language, source in SOURCES.items():
        raw_url = (
            f"https://raw.githubusercontent.com/{source['repository']}/"
            f"{source['commit']}/{source['file']}"
        )
        payload = _download(raw_url)
        source_digests[language] = _sha256(payload)
        sentence_groups[language] = parse_conllu_sentences(payload.decode("utf-8"))
        if not license_text:
            license_url = (
                f"https://raw.githubusercontent.com/{source['repository']}/"
                f"{source['commit']}/LICENSE.txt"
            )
            license_text = _download(license_url).decode("utf-8")

    cases, source_manifest = build_naturalistic_cases(
        sentence_groups,
        targets=targets,
        sample_per_language=sample_per_language,
        created_at=created_at,
        retrieved_at=retrieved_at,
        source_file_digests=source_digests,
        target_matrix=target_matrix,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_path = output_dir / "scenario-cases.jsonl"
    if cases_path.exists():
        raise FileExistsError(f"refusing to overwrite {cases_path}")
    payload = ("\n".join(json.dumps(case, ensure_ascii=False, sort_keys=True) for case in cases) + "\n").encode("utf-8")
    cases_path.write_bytes(payload)
    source_manifest["cases_jsonl_sha256"] = _sha256(payload)
    source_manifest_path = output_dir / "source-manifest.json"
    source_manifest_path.write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "LICENSE.txt").write_text(license_text, encoding="utf-8")
    attribution = [
        "# PUD Naturalistic Pilot Attribution",
        "",
        "This evaluation artifact contains verbatim sentence excerpts from:",
        "",
        "- UD_English-PUD, Universal Dependencies contributors",
        "- UD_Arabic-PUD, Universal Dependencies contributors",
        "",
        "Both source treebanks declare **Creative Commons Attribution-ShareAlike 3.0 International (CC BY-SA 3.0)**.",
        "The selected excerpts and scenario artifacts derived from them are shared under the same license.",
        "",
        "Source commits and complete attribution: see `source-manifest.json` and the pinned upstream READMEs.",
        "The corpus is used as unlabeled evaluation input only. UD syntactic annotations are not USG semantic gold.",
        "",
    ]
    (output_dir / "ATTRIBUTION.md").write_text("\n".join(attribution), encoding="utf-8")
    manifest = {
        "manifest_version": "1.0.0",
        "generator_id": GENERATOR_ID,
        "generator_version": GENERATOR_VERSION,
        "created_at": created_at,
        "seed_mode": "explicit",
        "master_seed": hashlib.sha256(SEED.encode("utf-8")).hexdigest(),
        "population": "naturalistic",
        "target_matrix": target_matrix,
        "case_count": len(cases),
        "target_ids": [item["component_id"] for item in targets],
        "jsonl_sha256": _sha256(payload),
        "source_manifest": "source-manifest.json",
    }
    (output_dir / "generation-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "case_count": len(cases),
        "source_manifest": str(source_manifest_path),
        "cases": str(cases_path),
        "generation_manifest": str(output_dir / "generation-manifest.json"),
        "license": LICENSE,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a pinned, licensed PUD naturalistic evaluation pilot.")
    parser.add_argument("--sample-per-language", type=int, default=50)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target", action="append", dest="targets")
    parser.add_argument("--no-target-matrix", action="store_true")
    parser.add_argument("--created-at")
    args = parser.parse_args(argv)
    try:
        result = generate_pilot(
            sample_per_language=args.sample_per_language,
            output_dir=args.output_dir,
            target_ids=args.targets,
            target_matrix=not args.no_target_matrix,
            created_at=args.created_at,
        )
    except (OSError, ValueError, RuntimeError, UnicodeDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
