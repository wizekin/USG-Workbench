"""Reproducible bilingual PUD structural-frequency diagnostics.

Counts are syntactic proxies derived from pinned UD dependency/POS annotations.
They are not USG semantic roles, semantic frames, or semantic gold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from .pud_naturalistic_pilot import LICENSE, SOURCES

CONTRACT = "USG-PUD-STRUCTURAL-FREQUENCY/0.1.0"
CONSTRUCTION_RULES: dict[str, dict[str, Any]] = {
    "relative_clause_attachment": {
        "relations": ["acl:relcl"],
        "unit": "sentence_presence_and_relation_instances",
        "description": "A sentence contains one or more acl:relcl dependency arcs.",
    },
    "active_transitive_root": {
        "relations": ["root VERB with direct obj and no passive marker"],
        "unit": "sentence_presence_and_root_instances",
        "description": "A verbal root has a direct obj dependent and no UD passive marker.",
    },
    "copular_predicate": {
        "relations": ["cop"],
        "unit": "sentence_presence_and_predicate_heads",
        "description": "A predicate head has a dependent with deprel=cop.",
    },
    "clause_complement": {
        "relations": ["ccomp", "xcomp"],
        "unit": "sentence_presence_and_relation_instances",
        "description": "A sentence contains one or more ccomp or xcomp arcs.",
    },
    "passive_root": {
        "relations": ["Voice=Pass", "aux:pass", "nsubj:pass", "csubj:pass"],
        "unit": "sentence_presence_and_root_instances",
        "description": "A verbal root has an explicit UD passive feature or dependent marker.",
    },
    "adverbial_clause": {
        "relations": ["advcl"],
        "unit": "sentence_presence_and_relation_instances",
        "description": "A sentence contains one or more advcl dependency arcs.",
    },
    "coordination": {
        "relations": ["conj"],
        "unit": "sentence_presence_and_relation_instances",
        "description": "A sentence contains one or more conj dependency arcs.",
    },
}


def parse_conllu_structure(payload: str) -> list[dict[str, Any]]:
    """Parse syntactic word rows, excluding multiword-token and empty-node rows."""
    sentences: list[dict[str, Any]] = []
    for block_index, block in enumerate(re.split(r"\n\s*\n", payload.strip()), start=1):
        metadata: dict[str, str] = {}
        tokens: list[dict[str, Any]] = []
        for line_number, line in enumerate(block.splitlines(), start=1):
            if not line:
                continue
            if line.startswith("#"):
                if "=" in line:
                    key, value = line[1:].split("=", 1)
                    metadata[key.strip()] = value.strip()
                continue
            fields = line.split("\t")
            if len(fields) != 10:
                raise ValueError(f"CoNLL-U row must have 10 fields (block {block_index}, line {line_number})")
            raw_id = fields[0]
            if "-" in raw_id or "." in raw_id:
                continue
            try:
                token_id = int(raw_id)
                head = int(fields[6])
            except ValueError as exc:
                raise ValueError(f"invalid integer ID/HEAD (block {block_index}, line {line_number})") from exc
            feats: dict[str, str] = {}
            if fields[5] != "_":
                for item in fields[5].split("|"):
                    key, sep, value = item.partition("=")
                    if sep:
                        feats[key] = value
            tokens.append({
                "id": token_id,
                "form": fields[1],
                "upos": fields[3],
                "feats": feats,
                "head": head,
                "deprel": fields[7],
            })
        if tokens:
            sentences.append({
                "sentence_id": metadata.get("sent_id", str(block_index)),
                "text": metadata.get("text", ""),
                "tokens": tokens,
            })
    return sentences


def _is_passive_root(root: dict[str, Any], children: list[dict[str, Any]]) -> bool:
    if root["feats"].get("Voice") == "Pass":
        return True
    return any(token["deprel"] in {"aux:pass", "nsubj:pass", "csubj:pass"} for token in children)


def summarize_language(sentences: list[dict[str, Any]]) -> dict[str, Any]:
    """Count sentence presence and dependency instances for fixed UD proxy rules."""
    if not sentences:
        raise ValueError("cannot compute frequencies for an empty PUD population")

    sentence_counts = {key: 0 for key in CONSTRUCTION_RULES}
    instance_counts = {key: 0 for key in CONSTRUCTION_RULES}
    clause_subtype_sentence_counts = {"ccomp": 0, "xcomp": 0}
    clause_subtype_instance_counts = {"ccomp": 0, "xcomp": 0}
    token_count = 0

    for sentence in sentences:
        tokens = sentence["tokens"]
        token_count += len(tokens)
        children: dict[int, list[dict[str, Any]]] = {}
        for token in tokens:
            children.setdefault(token["head"], []).append(token)

        clause_subtypes = {
            relation: sum(t["deprel"] == relation for t in tokens)
            for relation in ("ccomp", "xcomp")
        }
        matches: dict[str, int] = {
            "relative_clause_attachment": sum(t["deprel"] == "acl:relcl" for t in tokens),
            "copular_predicate": sum(any(c["deprel"] == "cop" for c in children.get(t["id"], [])) for t in tokens),
            "clause_complement": sum(clause_subtypes.values()),
            "adverbial_clause": sum(t["deprel"] == "advcl" for t in tokens),
            "coordination": sum(t["deprel"] == "conj" for t in tokens),
            "active_transitive_root": 0,
            "passive_root": 0,
        }
        for root in tokens:
            if root["head"] != 0 or root["upos"] != "VERB":
                continue
            root_children = children.get(root["id"], [])
            passive = _is_passive_root(root, root_children)
            if passive:
                matches["passive_root"] += 1
            elif any(child["deprel"] == "obj" for child in root_children):
                matches["active_transitive_root"] += 1

        for relation, count in clause_subtypes.items():
            clause_subtype_instance_counts[relation] += count
            if count:
                clause_subtype_sentence_counts[relation] += 1

        for key, count in matches.items():
            instance_counts[key] += count
            if count:
                sentence_counts[key] += 1

    denominator = len(sentences)
    constructions: dict[str, Any] = {}
    for key, rules in CONSTRUCTION_RULES.items():
        present = sentence_counts[key]
        construction = {
            **rules,
            "sentence_count": present,
            "instance_count": instance_counts[key],
            "sentence_rate": present / denominator,
            "per_1000_sentences": present * 1000 / denominator,
            "instances_per_1000_sentences": instance_counts[key] * 1000 / denominator,
        }
        if key == "clause_complement":
            construction["subtypes"] = {
                relation: {
                    "sentence_count": clause_subtype_sentence_counts[relation],
                    "instance_count": clause_subtype_instance_counts[relation],
                    "sentence_rate": clause_subtype_sentence_counts[relation] / denominator,
                    "per_1000_sentences": clause_subtype_sentence_counts[relation] * 1000 / denominator,
                    "instances_per_1000_sentences": clause_subtype_instance_counts[relation] * 1000 / denominator,
                }
                for relation in ("ccomp", "xcomp")
            }
        constructions[key] = construction

    return {
        "sentence_count": denominator,
        "token_count": token_count,
        "constructions": constructions,
    }


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _download_pinned_source(language: str, timeout: int = 45) -> bytes:
    source = SOURCES[language]
    url = (
        f"https://raw.githubusercontent.com/{source['repository']}/"
        f"{source['commit']}/{source['file']}"
    )
    request = Request(url, headers={"User-Agent": "USG-PUD-Structural-Frequency/0.1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"PUD source download failed ({response.status}): {url}")
        return response.read()


def build_report(
    payloads: dict[str, bytes],
    source_manifest: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a report only when source bytes match the generator's pinned manifest."""
    if source_manifest.get("license") != LICENSE:
        raise ValueError("source manifest license does not match the pinned PUD policy")
    if source_manifest.get("semantic_gold", {}).get("available") is not False:
        raise ValueError("PUD structural diagnostics require an explicit no-semantic-gold manifest")
    if source_manifest.get("privacy_review", {}).get("status") != "approved_for_bounded_internal_evaluation":
        raise ValueError("PUD source manifest lacks the bounded privacy-review status")

    languages: dict[str, Any] = {}
    for language in ("en", "ar"):
        if language not in payloads:
            raise ValueError(f"missing pinned PUD source payload for {language}")
        source = SOURCES[language]
        manifest_source = source_manifest.get("sources", {}).get(language, {})
        payload = payloads[language]
        content_sha = hashlib.sha256(payload).hexdigest()
        blob_sha = _git_blob_sha1(payload)
        if manifest_source.get("repository") != source["repository"]:
            raise ValueError(f"{language} repository differs from the pinned source")
        if manifest_source.get("commit") != source["commit"] or manifest_source.get("file") != source["file"]:
            raise ValueError(f"{language} source commit/file differs from the pinned source")
        if manifest_source.get("blob_sha") != source["blob_sha"] or blob_sha != source["blob_sha"]:
            raise ValueError(f"{language} CoNLL-U Git blob SHA does not match the pinned source")
        if manifest_source.get("content_sha256") != content_sha:
            raise ValueError(f"{language} CoNLL-U SHA-256 differs from source-manifest.json")
        sentences = parse_conllu_structure(payload.decode("utf-8"))
        expected_sentences = int(manifest_source.get("sentence_count", 0))
        if len(sentences) != expected_sentences:
            raise ValueError(f"{language} sentence count differs from source-manifest.json")
        languages[language] = {
            "source": {
                "repository": source["repository"],
                "commit": source["commit"],
                "file": source["file"],
                "git_blob_sha1": blob_sha,
                "content_sha256": content_sha,
                "license": LICENSE,
            },
            **summarize_language(sentences),
        }

    return {
        "contract": CONTRACT,
        "generated_at": generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_retrieved_at": source_manifest.get("retrieved_at"),
        "population": "naturalistic",
        "dataset_id": source_manifest.get("dataset_id"),
        "languages": languages,
        "construction_rules": CONSTRUCTION_RULES,
        "label_basis": "Pinned Universal Dependencies CoNLL-U POS and dependency labels; syntactic proxy diagnostics only.",
        "semantic_gold": {
            "available": False,
            "reason": "UD dependency/POS labels do not establish USG semantic roles, frames, relations, or semantic correctness.",
        },
        "interpretation_limits": [
            "Counts are sentence-presence and dependency-instance frequencies, not semantic accuracy.",
            "Subject/object/dependency labels are syntactic annotations and must not be relabeled as semantic agent/patient roles.",
            "The Arabic PUD population is translated and is not a representative native-MSA distribution.",
            "PUD is news/Wikipedia text, not conversational user requests.",
        ],
    }


def generate_report(source_manifest_path: Path, output_path: Path) -> dict[str, Any]:
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    payloads = {language: _download_pinned_source(language) for language in ("en", "ar")}
    report = build_report(payloads, source_manifest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    output_path.write_bytes(output_bytes)
    source_manifest["structural_frequency"] = {
        "contract": CONTRACT,
        "artifact": output_path.name,
        "sha256": hashlib.sha256(output_bytes).hexdigest(),
        "sentence_counts": {language: data["sentence_count"] for language, data in report["languages"].items()},
    }
    source_manifest_path.write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute pinned bilingual PUD structural-frequency diagnostics.")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = generate_report(args.source_manifest, args.output)
    except (OSError, ValueError, RuntimeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "contract": report["contract"],
        "output": str(args.output),
        "languages": {
            language: {
                "sentence_count": data["sentence_count"],
                "token_count": data["token_count"],
                "constructions": {
                    key: value["per_1000_sentences"]
                    for key, value in data["constructions"].items()
                },
            }
            for language, data in report["languages"].items()
        },
        "semantic_gold_available": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
