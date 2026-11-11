"""Download the compact headword indexes from figueirego/english-dictionary.

This imports headwords and pointers only. It deliberately does not download the
source repository's multi-gigabyte entry corpus or promote headwords into the
runtime LexicalResource, because a headword alone has no verified lemma, POS,
or sense identity.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import html
import json
import os
from pathlib import Path
import posixpath
import re
import sys
import time
from typing import Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

DEFAULT_REPOSITORY = "figueirego/english-dictionary"
DEFAULT_REF = "main"
DEFAULT_OUTPUT = Path("data/lexical-corpus/english-headwords.jsonl.gz")
USER_AGENT = "USG-Workbench-Lexical-Corpus-Importer/0.1 (+https://github.com/wizekin/USG-Workbench)"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class SourceFormatError(ValueError):
    """Raised when an upstream index does not match its documented format."""


def _request_text(url: str, *, timeout: int = 45, retries: int = 4) -> str:
    """Fetch UTF-8 text with a descriptive User-Agent and bounded retries."""
    for attempt in range(retries + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain, */*"})
        try:
            with urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS or attempt >= retries:
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 20)
        except (URLError, TimeoutError):
            if attempt >= retries:
                raise
            delay = min(2 ** attempt, 20)
        time.sleep(delay)
    raise RuntimeError("unreachable retry state")


def resolve_commit(repository: str = DEFAULT_REPOSITORY, ref: str = DEFAULT_REF) -> str:
    """Resolve a branch or tag to a commit SHA so one import uses a fixed snapshot."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be in owner/name form")
    url = f"https://api.github.com/repos/{repository}/commits/{quote(ref, safe='')}"
    payload = json.loads(_request_text(url))
    sha = payload.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SourceFormatError("GitHub commit endpoint did not return a valid 40-character SHA")
    return sha


def parse_front_matter(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SourceFormatError("Markdown page is missing YAML front matter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise SourceFormatError("Markdown page has unterminated YAML front matter") from exc
    result: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[match.group(1)] = value
    return result


def iter_markdown_links(markdown: str) -> Iterator[tuple[str, str]]:
    """Yield simple Markdown [label](target) links, including nested/escaped labels."""
    for line in markdown.splitlines():
        pos = 0
        while pos < len(line):
            start = line.find("[", pos)
            if start < 0:
                break
            depth = 1
            i = start + 1
            while i < len(line):
                char = line[i]
                if char == "\\":
                    i += 2
                    continue
                if char == "[":
                    depth += 1
                elif char == "]":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            if depth != 0:
                pos = start + 1
                continue
            if i + 1 >= len(line) or line[i + 1] != "(":
                pos = i + 1
                continue
            close = line.find(")", i + 2)
            if close < 0:
                pos = i + 1
                continue
            label = line[start + 1:i]
            target = line[i + 2:close]
            yield label, target
            pos = close + 1


def decode_markdown_label(label: str) -> str:
    """Decode HTML entities and Markdown escapes while retaining exact spelling."""
    decoded = html.unescape(label)
    return re.sub(r"\\([\\*_{}\[\]()#+.!|>~-])", r"\1", decoded).strip()


def parse_initial_index(markdown: str) -> list[tuple[str, str]]:
    metadata = parse_front_matter(markdown)
    if metadata.get("kind") != "dictionary-index":
        raise SourceFormatError("Expected dictionary-index front matter")
    initials = []
    for label, target in iter_markdown_links(markdown):
        match = re.fullmatch(r"browse/([a-z_])/INDEX\.md", target)
        if match:
            initials.append((match.group(1), target))
    if not initials:
        raise SourceFormatError("No alphabetical browse indexes were found")
    return initials


def parse_letter_index(markdown: str) -> list[str]:
    metadata = parse_front_matter(markdown)
    if metadata.get("kind") != "alphabetical-letter-index":
        raise SourceFormatError("Expected alphabetical-letter-index front matter")
    pages = []
    for _label, target in iter_markdown_links(markdown):
        if re.fullmatch(r"\d{4}\.md", target):
            pages.append(target)
    if not pages:
        raise SourceFormatError("No numbered headword pages were found in a letter index")
    return pages


def stable_headword_id(word: str) -> str:
    digest = hashlib.sha256(("en\0" + word).encode("utf-8")).hexdigest()
    return "en-hw-" + digest[:24]


def parse_headword_page(
    markdown: str,
    page_path: str,
    *,
    expected_snapshot_id: str | None = None,
    repository: str = DEFAULT_REPOSITORY,
    commit_sha: str = "main",
) -> list[dict[str, str]]:
    metadata = parse_front_matter(markdown)
    if metadata.get("kind") != "alphabetical-headword-page":
        raise SourceFormatError(f"Unexpected page kind in {page_path}")
    snapshot_id = metadata.get("snapshot_id", "")
    if not snapshot_id:
        raise SourceFormatError(f"Missing snapshot_id in {page_path}")
    if expected_snapshot_id and snapshot_id != expected_snapshot_id:
        raise SourceFormatError(f"Snapshot mismatch in {page_path}: {snapshot_id}")
    base_dir = posixpath.dirname(page_path)
    rows: list[dict[str, str]] = []
    for label, target in iter_markdown_links(markdown):
        if not target.startswith("../../entries/") or not target.endswith(".md"):
            continue
        word = decode_markdown_label(label)
        if not word:
            raise SourceFormatError(f"Empty headword in {page_path}")
        entry_path = posixpath.normpath(posixpath.join(base_dir, target))
        if not entry_path.startswith("dictionary/entries/") or ".." in entry_path.split("/"):
            raise SourceFormatError(f"Unsafe entry target in {page_path}: {target}")
        rows.append({
            "headword_id": stable_headword_id(word),
            "language": "en",
            "headword_candidate": word,
            "lookup_key": word.casefold(),
            "headword_source": "alphabetical_browse_label; verify against entry front matter before sense ingestion",
            "entry_path": entry_path,
            "entry_url": f"https://github.com/{repository}/blob/{commit_sha}/{entry_path}",
            "source_snapshot_id": snapshot_id,
            "data_license": "per-entry; inspect entry front matter and repository LICENSE.md",
        })
    declared = metadata.get("headwords")
    if declared and declared.isdigit() and int(declared) != len(rows):
        raise SourceFormatError(
            f"Headword count mismatch in {page_path}: declared {declared}, parsed {len(rows)}"
        )
    if not rows:
        raise SourceFormatError(f"No headword entry links found in {page_path}")
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def import_headwords(
    *,
    repository: str = DEFAULT_REPOSITORY,
    ref: str = DEFAULT_REF,
    output: Path = DEFAULT_OUTPUT,
    workers: int = 4,
    max_pages: int | None = None,
    fetch_text=_request_text,
    resolved_commit: str | None = None,
) -> dict:
    """Fetch all compact index pages and write a compressed headword inventory."""
    if workers < 1 or workers > 16:
        raise ValueError("workers must be between 1 and 16")
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    commit_sha = resolved_commit or resolve_commit(repository, ref)
    raw_base = f"https://raw.githubusercontent.com/{repository}/{commit_sha}/"

    root_path = "dictionary/INDEX.md"
    root_markdown = fetch_text(raw_base + root_path)
    root_metadata = parse_front_matter(root_markdown)
    if root_metadata.get("kind") != "dictionary-index":
        raise SourceFormatError("The root dictionary index has an unexpected kind")
    expected_headwords = int(root_metadata.get("headwords", "0"))
    if expected_headwords <= 0:
        raise SourceFormatError("The root dictionary index is missing its headword count")
    source_markdown = fetch_text(raw_base + "dictionary/SOURCE.md")
    source_metadata = parse_front_matter(source_markdown)
    if source_metadata.get("kind") != "public-source-snapshot":
        raise SourceFormatError("The source metadata page has an unexpected kind")
    snapshot_id = source_metadata.get("snapshot_id", "")
    if not snapshot_id:
        raise SourceFormatError("The source metadata page is missing its snapshot_id")

    page_paths: list[str] = []
    initials = parse_initial_index(root_markdown)
    for initial, index_path in initials:
        letter_markdown = fetch_text(raw_base + "dictionary/" + index_path)
        letter_meta = parse_front_matter(letter_markdown)
        if letter_meta.get("snapshot_id") != snapshot_id:
            raise SourceFormatError(f"Snapshot mismatch in browse index {index_path}")
        for page_name in parse_letter_index(letter_markdown):
            page_paths.append(f"dictionary/browse/{initial}/{page_name}")

    complete = max_pages is None or max_pages >= len(page_paths)
    selected_paths = page_paths if max_pages is None else page_paths[:max_pages]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(output.name + ".tmp")
    seen: set[str] = set()
    word_count = 0
    duplicate_count = 0
    try:
        with gzip.open(temporary_output, "wt", encoding="utf-8", newline="\n", compresslevel=6) as stream:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = pool.map(lambda path: (path, fetch_text(raw_base + path)), selected_paths)
                for page_number, (page_path, markdown) in enumerate(futures, start=1):
                    rows = parse_headword_page(
                        markdown, page_path, expected_snapshot_id=snapshot_id,
                        repository=repository, commit_sha=commit_sha,
                    )
                    for row in rows:
                        word = row["headword_candidate"]
                        if word in seen:
                            duplicate_count += 1
                            continue
                        seen.add(word)
                        stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                        word_count += 1
                    if page_number % 25 == 0 or page_number == len(selected_paths):
                        print(f"Processed {page_number}/{len(selected_paths)} headword pages; {word_count:,} unique headwords", file=sys.stderr)
        if complete and word_count != expected_headwords:
            raise SourceFormatError(
                f"Final count mismatch: source index declares {expected_headwords:,}, parsed {word_count:,}"
            )
        os.replace(temporary_output, output)
    except Exception:
        temporary_output.unlink(missing_ok=True)
        raise

    manifest = {
        "manifest_version": "usg-external-headword-inventory/0.1.0",
        "source_repository": f"https://github.com/{repository}",
        "source_ref_requested": ref,
        "source_commit_sha": commit_sha,
        "source_snapshot_id": snapshot_id,
        "source_dump_date": source_metadata.get("dump_date"),
        "source_extraction_date": source_metadata.get("extraction_date"),
        "source_data_license": source_metadata.get("license"),
        "source_index_path": root_path,
        "language": "en",
        "expected_headwords": expected_headwords,
        "imported_unique_headword_candidates": word_count,
        "duplicate_headwords_skipped": duplicate_count,
        "alphabetical_pages_total": len(page_paths),
        "alphabetical_pages_imported": len(selected_paths),
        "complete": complete and word_count == expected_headwords,
        "output_file": str(output),
        "output_sha256": _sha256_file(output),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "content_rights_policy": (
            "Per-entry rights apply. The source repository's base English Wiktionary-derived text is CC BY-SA 4.0; "
            "supplemental records may carry distinct licences. Inspect the entry front matter and repository LICENSE.md. "
            "Preserve source-page/history attribution, licence notices, and notices of changes; do not infer a single licence for all records."
        ),
        "usage_boundary": (
            "Headwords are vocabulary candidates only. They are not USG lexical senses and must not be inserted into "
            "LexicalResource until lemma, part of speech, sense identity, and provenance are independently mapped."
        ),
    }
    _atomic_json(output.with_suffix(output.suffix + ".manifest.json"), manifest)
    return manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import compact English headword indexes for USG.")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF, help="Branch, tag, or commit; resolved to a commit SHA before download.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-pages", type=int, default=None, help="Optional pilot limit; omit to import the complete inventory.")
    args = parser.parse_args(argv)
    try:
        manifest = import_headwords(
            repository=args.repository, ref=args.ref, output=args.output,
            workers=args.workers, max_pages=args.max_pages,
        )
    except (OSError, ValueError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
