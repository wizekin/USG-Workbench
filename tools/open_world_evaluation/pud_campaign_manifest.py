"""Add post-pipeline auxiliary files to an append-only campaign bundle manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def include_auxiliary_files(campaign_dir: Path, filenames: list[str]) -> dict:
    root = campaign_dir.resolve()
    manifest_path = root / "bundle-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("campaign bundle manifest must contain a files array")

    entries = {}
    for item in manifest["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("campaign bundle manifest contains an invalid file entry")
        entries[item["name"]] = item

    if len(set(filenames)) != len(filenames):
        raise ValueError("auxiliary file list contains duplicate names")

    for filename in filenames:
        if not filename or Path(filename).name != filename or filename == "bundle-manifest.json":
            raise ValueError(f"unsafe auxiliary filename: {filename!r}")
        path = root / filename
        if not path.is_file():
            raise FileNotFoundError(f"campaign auxiliary file is missing: {filename}")
        payload = path.read_bytes()
        record = {
            "name": filename,
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        previous = entries.get(filename)
        if previous is not None and previous != record:
            raise ValueError(f"existing bundle entry conflicts with auxiliary file: {filename}")
        entries[filename] = record

    manifest["files"] = [entries[name] for name in sorted(entries)]
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = manifest_path.with_name(".bundle-manifest.json.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--file", dest="files", action="append", required=True)
    args = parser.parse_args()
    manifest = include_auxiliary_files(args.campaign_dir, args.files)
    print(f"Campaign manifest now covers {len(manifest['files'])} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
