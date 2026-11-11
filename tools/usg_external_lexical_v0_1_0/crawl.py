"""Resumable, bounded crawler for scheduled GitHub Actions lexical analysis.

The crawler retrieves one source entry at a time from a pinned English Dictionary
snapshot. It stores compact, source-linked analysis metadata (not raw definitions
or example passages) in immutable gzip JSONL shards on a separate Git branch.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import html
import json
import os
import posixpath
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .analysis import analyze_bundle, classify_definition_pattern
from .providers import (
    GITHUB_REPOSITORY,
    HttpClient,
    ProviderError,
    ProviderNotFound,
    ProviderRateLimited,
    _front_matter,
    _markdown_links,
    parse_english_dictionary_entry,
    utc_now,
)


DEFAULT_DATA_BRANCH = "usg-external-lexical-data"
DEFAULT_SOURCE_REPOSITORY = GITHUB_REPOSITORY
DEFAULT_MAX_RUNTIME_SECONDS = 19_200  # 5h20m; leaves 40 minutes before the 6h runner limit.
DEFAULT_MAX_HEADWORDS = 30_000
DEFAULT_DELAY_SECONDS = 0.35
DEFAULT_MAX_SHARD_BYTES = 16 * 1024 * 1024
DEFAULT_STORAGE_BUDGET_BYTES = 700 * 1024 * 1024
GITHUB_API = "https://api.github.com"
CHECKPOINT_PATH = "state/checkpoint.json"
MANIFEST_PATH = "state/manifest.json"


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _initials_from_root(markdown: str) -> list[str]:
    metadata = _front_matter(markdown)
    if metadata.get("kind") != "dictionary-index":
        raise ProviderError("Source root index has an unexpected kind")
    initials = []
    for _label, target in _markdown_links(markdown):
        match = re.fullmatch(r"browse/([a-z_])/INDEX\.md", target)
        if match:
            initials.append(match.group(1))
    if not initials:
        raise ProviderError("No alphabetical browse indexes were found")
    return initials


def _pages_from_letter_index(markdown: str, expected_snapshot: str) -> list[str]:
    metadata = _front_matter(markdown)
    if metadata.get("kind") != "alphabetical-letter-index":
        raise ProviderError("Source letter index has an unexpected kind")
    if metadata.get("snapshot_id") != expected_snapshot:
        raise ProviderError("Source letter index belongs to a different snapshot")
    pages = []
    for _label, target in _markdown_links(markdown):
        if re.fullmatch(r"\d{4}\.md", target):
            pages.append(target)
    if not pages:
        raise ProviderError("Source letter index contained no numbered browse pages")
    return pages


def parse_headword_page(
    markdown: str, page_path: str, expected_snapshot_id: str | None = None
) -> list[dict[str, str]]:
    """Return validated candidate labels and safe entry paths from one browse page."""
    metadata = _front_matter(markdown)
    if metadata.get("kind") != "alphabetical-headword-page":
        raise ProviderError(f"Unexpected browse page kind: {page_path}")
    if expected_snapshot_id and metadata.get("snapshot_id") != expected_snapshot_id:
        raise ProviderError(f"Browse page snapshot mismatch: {page_path}")
    rows = []
    base_dir = posixpath.dirname(page_path)
    for label, target in _markdown_links(markdown):
        if not target.startswith("../../entries/") or not target.endswith(".md"):
            continue
        entry_path = posixpath.normpath(posixpath.join(base_dir, target))
        if not entry_path.startswith("dictionary/entries/") or ".." in entry_path.split("/"):
            raise ProviderError(f"Unsafe entry path in browse page: {page_path}")
        if not label:
            raise ProviderError(f"Empty headword candidate in browse page: {page_path}")
        rows.append({"headword_candidate": label, "entry_path": entry_path})
    declared = metadata.get("headwords")
    if declared and declared.isdigit() and int(declared) != len(rows):
        raise ProviderError(
            f"Browse page count mismatch in {page_path}: expected {declared}, parsed {len(rows)}"
        )
    return rows


def _compact_entry(
    parsed: dict[str, Any], headword: str, entry_path: str,
    structural_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep useful derived lexical structure while omitting copied source passages."""
    source = dict(parsed.get("source") or {})
    compact_entries = []
    graph_nodes: dict[str, dict[str, Any]] = {}
    graph_edges: list[dict[str, Any]] = []
    pattern_counts: dict[str, int] = {}
    relation_count = 0
    form_count = 0
    sense_count = 0

    def add_node(node_id: str, node_type: str, **fields):
        graph_nodes.setdefault(node_id, {"node_id": node_id, "node_type": node_type, **fields})

    for entry in parsed.get("entries", []) or []:
        entry_id = str(entry.get("entry_id") or "")
        lemma = str(entry.get("lemma") or headword)
        pos = entry.get("part_of_speech")
        lemma_node = "lemma:" + lemma.casefold()
        add_node(lemma_node, "lemma_candidate", label=lemma)
        add_node(entry_id, "lexical_entry", lemma=lemma, part_of_speech=pos)
        graph_edges.append({
            "edge_id": "entry-lemma-" + _sha256((entry_id + "\0" + lemma_node).encode())[:20],
            "source": entry_id, "target": lemma_node, "type": "entry_has_lemma", "scope": "entry",
        })

        compact_forms = []
        for form in entry.get("forms", []) or []:
            if not isinstance(form, dict) or not isinstance(form.get("form"), str):
                continue
            form_value = form["form"]
            tags = form.get("tags", []) if isinstance(form.get("tags"), list) else []
            compact_forms.append({"form": form_value, "tags": tags})
            form_node = "form:" + form_value.casefold()
            add_node(form_node, "surface_form_candidate", label=form_value)
            graph_edges.append({
                "edge_id": "form-" + _sha256((entry_id + "\0" + form_value).encode())[:20],
                "source": entry_id, "target": form_node, "type": "observed_form",
                "scope": "entry", "tags": tags,
            })
            form_count += 1

        compact_senses = []
        for sense in entry.get("senses", []) or []:
            if not isinstance(sense, dict):
                continue
            definition = sense.get("definition")
            if not isinstance(definition, str) or not definition.strip():
                continue
            sense_id = str(sense.get("sense_id") or "")
            if not sense_id:
                continue
            pos_value = sense.get("part_of_speech") or pos
            pattern = classify_definition_pattern(definition)
            pattern_type = str(pattern.get("pattern_type") or "unclassified_definition")
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
            tags = sense.get("tags", []) if isinstance(sense.get("tags"), list) else []
            relations = sense.get("relations", []) if isinstance(sense.get("relations"), list) else []
            compact_senses.append({
                "sense_id": sense_id,
                "source_sense_id": sense.get("source_sense_id"),
                "part_of_speech": pos_value,
                "definition_sha256": _sha256(definition.encode("utf-8")),
                "definition_pattern": {
                    "pattern_type": pattern_type,
                    "extraction_method": pattern.get("extraction_method"),
                    "heuristic_strength": pattern.get("heuristic_strength"),
                    "validation_status": "unvalidated_observation",
                },
                "tags": tags,
                "example_count": len(sense.get("examples", []) or []),
                "relations": relations,
            })
            add_node(sense_id, "lexical_sense_candidate", entry_id=entry_id, part_of_speech=pos_value,
                     definition_pattern=pattern_type)
            graph_edges.append({
                "edge_id": "entry-sense-" + _sha256((entry_id + "\0" + sense_id).encode())[:20],
                "source": entry_id, "target": sense_id, "type": "entry_has_sense", "scope": "entry",
            })
            for relation in relations:
                if not isinstance(relation, dict):
                    continue
                target_lemma = relation.get("target_lemma")
                if not isinstance(target_lemma, str) or not target_lemma.strip():
                    continue
                target_node = "lemma:" + target_lemma.casefold()
                add_node(target_node, "lemma_candidate", label=target_lemma)
                graph_edges.append({
                    "edge_id": relation.get("relation_id") or "relation-" + _sha256(
                        (sense_id + "\0" + target_lemma + "\0" + str(relation.get("type"))).encode()
                    )[:20],
                    "source": sense_id, "target": target_node,
                    "type": relation.get("type"), "scope": relation.get("scope", "sense"),
                    "status": relation.get("status", "source_asserted_unvalidated"),
                })
                relation_count += 1
            sense_count += 1

        entry_relations = []
        for relation in entry.get("relations", []) or []:
            if not isinstance(relation, dict):
                continue
            target_lemma = relation.get("target_lemma")
            if not isinstance(target_lemma, str) or not target_lemma.strip():
                continue
            target_node = "lemma:" + target_lemma.casefold()
            add_node(target_node, "lemma_candidate", label=target_lemma)
            entry_relations.append(relation)
            graph_edges.append({
                "edge_id": relation.get("relation_id") or "relation-" + _sha256(
                    (entry_id + "\0" + target_lemma + "\0" + str(relation.get("type"))).encode()
                )[:20],
                "source": entry_id, "target": target_node,
                "type": relation.get("type"), "scope": relation.get("scope", "entry"),
                "status": relation.get("status", "source_asserted_unvalidated"),
            })
            relation_count += 1

        compact_entries.append({
            "entry_id": entry_id,
            "lemma": lemma,
            "part_of_speech": pos,
            "forms": compact_forms,
            "senses": compact_senses,
            "relations": entry_relations,
        })

    provenance = {
        "provider": source.get("provider"),
        "provider_url": source.get("provider_url"),
        "record_url": source.get("record_url"),
        "history_url": source.get("history_url"),
        "entry_file_url": source.get("entry_file_url"),
        "snapshot_id": source.get("snapshot_id"),
        "source_entry_id": source.get("source_entry_id"),
        "license": source.get("license", "not_declared"),
        "attribution": source.get("attribution"),
        "editorial_review_status": source.get("editorial_review_status"),
        "relation_link_scope": source.get("relation_link_scope"),
        "rights_note": source.get("rights_note"),
    }
    return {
        "headword_candidate": headword,
        "entry_path": entry_path,
        "source_provenance": provenance,
        "entries": compact_entries,
        "candidate_graph": {
            "graph_version": "usg-lexical-candidate-graph/0.1.0",
            "nodes": list(graph_nodes.values()),
            "edges": graph_edges,
        },
        "analysis_summary": {
            "entry_count": len(compact_entries),
            "sense_count": sense_count,
            "form_count": form_count,
            "relation_count": relation_count,
            "definition_pattern_counts": pattern_counts,
            "validation_status": (structural_analysis or {}).get("validation", {}).get("status", "not_run"),
            "validation_error_count": (structural_analysis or {}).get("validation", {}).get("error_count", 0),
            "validation_warning_count": (structural_analysis or {}).get("validation", {}).get("warning_count", 0),
            "analysis_version": (structural_analysis or {}).get("analysis_version"),
            "validation_note": "Structural analysis only; definition strings and example passages are intentionally not copied into the public data branch.",
        },
        "rights_policy": {
            "raw_definitions_persisted": False,
            "examples_persisted": False,
            "source_and_history_links_retained": True,
            "declared_license_retained": True,
        },
    }


def _github_api_request(method: str, url: str, token: str, payload: dict | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "USG-External-Lexical-Crawler/0.1",
    })
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read(5 * 1024 * 1024 + 1)
            if len(raw) > 5 * 1024 * 1024:
                raise RuntimeError("GitHub API response exceeded 5 MiB")
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        details = exc.read(2000).decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub data publisher failed (HTTP {exc.code}): {details}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub data publisher request failed: {type(exc).__name__}") from exc


class GitHubDataPublisher:
    """Publish one append-only shard plus the latest checkpoint and manifest."""

    def __init__(self, repository: str, token: str, branch: str = DEFAULT_DATA_BRANCH):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("repository must be in owner/name form")
        if not token:
            raise ValueError("GITHUB_TOKEN is required to publish lexical data")
        self.repository = repository
        self.token = token
        self.branch = branch
        self.api = f"{GITHUB_API}/repos/{repository}"

    def _create_blob(self, payload: bytes) -> str:
        encoded = base64.b64encode(payload).decode("ascii")
        result = _github_api_request("POST", self.api + "/git/blobs", self.token, {
            "content": encoded,
            "encoding": "base64",
        })
        sha = result.get("sha")
        if not isinstance(sha, str):
            raise RuntimeError("GitHub did not return a blob SHA")
        return sha

    def publish(
        self,
        shard_path: str | None,
        shard_bytes: bytes | None,
        checkpoint: dict[str, Any],
        manifest: dict[str, Any],
        message: str,
    ) -> str:
        ref_url = self.api + "/git/ref/heads/" + quote(self.branch, safe="")
        update_ref_url = self.api + "/git/refs/heads/" + quote(self.branch, safe="")
        ref = _github_api_request("GET", ref_url, self.token)
        head_sha = ref.get("object", {}).get("sha")
        if not isinstance(head_sha, str):
            raise RuntimeError("Data branch does not exist or has no commit")
        head_commit = _github_api_request("GET", self.api + "/git/commits/" + head_sha, self.token)
        base_tree = head_commit.get("tree", {}).get("sha")
        if not isinstance(base_tree, str):
            raise RuntimeError("Could not resolve the data branch tree")

        elements = []
        if shard_path and shard_bytes is not None:
            elements.append({
                "path": shard_path,
                "mode": "100644",
                "type": "blob",
                "sha": self._create_blob(shard_bytes),
            })
        for path, data in (
            (CHECKPOINT_PATH, _json_bytes(checkpoint)),
            (MANIFEST_PATH, _json_bytes(manifest)),
        ):
            elements.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": self._create_blob(data),
            })
        tree = _github_api_request("POST", self.api + "/git/trees", self.token, {
            "base_tree": base_tree,
            "tree": elements,
        })
        tree_sha = tree.get("sha")
        if not isinstance(tree_sha, str):
            raise RuntimeError("GitHub did not return a tree SHA")
        commit = _github_api_request("POST", self.api + "/git/commits", self.token, {
            "message": message,
            "tree": tree_sha,
            "parents": [head_sha],
        })
        commit_sha = commit.get("sha")
        if not isinstance(commit_sha, str):
            raise RuntimeError("GitHub did not return a commit SHA")
        _github_api_request("PATCH", update_ref_url, self.token, {"sha": commit_sha, "force": False})
        return commit_sha


class LexicalCrawler:
    def __init__(
        self,
        *,
        repository: str = DEFAULT_SOURCE_REPOSITORY,
        client: HttpClient | None = None,
        publisher: GitHubDataPublisher | None = None,
        data_branch: str = DEFAULT_DATA_BRANCH,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        storage_budget_bytes: int = DEFAULT_STORAGE_BUDGET_BYTES,
    ):
        self.repository = repository
        self.client = client or HttpClient(timeout=25, max_bytes=20_000_000, retries=3)
        self.publisher = publisher
        self.data_branch = data_branch
        self.delay_seconds = max(0.0, min(float(delay_seconds), 2.0))
        self.storage_budget_bytes = max(1, int(storage_budget_bytes))

    def _raw_base(self, commit: str) -> str:
        return f"https://raw.githubusercontent.com/{self.repository}/{commit}/"

    def _resolve_latest_source(self) -> str:
        payload, _ = self.client.get_json(
            f"https://api.github.com/repos/{self.repository}/commits/main"
        )
        sha = payload.get("sha") if isinstance(payload, dict) else None
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ProviderError("Source repository did not return a valid commit SHA")
        return sha

    def _build_catalogue(self, commit: str) -> tuple[str, list[str], int]:
        base = self._raw_base(commit)
        root, _ = self.client.get_text(base + "dictionary/INDEX.md")
        root_meta = _front_matter(root)
        expected_count = int(root_meta.get("headwords", "0") or 0)
        if expected_count <= 0:
            raise ProviderError("Source root index is missing its headword count")
        # The actual upstream browse root has no snapshot_id; dictionary/SOURCE.md
        # is the authoritative snapshot metadata document.
        source, _ = self.client.get_text(base + "dictionary/SOURCE.md")
        source_meta = _front_matter(source)
        snapshot = source_meta.get("snapshot_id")
        if not snapshot:
            raise ProviderError("Source metadata page is missing its snapshot ID")
        root_snapshot = root_meta.get("snapshot_id")
        if root_snapshot and root_snapshot != snapshot:
            raise ProviderError("Root index and source metadata describe different snapshots")
        page_paths = []
        for initial in _initials_from_root(root):
            letter_index, _ = self.client.get_text(
                base + f"dictionary/browse/{initial}/INDEX.md"
            )
            for page_name in _pages_from_letter_index(letter_index, snapshot):
                page_paths.append(f"dictionary/browse/{initial}/{page_name}")
        if not page_paths:
            raise ProviderError("No alphabetical browse pages were found")
        return snapshot, page_paths, expected_count

    def load_checkpoint(self) -> dict[str, Any] | None:
        # Read the mutable branch ref through the GitHub Contents API. The raw
        # content URL is CDN-cached and can briefly return an older checkpoint,
        # which would make a scheduled run replay a previously published batch.
        url = (
            f"https://api.github.com/repos/wizekin/USG-Workbench/contents/"
            f"{CHECKPOINT_PATH}?ref={quote(self.data_branch, safe='')}"
        )
        try:
            payload, _ = self.client.get_json(url)
            if not isinstance(payload, dict):
                raise ProviderError("GitHub returned an invalid checkpoint response")
            encoded = payload.get("content")
            encoding = payload.get("encoding")
            if not isinstance(encoded, str) or encoding != "base64":
                raise ProviderError("GitHub checkpoint response did not contain base64 content")
            decoded = base64.b64decode(encoded).decode("utf-8")
            value = json.loads(decoded)
            return value if isinstance(value, dict) else None
        except ProviderNotFound:
            return None
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, ProviderError):
            raise ProviderError("The data-branch checkpoint is invalid or unavailable")

    def _discover_failed_headwords(self, snapshot_id: str) -> tuple[list[dict[str, Any]], int]:
        """Rebuild the retry queue from immutable prior shards after upgrading an old checkpoint."""
        safe_snapshot = re.sub(r"[^A-Za-z0-9_.-]+", "-", snapshot_id)
        listing_url = (
            f"https://api.github.com/repos/wizekin/USG-Workbench/contents/"
            f"shards/{safe_snapshot}?ref={quote(self.data_branch, safe='')}"
        )
        try:
            items, _ = self.client.get_json(listing_url)
        except ProviderNotFound:
            return [], 0
        if not isinstance(items, list):
            raise ProviderError("GitHub returned an invalid lexical shard listing")

        failures: dict[str, dict[str, Any]] = {}
        observed_shard_bytes = 0
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "file":
                continue
            if not str(item.get("name", "")).endswith(".jsonl.gz"):
                continue
            observed_shard_bytes += max(0, int(item.get("size", 0) or 0))
            download_url = item.get("download_url")
            if not isinstance(download_url, str) or not download_url.startswith("https://raw.githubusercontent.com/"):
                raise ProviderError("A prior lexical shard has no safe immutable download URL")
            raw, _ = self.client.get_bytes(download_url)
            try:
                lines = gzip.decompress(raw).decode("utf-8").splitlines()
            except (OSError, UnicodeDecodeError) as exc:
                raise ProviderError("A prior lexical shard could not be decoded") from exc
            for line in lines:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProviderError("A prior lexical shard contains invalid JSONL") from exc
                if not isinstance(record, dict) or record.get("event_type") != "headword_error":
                    continue
                candidate = record.get("headword_candidate")
                entry_path = record.get("entry_path")
                if not isinstance(candidate, str) or not candidate.strip():
                    continue
                if not isinstance(entry_path, str) or not entry_path.startswith("dictionary/entries/"):
                    continue
                failures.setdefault(entry_path, {
                    "headword_candidate": candidate,
                    "entry_path": entry_path,
                    "attempts": 0,
                })
        return list(failures.values()), observed_shard_bytes

    @staticmethod
    def _new_checkpoint(
        commit: str, snapshot: str, pages: list[str], expected_count: int,
        previous: dict[str, Any] | None,
    ) -> dict[str, Any]:
        cycle_number = int((previous or {}).get("cycle_number", 0)) + 1
        return {
            "schema_version": "usg-lexical-crawl-checkpoint/0.1.0",
            "status": "in_progress",
            "source_repository": DEFAULT_SOURCE_REPOSITORY,
            "source_commit": commit,
            "source_snapshot_id": snapshot,
            "expected_headwords": expected_count,
            "pages": pages,
            "page_index": 0,
            "entry_index": 0,
            "cycle_number": cycle_number,
            "batch_number": 0,
            "processed_headwords": 0,
            "processed_entries": 0,
            "processed_senses": 0,
            "failed_headwords": 0,
            "failed_pages": 0,
            "retry_queue_initialized": bool((previous or {}).get("retry_queue_initialized", False)),
            "retry_queue": list((previous or {}).get("retry_queue", [])),
            "retried_headwords": int((previous or {}).get("retried_headwords", 0)),
            "recovered_headwords": int((previous or {}).get("recovered_headwords", 0)),
            "retry_failed_headwords": int((previous or {}).get("retry_failed_headwords", 0)),
            "retry_dead_letter_headwords": int((previous or {}).get("retry_dead_letter_headwords", 0)),
            "stored_bytes": int((previous or {}).get("stored_bytes", 0)),
            "updated_at": utc_now(),
        }

    def _load_page_rows(
        self, commit: str, page_path: str, snapshot_id: str
    ) -> list[dict[str, str]]:
        markdown, _ = self.client.get_text(self._raw_base(commit) + page_path)
        return parse_headword_page(markdown, page_path, expected_snapshot_id=snapshot_id)

    def _process_candidate(self, commit: str, row: dict[str, str]) -> dict[str, Any]:
        entry_path = row["entry_path"]
        entry_url = self._raw_base(commit) + entry_path
        markdown, _ = self.client.get_text(entry_url)
        parsed = parse_english_dictionary_entry(
            markdown, row["headword_candidate"], entry_url
        )
        parsed["source"]["provider"] = "english_dictionary_github"
        for entry in parsed.get("entries", []):
            entry["provider"] = "english_dictionary_github"
        structural_analysis = analyze_bundle({
            "schema_version": "usg-external-lexical/0.1.0",
            "queried_form": row["headword_candidate"],
            "sources": [parsed["source"]],
            "entries": parsed.get("entries", []),
        })
        return _compact_entry(
            parsed, row["headword_candidate"], entry_path, structural_analysis
        )

    def _initial_manifest(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "usg-lexical-crawl-manifest/0.1.0",
            "source_repository": f"https://github.com/{self.repository}",
            "status": checkpoint.get("status"),
            "source_snapshot_id": checkpoint.get("source_snapshot_id"),
            "source_commit": checkpoint.get("source_commit"),
            "expected_headwords": checkpoint.get("expected_headwords"),
            "processed_headwords": checkpoint.get("processed_headwords", 0),
            "processed_entries": checkpoint.get("processed_entries", 0),
            "processed_senses": checkpoint.get("processed_senses", 0),
            "failed_headwords": checkpoint.get("failed_headwords", 0),
            "failed_pages": checkpoint.get("failed_pages", 0),
            "retried_headwords": checkpoint.get("retried_headwords", 0),
            "recovered_headwords": checkpoint.get("recovered_headwords", 0),
            "retry_failed_headwords": checkpoint.get("retry_failed_headwords", 0),
            "retry_dead_letter_headwords": checkpoint.get("retry_dead_letter_headwords", 0),
            "pending_retries": len(checkpoint.get("retry_queue", [])),
            "batch_count": checkpoint.get("batch_number", 0),
            "stored_bytes": checkpoint.get("stored_bytes", 0),
            "storage_budget_bytes": self.storage_budget_bytes,
            "cycle_number": checkpoint.get("cycle_number", 1),
            "last_batch": None,
            "updated_at": utc_now(),
            "rights_policy": "No source definition or example passage is stored. Per-entry declared licence, entry URL, history URL and snapshot are retained with structured lexical evidence.",
        }

    def run_batch(
        self,
        *,
        max_runtime_seconds: int = DEFAULT_MAX_RUNTIME_SECONDS,
        max_headwords: int = DEFAULT_MAX_HEADWORDS,
        max_shard_bytes: int = DEFAULT_MAX_SHARD_BYTES,
        run_id: str = "manual",
    ) -> dict[str, Any]:
        started = time.monotonic()
        deadline = started + max(1, int(max_runtime_seconds))
        previous = self.load_checkpoint()
        if previous and previous.get("status") == "storage_limit_reached":
            return {
                "status": "storage_limit_reached",
                "message": "The persistent data branch reached its configured storage budget; manual review or a new storage repository is required.",
                "checkpoint": previous,
                "published": False,
            }

        if previous and (
            previous.get("status") == "in_progress"
            or bool(previous.get("retry_queue"))
            or (
                previous.get("status") == "complete"
                and int(previous.get("failed_headwords", 0)) > 0
                and not previous.get("retry_queue_initialized", False)
            )
        ):
            checkpoint = previous
            if checkpoint.get("status") == "complete":
                checkpoint["status"] = "in_progress"
        else:
            latest_commit = self._resolve_latest_source()
            snapshot, pages, expected_count = self._build_catalogue(latest_commit)
            if previous and previous.get("status") == "complete" and previous.get("source_snapshot_id") == snapshot:
                return {
                    "status": "up_to_date",
                    "source_snapshot_id": snapshot,
                    "processed_headwords": previous.get("processed_headwords", 0),
                    "published": False,
                    "message": "The latest source snapshot has already been processed.",
                }
            checkpoint = self._new_checkpoint(
                latest_commit, snapshot, pages, expected_count, previous
            )

        # Additive checkpoint fields are migrated in place when resuming an older run.
        checkpoint.setdefault("failed_pages", 0)
        checkpoint.setdefault("retried_headwords", 0)
        checkpoint.setdefault("recovered_headwords", 0)
        checkpoint.setdefault("retry_failed_headwords", 0)
        checkpoint.setdefault("retry_dead_letter_headwords", 0)
        checkpoint.setdefault("retry_queue", [])
        if not checkpoint.get("retry_queue_initialized"):
            if int(checkpoint.get("failed_headwords", 0)) > 0:
                (
                    checkpoint["retry_queue"],
                    observed_shard_bytes,
                ) = self._discover_failed_headwords(
                    str(checkpoint["source_snapshot_id"])
                )
                # Reconcile historical duplicate shards that were published by a
                # stale checkpoint read; never undercount physical storage usage.
                checkpoint["stored_bytes"] = max(
                    int(checkpoint.get("stored_bytes", 0)),
                    observed_shard_bytes,
                )
                if not checkpoint["retry_queue"]:
                    raise ProviderError(
                        "Historical headword failures exist, but no retryable events "
                        "could be recovered from the stored shards"
                    )
            checkpoint["retry_queue_initialized"] = True
        manifest = self._initial_manifest(checkpoint)
        if checkpoint.get("stored_bytes", 0) >= self.storage_budget_bytes:
            checkpoint["status"] = "storage_limit_reached"
            manifest["status"] = checkpoint["status"]
            commit_sha = self.publisher.publish(None, None, checkpoint, manifest, "Pause lexical crawl at storage guard") if self.publisher else None
            return {"status": checkpoint["status"], "published": bool(commit_sha), "commit_sha": commit_sha}

        source_commit = checkpoint["source_commit"]
        pages = checkpoint.get("pages", [])
        page_index = int(checkpoint.get("page_index", 0))
        entry_index = int(checkpoint.get("entry_index", 0))
        records: list[str] = []
        batch_headwords = batch_entries = batch_senses = batch_failed = batch_failed_pages = 0
        batch_retry_attempts = batch_retry_recovered = batch_retry_failed = 0
        stop_reason = "batch_limit"
        limit = max(1, min(int(max_headwords), 100_000))

        # Retry historical failures before advancing the normal source cursor.
        # Process only the queue length present at batch start; failures are
        # deferred to a later run so a persistent source error cannot loop here.
        retry_queue = list(checkpoint.get("retry_queue", []))
        retry_batch = retry_queue[:limit]
        retry_deferred: list[dict[str, Any]] = []
        for retry_item in retry_batch:
            if time.monotonic() >= deadline:
                retry_deferred.append(retry_item)
                continue
            batch_retry_attempts += 1
            try:
                compact = self._process_candidate(source_commit, retry_item)
                compact["retrieval_event"] = {
                    "type": "headword_retry_recovered",
                    "attempt": int(retry_item.get("attempts", 0)) + 1,
                }
                records.append(json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
                record_entries = compact["analysis_summary"]["entry_count"]
                record_senses = compact["analysis_summary"]["sense_count"]
                batch_entries += record_entries
                batch_senses += record_senses
                checkpoint["processed_entries"] = int(checkpoint.get("processed_entries", 0)) + record_entries
                checkpoint["processed_senses"] = int(checkpoint.get("processed_senses", 0)) + record_senses
                checkpoint["recovered_headwords"] = int(checkpoint.get("recovered_headwords", 0)) + 1
                batch_retry_recovered += 1
            except ProviderRateLimited:
                stop_reason = "source_rate_limited"
                retry_deferred.append(retry_item)
                retry_deferred.extend(retry_batch[batch_retry_attempts:])
                break
            except (ProviderNotFound, ProviderError, ValueError) as exc:
                attempt = int(retry_item.get("attempts", 0)) + 1
                records.append(json.dumps({
                    "event_type": "headword_retry_error",
                    "headword_candidate": retry_item.get("headword_candidate"),
                    "entry_path": retry_item.get("entry_path"),
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "recorded_at": utc_now(),
                }, ensure_ascii=False, separators=(",", ":")))
                checkpoint["retry_failed_headwords"] = int(checkpoint.get("retry_failed_headwords", 0)) + 1
                batch_retry_failed += 1
                if attempt < 3:
                    retry_deferred.append({
                        **retry_item,
                        "attempts": attempt,
                        "last_error_type": type(exc).__name__,
                    })
                else:
                    checkpoint["retry_dead_letter_headwords"] = int(checkpoint.get("retry_dead_letter_headwords", 0)) + 1

        checkpoint["retry_queue"] = retry_queue[len(retry_batch):] + retry_deferred
        checkpoint["retried_headwords"] = int(checkpoint.get("retried_headwords", 0)) + batch_retry_attempts
        batch_headwords = batch_retry_attempts

        while page_index < len(pages) and stop_reason != "source_rate_limited":
            if time.monotonic() >= deadline:
                stop_reason = "time_budget"
                break
            page_path = pages[page_index]
            try:
                page_rows = self._load_page_rows(
                    source_commit, page_path, str(checkpoint["source_snapshot_id"])
                )
            except ProviderRateLimited:
                stop_reason = "source_rate_limited"
                break
            except ProviderError as exc:
                # A browse page can contain hundreds of headwords. Never advance
                # past it after a fetch/parse error: the next scheduled run retries
                # this exact page and cursor instead of silently losing its entries.
                records.append(json.dumps({
                    "event_type": "browse_page_error",
                    "page_path": page_path,
                    "error_type": type(exc).__name__,
                    "recorded_at": utc_now(),
                }, ensure_ascii=False, separators=(",", ":")))
                batch_failed_pages += 1
                checkpoint["failed_pages"] = int(checkpoint.get("failed_pages", 0)) + 1
                stop_reason = "browse_page_error"
                break

            while entry_index < len(page_rows):
                if time.monotonic() >= deadline:
                    stop_reason = "time_budget"
                    break
                if batch_headwords >= limit:
                    stop_reason = "headword_limit"
                    break
                row = page_rows[entry_index]
                try:
                    compact = self._process_candidate(source_commit, row)
                    record_entries = compact["analysis_summary"]["entry_count"]
                    record_senses = compact["analysis_summary"]["sense_count"]
                    records.append(json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
                    batch_entries += record_entries
                    batch_senses += record_senses
                    checkpoint["processed_entries"] = int(checkpoint.get("processed_entries", 0)) + record_entries
                    checkpoint["processed_senses"] = int(checkpoint.get("processed_senses", 0)) + record_senses
                except ProviderRateLimited:
                    stop_reason = "source_rate_limited"
                    break
                except (ProviderNotFound, ProviderError, ValueError) as exc:
                    records.append(json.dumps({
                        "event_type": "headword_error",
                        "headword_candidate": row["headword_candidate"],
                        "entry_path": row["entry_path"],
                        "error_type": type(exc).__name__,
                        "recorded_at": utc_now(),
                    }, ensure_ascii=False, separators=(",", ":")))
                    batch_failed += 1
                    checkpoint["failed_headwords"] = int(checkpoint.get("failed_headwords", 0)) + 1
                    checkpoint.setdefault("retry_queue", []).append({
                        "headword_candidate": row["headword_candidate"],
                        "entry_path": row["entry_path"],
                        "attempts": 0,
                    })

                batch_headwords += 1
                checkpoint["processed_headwords"] = int(checkpoint.get("processed_headwords", 0)) + 1
                entry_index += 1
                if self.delay_seconds:
                    time.sleep(self.delay_seconds)
            if stop_reason in {"time_budget", "headword_limit", "source_rate_limited"}:
                break
            page_index += 1
            entry_index = 0

        if page_index >= len(pages) and not checkpoint.get("retry_queue"):
            checkpoint["status"] = "complete"
            stop_reason = "source_snapshot_complete"
        else:
            checkpoint["status"] = "in_progress"
            if page_index >= len(pages):
                stop_reason = "retry_queue_pending"
        checkpoint["page_index"] = page_index
        checkpoint["entry_index"] = entry_index
        checkpoint["updated_at"] = utc_now()

        raw = ("\n".join(records) + ("\n" if records else "")).encode("utf-8")
        shard_bytes = gzip.compress(raw, compresslevel=6, mtime=0) if raw else b""
        if shard_bytes and len(shard_bytes) > max_shard_bytes:
            return {
                "status": "shard_size_limit",
                "message": f"Compressed batch is {len(shard_bytes)} bytes, above the {max_shard_bytes} byte limit; no cursor advancement was published.",
                "published": False,
                "cursor": {"page_index": page_index, "entry_index": entry_index},
            }

        proposed_stored = int(checkpoint.get("stored_bytes", 0)) + len(shard_bytes)
        if proposed_stored > self.storage_budget_bytes:
            # Preserve the exact previous cursor. A future run must not advance past
            # data that could not be committed to the durable store.
            if previous:
                checkpoint = dict(previous)
            else:
                checkpoint["page_index"] = 0
                checkpoint["entry_index"] = 0
                checkpoint["processed_headwords"] = 0
                checkpoint["processed_entries"] = 0
                checkpoint["processed_senses"] = 0
                checkpoint["failed_headwords"] = 0
                checkpoint["failed_pages"] = 0
                checkpoint["stored_bytes"] = 0
            checkpoint["status"] = "storage_limit_reached"
            checkpoint["updated_at"] = utc_now()
            manifest = self._initial_manifest(checkpoint)
            manifest["status"] = "storage_limit_reached"
            commit_sha = self.publisher.publish(None, None, checkpoint, manifest, "Record lexical storage guard") if self.publisher else None
            return {"status": "storage_limit_reached", "published": bool(commit_sha), "commit_sha": commit_sha}

        checkpoint["stored_bytes"] = proposed_stored
        checkpoint["batch_number"] = int(checkpoint.get("batch_number", 0)) + int(bool(shard_bytes))
        manifest.update({
            "status": checkpoint["status"],
            "processed_headwords": checkpoint["processed_headwords"],
            "processed_entries": checkpoint["processed_entries"],
            "processed_senses": checkpoint["processed_senses"],
            "failed_headwords": checkpoint["failed_headwords"],
            "failed_pages": checkpoint.get("failed_pages", 0),
            "retried_headwords": checkpoint.get("retried_headwords", 0),
            "recovered_headwords": checkpoint.get("recovered_headwords", 0),
            "retry_failed_headwords": checkpoint.get("retry_failed_headwords", 0),
            "retry_dead_letter_headwords": checkpoint.get("retry_dead_letter_headwords", 0),
            "pending_retries": len(checkpoint.get("retry_queue", [])),
            "batch_count": checkpoint["batch_number"],
            "stored_bytes": checkpoint["stored_bytes"],
            "updated_at": utc_now(),
        })

        shard_path = None
        if shard_bytes:
            safe_snapshot = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(checkpoint["source_snapshot_id"]))
            shard_path = f"shards/{safe_snapshot}/batch-{checkpoint['batch_number']:06d}-{run_id}.jsonl.gz"
            manifest["last_batch"] = {
                "path": shard_path,
                "sha256": _sha256(shard_bytes),
                "bytes": len(shard_bytes),
                "headwords": batch_headwords,
                "entries": batch_entries,
                "senses": batch_senses,
                "failed_headwords": batch_failed,
                "failed_pages": batch_failed_pages,
                "retry_attempts": batch_retry_attempts,
                "retry_recovered": batch_retry_recovered,
                "retry_failed": batch_retry_failed,
                "pending_retries": len(checkpoint.get("retry_queue", [])),
                "stop_reason": stop_reason,
            }

        commit_sha = None
        if self.publisher:
            commit_sha = self.publisher.publish(
                shard_path, shard_bytes if shard_path else None,
                checkpoint, manifest,
                f"USG lexical crawl batch {checkpoint['batch_number']:06d}: {batch_headwords} headwords",
            )
        elapsed = time.monotonic() - started
        return {
            "status": checkpoint["status"],
            "stop_reason": stop_reason,
            "published": bool(commit_sha),
            "data_branch": self.data_branch,
            "commit_sha": commit_sha,
            "source_snapshot_id": checkpoint["source_snapshot_id"],
            "source_commit": source_commit,
            "batch": {
                "headwords": batch_headwords,
                "entries": batch_entries,
                "senses": batch_senses,
                "failed_headwords": batch_failed,
                "failed_pages": batch_failed_pages,
                "retry_attempts": batch_retry_attempts,
                "retry_recovered": batch_retry_recovered,
                "retry_failed": batch_retry_failed,
                "pending_retries": len(checkpoint.get("retry_queue", [])),
                "compressed_bytes": len(shard_bytes),
                "shard_path": shard_path,
            },
            "cumulative": {
                "headwords": checkpoint["processed_headwords"],
                "entries": checkpoint["processed_entries"],
                "senses": checkpoint["processed_senses"],
                "failed_headwords": checkpoint["failed_headwords"],
                "failed_pages": checkpoint.get("failed_pages", 0),
                "stored_bytes": checkpoint["stored_bytes"],
                "expected_headwords": checkpoint.get("expected_headwords"),
            },
            "cursor": {"page_index": page_index, "entry_index": entry_index, "total_pages": len(pages)},
            "elapsed_seconds": round(elapsed, 2),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run one resumable external lexical-analysis batch.")
    parser.add_argument("--repository", default=DEFAULT_SOURCE_REPOSITORY)
    parser.add_argument("--data-repository", default=os.environ.get("GITHUB_REPOSITORY", "wizekin/USG-Workbench"))
    parser.add_argument("--data-branch", default=os.environ.get("USG_LEXICAL_DATA_BRANCH", DEFAULT_DATA_BRANCH))
    parser.add_argument("--max-runtime-seconds", type=int, default=DEFAULT_MAX_RUNTIME_SECONDS)
    parser.add_argument("--max-headwords", type=int, default=DEFAULT_MAX_HEADWORDS)
    parser.add_argument("--max-shard-bytes", type=int, default=DEFAULT_MAX_SHARD_BYTES)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--storage-budget-mib", type=int, default=700)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "manual"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    publisher = None
    if not args.dry_run:
        publisher = GitHubDataPublisher(args.data_repository, token or "", args.data_branch)
    crawler = LexicalCrawler(
        repository=args.repository,
        publisher=publisher,
        data_branch=args.data_branch,
        delay_seconds=args.delay_seconds,
        storage_budget_bytes=max(1, args.storage_budget_mib) * 1024 * 1024,
    )
    try:
        result = crawler.run_batch(
            max_runtime_seconds=args.max_runtime_seconds,
            max_headwords=args.max_headwords,
            max_shard_bytes=args.max_shard_bytes,
            run_id=args.run_id,
        )
    except Exception as exc:
        print(f"Crawler failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("# USG external lexical crawl\n\n")
            stream.write(f"- Status: {result.get('status')}\n")
            stream.write(f"- Stop reason: {result.get('stop_reason', result.get('message', 'n/a'))}\n")
            batch = result.get("batch", {})
            cumulative = result.get("cumulative", {})
            stream.write(f"- Headwords processed this run: {batch.get('headwords', 0):,}\n")
            stream.write(f"- Senses processed this run: {batch.get('senses', 0):,}\n")
            stream.write(f"- Cumulative headwords: {cumulative.get('headwords', 0):,}\n")
            stream.write(f"- Cumulative senses: {cumulative.get('senses', 0):,}\n")
            stream.write(f"- Stored compressed data: {cumulative.get('stored_bytes', 0):,} bytes\n")
            if result.get("commit_sha"):
                stream.write(f"- Data commit: {result['commit_sha']} on {args.data_branch}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
