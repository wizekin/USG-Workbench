"""Content-addressed external lexical shard inventory and deduplicated evaluation input."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def inventory_and_deduplicate(shards_dir: Path, unique_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    shards_dir, unique_dir = Path(shards_dir), Path(unique_dir)
    if not shards_dir.is_dir():
        raise ValueError(f"external lexical shards directory not found: {shards_dir}")
    unique_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(shards_dir.rglob("*.jsonl.gz"))
    files = []
    first_by_digest: dict[str, dict[str, Any]] = {}
    duplicate_groups: dict[str, list[str]] = {}
    unique_files = []
    for path in paths:
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        git_blob = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + bytes([0]) + payload).hexdigest()
        relative = path.relative_to(shards_dir).as_posix()
        item = {
            "path": relative, "size_bytes": len(payload),
            "sha256": digest, "git_blob_sha1": git_blob,
        }
        files.append(item)
        if digest in first_by_digest:
            duplicate_groups.setdefault(digest, [first_by_digest[digest]["path"]]).append(relative)
            continue
        first_by_digest[digest] = item
        unique_files.append(item)
        destination = unique_dir / Path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)

    batch_count = int(manifest.get("batch_count", -1))
    unique_count = len(unique_files)
    physical_count = len(files)
    groups = [
        {"sha256": digest, "canonical_path": paths[0], "duplicate_paths": paths[1:]}
        for digest, paths in sorted(duplicate_groups.items())
    ]
    return {
        "status": "matches_manifest_with_duplicates" if unique_count == batch_count and physical_count > unique_count
                  else ("matches_manifest" if unique_count == batch_count else "count_mismatch"),
        "snapshot_id": manifest.get("source_snapshot_id"),
        # file_count means unique content objects and is directly comparable to manifest batch_count.
        "file_count": unique_count,
        "unique_content_count": unique_count,
        "physical_file_count": physical_count,
        "duplicate_file_count": physical_count - unique_count,
        "duplicate_groups": groups,
        "total_size_bytes": sum(item["size_bytes"] for item in files),
        "unique_content_size_bytes": sum(item["size_bytes"] for item in unique_files),
        "manifest_batch_count": batch_count,
        "matches_manifest": unique_count == batch_count,
        "files": files,
        "unique_files": unique_files,
        "evaluation_input": "unique-content-only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shards-dir", type=Path, required=True)
    parser.add_argument("--unique-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = inventory_and_deduplicate(args.shards_dir, args.unique_dir, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "file_count", "physical_file_count", "duplicate_file_count",
        "manifest_batch_count", "matches_manifest", "status")}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
