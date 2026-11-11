"""Read-only reconciliation against the durable GitHub lexical-data branch."""
from __future__ import annotations

import base64
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .audit import audit_crawl_state


API_ROOT = "https://api.github.com"


def _github_json(url: str, token: str | None, opener=urlopen) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "USG-External-Lexical-State-Audit/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with opener(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub state audit request failed for {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"GitHub returned an unexpected response for {url}")
    return payload


def _decode_contents(payload: dict, label: str) -> dict:
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise RuntimeError(f"{label} was not returned as base64 GitHub contents")
    try:
        value = json.loads(base64.b64decode(payload["content"]).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return value


def audit_github_branch(repository: str, branch: str, token: str | None = None, opener=urlopen) -> dict:
    """Fetch the current data-branch state and reconcile it with physical shard metadata."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be in owner/name form")
    if not branch or branch.startswith("-"):
        raise ValueError("branch must be a non-empty branch name")

    encoded_branch = quote(branch, safe="")
    base = f"{API_ROOT}/repos/{repository}"
    checkpoint_payload = _github_json(
        f"{base}/contents/state/checkpoint.json?ref={encoded_branch}", token, opener
    )
    manifest_payload = _github_json(
        f"{base}/contents/state/manifest.json?ref={encoded_branch}", token, opener
    )
    checkpoint = _decode_contents(checkpoint_payload, "state/checkpoint.json")
    manifest = _decode_contents(manifest_payload, "state/manifest.json")
    snapshot_id = checkpoint.get("source_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise RuntimeError("checkpoint does not declare source_snapshot_id")

    tree_payload = _github_json(
        f"{base}/git/trees/{encoded_branch}?recursive=1", token, opener
    )
    if tree_payload.get("truncated"):
        raise RuntimeError("GitHub tree response was truncated; refusing an incomplete shard audit")
    tree = tree_payload.get("tree")
    if not isinstance(tree, list):
        raise RuntimeError("GitHub tree response did not contain a tree array")
    prefix = f"shards/{snapshot_id}/"
    inventory = [
        {
            "type": item.get("type"),
            "path": item.get("path"),
            "size": item.get("size", 0),
            "sha": item.get("sha"),
        }
        for item in tree
        if isinstance(item, dict)
        and item.get("type") == "blob"
        and isinstance(item.get("path"), str)
        and item["path"].startswith(prefix)
        and item["path"].endswith(".jsonl.gz")
    ]
    report = audit_crawl_state(checkpoint, manifest, inventory)
    report["source"] = {
        "repository": repository,
        "branch": branch,
        "snapshot_id": snapshot_id,
        "checkpoint_blob_sha": checkpoint_payload.get("sha"),
        "manifest_blob_sha": manifest_payload.get("sha"),
        "shard_inventory_count": len(inventory),
        "tree_sha": tree_payload.get("sha"),
    }
    return report
