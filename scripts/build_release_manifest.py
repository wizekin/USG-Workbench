"""Generate a deterministic SHA-256 manifest for the local Phase 3 release."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.1.0"
MANIFEST_PATH = Path("release/phase3-release-manifest.json")
TOP_LEVEL = [
    "README.md", "pyproject.toml", "setup.py", "requirements-phase3.lock", "MANIFEST.in", "scripts/build_release_manifest.py",
]
ROOTS = [
    "tools", "specifications", "rules", "benchmarks", "interoperability",
    "implementations/python-kernel/v0.7.0/usg_discourse_v07", "examples", "release",
]


def release_files():
    paths = {ROOT / item for item in TOP_LEVEL}
    for relative in ROOTS:
        folder = ROOT / relative
        if folder.exists():
            paths.update(
                path for path in folder.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            )
    excluded = {ROOT / MANIFEST_PATH}
    return sorted((path for path in paths if path.is_file() and path not in excluded),
                  key=lambda path: path.relative_to(ROOT).as_posix())


def build_manifest():
    entries = []
    for path in release_files():
        raw = path.read_bytes()
        entries.append({
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return {
        "manifest_profile": "USG-RELEASE-MANIFEST/1.0.0",
        "release_version": RELEASE_VERSION,
        "canonical_profile": "USG-SEM/1.0",
        "canonical_storage_backend": "SQLite",
        "python_requires": ">=3.10",
        "runtime_dependency_lock": "requirements-phase3.lock",
        "hash_algorithm": "SHA-256",
        "file_count": len(entries),
        "files": entries,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / MANIFEST_PATH))
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(f"Wrote {output} ({len(build_manifest()['files'])} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
