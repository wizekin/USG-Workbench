"""On-demand adapters for the public lexical sources used by USG.

No provider downloads a corpus. Every adapter retrieves only the requested word,
normalizes the result without merging source senses, and preserves provenance.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
import json
import posixpath
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "USG-External-Lexical-Retrieval/0.1 (+https://github.com/wizekin/USG-Workbench)"
GITHUB_REPOSITORY = "figueirego/english-dictionary"


class ProviderError(RuntimeError):
    """A provider could not return a usable response."""


class ProviderNotFound(ProviderError):
    """The provider has no record for the requested spelling."""


class ProviderRateLimited(ProviderError):
    """A provider refused the request because of rate limits."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_id(*parts: str) -> str:
    raw = "\0".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


class HttpClient:
    """Small standard-library HTTP client with bounded retries and response sizes."""

    def __init__(self, timeout: float = 20.0, max_bytes: int = 12_000_000, retries: int = 2):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.retries = retries

    def _get(self, url: str) -> tuple[bytes, dict[str, str]]:
        if not url.startswith("https://"):
            raise ProviderError("Only HTTPS provider URLs are permitted")
        for attempt in range(self.retries + 1):
            request = Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/markdown, text/plain;q=0.9, */*;q=0.1",
            })
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read(self.max_bytes + 1)
                    if len(raw) > self.max_bytes:
                        raise ProviderError("Provider response exceeded the configured size limit")
                    headers = {key.lower(): value for key, value in response.headers.items()}
                    return raw, headers
            except HTTPError as exc:
                if exc.code == 404:
                    raise ProviderNotFound(f"Word not found (HTTP 404): {url}") from exc
                if exc.code == 429:
                    retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                    raise ProviderRateLimited(f"Provider rate limited the request; Retry-After={retry_after}") from exc
                if exc.code not in {500, 502, 503, 504} or attempt >= self.retries:
                    raise ProviderError(f"Provider returned HTTP {exc.code}") from exc
            except (URLError, TimeoutError) as exc:
                if attempt >= self.retries:
                    raise ProviderError(f"Provider request failed: {exc}") from exc
            time.sleep(min(2 ** attempt, 5))
        raise ProviderError("Provider request failed after retries")

    def get_json(self, url: str) -> tuple[Any, dict[str, str]]:
        raw, headers = self._get(url)
        try:
            return json.loads(raw.decode("utf-8")), headers
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("Provider returned invalid UTF-8 JSON") from exc

    def get_text(self, url: str) -> tuple[str, dict[str, str]]:
        raw, headers = self._get(url)
        try:
            return raw.decode("utf-8"), headers
        except UnicodeDecodeError as exc:
            raise ProviderError("Provider returned non-UTF-8 text") from exc

    def get_bytes(self, url: str) -> tuple[bytes, dict[str, str]]:
        """Return a bounded binary response for immutable compressed evidence shards."""
        return self._get(url)


def _as_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _relation_items(values: Any, relation_type: str, provider: str, sense_id: str | None) -> list[dict[str, Any]]:
    result = []
    for target in _as_strings(values):
        result.append({
            "relation_id": "rel-" + stable_id(provider, sense_id or "entry", relation_type, target),
            "type": relation_type,
            "target_lemma": target,
            "scope": "sense" if sense_id else "entry",
            "source_sense_id": sense_id,
            "target_sense_id": None,
            "evidence": "Explicit relation field returned by provider",
            "status": "source_asserted_unvalidated",
        })
    return result


def _walk_freedict_senses(
    senses: Any, provider: str, word: str, entry_index: int, part_of_speech: str,
    parent_path: str = "",
    parent_sense_id: str | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if not isinstance(senses, list):
        return result
    for index, raw in enumerate(senses, start=1):
        if not isinstance(raw, dict):
            continue
        definition = raw.get("definition")
        if not isinstance(definition, str) or not definition.strip():
            continue
        path = f"{parent_path}.{index}" if parent_path else str(index)
        sense_id = "fd-" + stable_id(word, entry_index, part_of_speech, path, definition)
        relations = _relation_items(raw.get("synonyms"), "synonym", provider, sense_id)
        relations += _relation_items(raw.get("antonyms"), "antonym", provider, sense_id)
        result.append({
            "sense_id": sense_id,
            "source_sense_id": path,
            "part_of_speech": part_of_speech or None,
            "definition": definition.strip(),
            "examples": _as_strings(raw.get("examples")),
            "tags": _as_strings(raw.get("tags")),
            "relations": relations,
            "parent_sense_id": parent_sense_id,
        })
        result.extend(_walk_freedict_senses(
            raw.get("subsenses"), provider, word, entry_index, part_of_speech, path, sense_id
        ))
    return result


class FreeDictionaryApiProvider:
    """Adapter for https://freedictionaryapi.com/ (Wiktionary-backed API)."""

    provider_id = "freedictionaryapi"
    base_url = "https://freedictionaryapi.com/api/v1"

    def __init__(self, client: HttpClient | None = None):
        self.client = client or HttpClient()

    def lookup(self, word: str) -> dict[str, Any]:
        url = f"{self.base_url}/entries/en/{quote(word, safe='')}"
        payload, _headers = self.client.get_json(url)
        if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
            raise ProviderError("FreeDictionaryAPI response did not match the documented entries shape")
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        license_data = source.get("license") if isinstance(source.get("license"), dict) else {}
        source_url = source.get("url") if isinstance(source.get("url"), str) else None
        normalized_entries = []
        for entry_index, raw in enumerate(payload["entries"], start=1):
            if not isinstance(raw, dict):
                continue
            language = raw.get("language") if isinstance(raw.get("language"), dict) else {}
            language_code = language.get("code") if isinstance(language.get("code"), str) else "en"
            if language_code.lower() not in {"en", "eng"}:
                continue
            pos = raw.get("partOfSpeech") if isinstance(raw.get("partOfSpeech"), str) else ""
            forms = []
            for form in raw.get("forms", []) if isinstance(raw.get("forms"), list) else []:
                if isinstance(form, dict) and isinstance(form.get("word"), str):
                    forms.append({"form": form["word"], "tags": _as_strings(form.get("tags")), "source": "provider"})
            pronunciations = []
            for pronunciation in raw.get("pronunciations", []) if isinstance(raw.get("pronunciations"), list) else []:
                if isinstance(pronunciation, dict):
                    pronunciations.append({
                        "text": pronunciation.get("text"),
                        "type": pronunciation.get("type"),
                        "tags": _as_strings(pronunciation.get("tags")),
                    })
            senses = _walk_freedict_senses(raw.get("senses"), self.provider_id, word, entry_index, pos)
            if not senses and not forms:
                continue
            entry_id = "fd-entry-" + stable_id(word, entry_index, pos, source_url or "")
            entry_relations = _relation_items(raw.get("synonyms"), "synonym", self.provider_id, None)
            entry_relations += _relation_items(raw.get("antonyms"), "antonym", self.provider_id, None)
            normalized_entries.append({
                "entry_id": entry_id,
                "lemma": payload.get("word") if isinstance(payload.get("word"), str) else word,
                "language": "en",
                "part_of_speech": pos or None,
                "forms": forms,
                "pronunciations": pronunciations,
                "senses": senses,
                "relations": entry_relations,
                "source_record_id": None,
            })
        if not normalized_entries:
            raise ProviderNotFound(f"FreeDictionaryAPI has no English senses for {word!r}")
        return {
            "provider": self.provider_id,
            "queried_form": word,
            "retrieved_at": utc_now(),
            "source": {
                "provider": self.provider_id,
                "provider_url": "https://freedictionaryapi.com/",
                "record_url": source_url,
                "license": license_data.get("name") if isinstance(license_data.get("name"), str) else "CC BY-SA 4.0 (provider-declared data source)",
                "license_url": license_data.get("url") if isinstance(license_data.get("url"), str) else "https://creativecommons.org/licenses/by-sa/4.0/",
                "attribution": "FreeDictionaryAPI.com and the linked original Wiktionary page",
                "rights_note": "Preserve the exact source URL and visible attribution; verify each source's applicable terms before redistribution.",
            },
            "entries": normalized_entries,
            "raw_schema": "freedictionaryapi-v1",
        }


class DictionaryApiDevProvider:
    """Adapter for dictionaryapi.dev v2; optional fields are handled defensively."""

    provider_id = "dictionaryapi_dev"
    base_url = "https://api.dictionaryapi.dev/api/v2/entries/en"

    def __init__(self, client: HttpClient | None = None):
        self.client = client or HttpClient()

    def lookup(self, word: str) -> dict[str, Any]:
        url = f"{self.base_url}/{quote(word, safe='')}"
        payload, _headers = self.client.get_json(url)
        if not isinstance(payload, list):
            raise ProviderError("dictionaryapi.dev response was not the documented v2 entry array")
        normalized_entries = []
        for entry_index, raw in enumerate(payload, start=1):
            if not isinstance(raw, dict):
                continue
            lemma = raw.get("word") if isinstance(raw.get("word"), str) else word
            phonetics = []
            raw_phonetics = raw.get("phonetics", [])
            if isinstance(raw_phonetics, list):
                for item in raw_phonetics:
                    if isinstance(item, dict):
                        phonetics.append({"text": item.get("text"), "audio": item.get("audio")})
            forms = []
            meanings = raw.get("meanings", [])
            if not isinstance(meanings, list):
                continue
            for meaning_index, meaning in enumerate(meanings, start=1):
                if not isinstance(meaning, dict):
                    continue
                pos = meaning.get("partOfSpeech") if isinstance(meaning.get("partOfSpeech"), str) else ""
                definitions = meaning.get("definitions", [])
                if not isinstance(definitions, list):
                    continue
                senses = []
                for definition_index, definition in enumerate(definitions, start=1):
                    if not isinstance(definition, dict):
                        continue
                    gloss = definition.get("definition")
                    if not isinstance(gloss, str) or not gloss.strip():
                        continue
                    sense_id = "dd-" + stable_id(word, entry_index, meaning_index, definition_index, gloss)
                    relations = _relation_items(definition.get("synonyms"), "synonym", self.provider_id, sense_id)
                    relations += _relation_items(definition.get("antonyms"), "antonym", self.provider_id, sense_id)
                    examples = [definition["example"]] if isinstance(definition.get("example"), str) and definition["example"].strip() else []
                    senses.append({
                        "sense_id": sense_id,
                        "source_sense_id": f"{meaning_index}.{definition_index}",
                        "part_of_speech": pos or None,
                        "definition": gloss.strip(),
                        "examples": examples,
                        "tags": _as_strings(definition.get("tags")),
                        "relations": relations,
                        "parent_sense_id": None,
                    })
                if senses:
                    normalized_entries.append({
                        "entry_id": "dd-entry-" + stable_id(word, entry_index, meaning_index, pos),
                        "lemma": lemma,
                        "language": "en",
                        "part_of_speech": pos or None,
                        "forms": forms,
                        "pronunciations": phonetics,
                        "senses": senses,
                        "relations": [],
                        "source_record_id": str(meaning_index),
                    })
        if not normalized_entries:
            raise ProviderNotFound(f"dictionaryapi.dev has no definitions for {word!r}")
        first = payload[0] if payload and isinstance(payload[0], dict) else {}
        license_data = first.get("license") if isinstance(first.get("license"), dict) else {}
        source_urls = _as_strings(first.get("sourceUrls"))
        return {
            "provider": self.provider_id,
            "queried_form": word,
            "retrieved_at": utc_now(),
            "source": {
                "provider": self.provider_id,
                "provider_url": "https://dictionaryapi.dev/",
                "record_urls": source_urls,
                "license": license_data.get("name") if isinstance(license_data.get("name"), str) else "not_declared_in_response",
                "license_url": license_data.get("url") if isinstance(license_data.get("url"), str) else None,
                "attribution": "dictionaryapi.dev; source-page links are retained when supplied",
                "rights_note": "The response does not always declare a data licence. Do not redistribute cached text unless rights are confirmed.",
            },
            "entries": normalized_entries,
            "raw_schema": "dictionaryapi-dev-v2",
        }


def _markdown_links(markdown: str):
    for line in markdown.splitlines():
        position = 0
        while position < len(line):
            start = line.find("[", position)
            if start < 0:
                break
            depth = 1
            cursor = start + 1
            while cursor < len(line):
                char = line[cursor]
                if char == "\\":
                    cursor += 2
                    continue
                if char == "[":
                    depth += 1
                elif char == "]":
                    depth -= 1
                    if depth == 0:
                        break
                cursor += 1
            if depth or cursor + 1 >= len(line) or line[cursor + 1] != "(":
                position = max(cursor + 1, start + 1)
                continue
            close = line.find(")", cursor + 2)
            if close < 0:
                position = cursor + 1
                continue
            label = re.sub(r"\\([\\*_{}\[\]()#+.!|>~-])", r"\1", html.unescape(line[start + 1:cursor])).strip()
            yield label, line[cursor + 2:close].strip()
            position = close + 1


def _front_matter(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ProviderError("English dictionary entry has no YAML front matter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ProviderError("English dictionary entry has unterminated front matter")
    result = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            try:
                value = json.loads(value) if value[0] == '"' else value[1:-1]
            except json.JSONDecodeError:
                value = value[1:-1]
        result[match.group(1)] = value
    return result


def parse_english_dictionary_entry(markdown: str, queried_word: str, entry_url: str) -> dict[str, Any]:
    """Parse each source record and source sense independently; never collapse senses."""
    metadata = _front_matter(markdown)
    entry_id = metadata.get("entry_id")
    if not entry_id or metadata.get("kind") != "dictionary-entry":
        raise ProviderError("Unexpected English dictionary entry format")
    source_url = metadata.get("source_url")
    history_url = metadata.get("history_url")
    snapshot_id = metadata.get("snapshot_id")
    license_name = metadata.get("license", "not_declared")
    body_start = markdown.find("\n---", 3)
    body = markdown[body_start + 4:] if body_start >= 0 else markdown
    heading_matches = [
        heading
        for heading in re.finditer(
            r"(?m)^##\s+(.+?)(?:\s+·\s+Etymology\s+\d+\s+·\s+Record\s+(\d+))?\s*$",
            body,
        )
        if heading.group(1).strip().casefold() not in {"source gaps", "sources"}
    ]
    normalized_entries = []
    for index, heading in enumerate(heading_matches):
        record_text = body[heading.end():heading_matches[index + 1].start() if index + 1 < len(heading_matches) else len(body)]
        pos = heading.group(1).strip()
        # Older exports include explicit etymology/record numbers. Simpler
        # source records use a plain POS heading, so assign a stable local order.
        record_number = heading.group(2) or str(index + 1)
        sense_markers = list(re.finditer(r"(?m)^<a id=\"r(\d+)-s(\d+)\"></a>\s*$", record_text))
        forms = []
        forms_match = re.search(r"(?ms)^### Forms\s*\n(.*?)(?=^### |\Z)", record_text)
        if forms_match:
            for form_line in forms_match.group(1).splitlines():
                form_match = re.match(r"^\s*-\s+(.+?)(?:\s+[—–]\s+(.+))?\s*$", form_line)
                if form_match:
                    forms.append({"form": form_match.group(1).strip(), "tags": [form_match.group(2).strip()] if form_match.group(2) else []})
        record_relations = []
        related_match = re.search(r"(?ms)^### Related words\s*\n(.*?)(?=^### |\Z)", record_text)
        if related_match:
            for relation_line in related_match.group(1).splitlines():
                relation_match = re.search(r"\*\*Source (synonyms|antonyms):\*\*\s*(.*)$", relation_line)
                if not relation_match:
                    continue
                relation_type = "synonym" if relation_match.group(1) == "synonyms" else "antonym"
                for label, target in _markdown_links(relation_line):
                    if target.startswith("../../entries/"):
                        record_relations.append({
                            "relation_id": "rel-" + stable_id(entry_id, record_number, relation_type, label),
                            "type": relation_type,
                            "target_lemma": label,
                            "scope": "entry",
                            "source_sense_id": None,
                            "target_sense_id": None,
                            "evidence": "Source explicitly labels this related-word link; source metadata says relation scope is entry-level, not sense-resolved.",
                            "status": "source_asserted_unvalidated",
                        })
        senses = []
        for sense_index, marker in enumerate(sense_markers):
            block_end = sense_markers[sense_index + 1].start() if sense_index + 1 < len(sense_markers) else len(record_text)
            block = record_text[marker.end():block_end]
            label_match = re.search(r"\*\*Source sense (R\d+\.S\d+)\*\*", block)
            definition_match = re.search(r"(?m)^\s*\d+\.\s+(.+?)\s*$", block)
            if not label_match or not definition_match:
                continue
            source_sense = label_match.group(1)
            definition = definition_match.group(1).strip()
            examples = re.findall(r"(?m)^\s*\*\*Example:\*\*\s*(.+?)\s*$", block)
            tags = []
            for label in ("Usage", "Source topics (extractor hierarchy; not curated)"):
                tags.extend(re.findall(r"(?m)^\s*\*\*" + re.escape(label) + r":\*\*\s*(.+?)\s*$", block))
            senses.append({
                "sense_id": f"{entry_id}:{source_sense}",
                "source_sense_id": source_sense,
                "part_of_speech": pos,
                "definition": definition,
                "examples": examples,
                "tags": tags,
                "relations": [],
                "parent_sense_id": None,
            })
        if senses or record_text.strip():
            normalized_entries.append({
                "entry_id": f"{entry_id}:record:{record_number}",
                "lemma": metadata.get("headword", queried_word),
                "language": "en",
                "part_of_speech": pos,
                "forms": forms,
                "pronunciations": [],
                "senses": senses,
                "relations": record_relations,
                "source_record_id": record_number,
            })
    if not normalized_entries:
        raise ProviderNotFound(f"Source entry contains no parseable English records for {queried_word!r}")
    return {
        "provider": "english_dictionary_github",
        "queried_form": queried_word,
        "retrieved_at": utc_now(),
        "source": {
            "provider": "figueirego/english-dictionary",
            "provider_url": "https://github.com/figueirego/english-dictionary",
            "record_url": source_url,
            "history_url": history_url,
            "entry_file_url": entry_url,
            "snapshot_id": snapshot_id,
            "source_entry_id": entry_id,
            "license": license_name,
            "attribution": "Wiktionary contributors, Kaikki/Wiktextract; see the source entry and repository licensing notice",
            "editorial_review_status": metadata.get("review_status"),
            "relation_link_scope": metadata.get("relation_link_scope", "unspecified"),
            "rights_note": "The upstream repository documents per-entry and per-supplement rights. Preserve source/history links and verify applicable terms before redistribution.",
        },
        "entries": normalized_entries,
        "raw_schema": "figueirego-english-dictionary-entry-v1",
    }


class EnglishDictionaryGitHubProvider:
    """Locate one spelling in the compact alphabetical indexes, then fetch its entry only."""

    provider_id = "english_dictionary_github"
    repository = GITHUB_REPOSITORY
    branch = "main"

    def __init__(self, client: HttpClient | None = None, commit_sha: str | None = None):
        self.client = client or HttpClient()
        self._commit_sha: str | None = commit_sha

    def _raw_url(self, path: str) -> str:
        if not self._commit_sha:
            url = f"https://api.github.com/repos/{self.repository}/commits/{quote(self.branch, safe='')}"
            payload, _ = self.client.get_json(url)
            sha = payload.get("sha") if isinstance(payload, dict) else None
            if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ProviderError("GitHub did not return a valid pinned source commit")
            self._commit_sha = sha
        return f"https://raw.githubusercontent.com/{self.repository}/{self._commit_sha}/{path}"

    @staticmethod
    def _initial(word: str) -> str:
        import unicodedata
        first = unicodedata.normalize("NFKD", word[:1]).encode("ascii", "ignore").decode("ascii").casefold()
        return first if len(first) == 1 and "a" <= first <= "z" else "_"

    @staticmethod
    def _sort_key(value: str) -> tuple[str, str]:
        return value.casefold(), value

    def _find_page(self, word: str, initial: str) -> str:
        index_path = f"dictionary/browse/{initial}/INDEX.md"
        markdown, _ = self.client.get_text(self._raw_url(index_path))
        rows = []
        pattern = re.compile(r"\|\s*\[\d+\]\((\d{4}\.md)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|")
        for line in markdown.splitlines():
            match = pattern.search(line)
            if match:
                rows.append((match.group(1), html.unescape(match.group(2).strip().strip('"')), html.unescape(match.group(3).strip().strip('"'))))
        if not rows:
            raise ProviderNotFound(f"No browse pages found for initial {initial!r}")
        key = self._sort_key(word)
        for filename, first, last in rows:
            if self._sort_key(first) <= key <= self._sort_key(last):
                return f"dictionary/browse/{initial}/{filename}"
        # If a spelling falls outside the exact interval, choose the nearest lexical page.
        following = [row for row in rows if self._sort_key(row[1]) >= key]
        nearest = following[0] if following else rows[-1]
        return f"dictionary/browse/{initial}/{nearest[0]}"

    def lookup(self, word: str) -> dict[str, Any]:
        initial = self._initial(word)
        page_path = self._find_page(word, initial)
        page, _ = self.client.get_text(self._raw_url(page_path))
        entry_paths = []
        for label, target in _markdown_links(page):
            if not target.startswith("../../entries/") or not target.endswith(".md"):
                continue
            if label == word or label.casefold() == word.casefold():
                path = posixpath.normpath(posixpath.join(posixpath.dirname(page_path), target))
                if path.startswith("dictionary/entries/") and ".." not in path.split("/"):
                    entry_paths.append((label, path))
        if not entry_paths:
            raise ProviderNotFound(f"English dictionary browse index has no candidate for {word!r}")
        # Exact spelling wins; case-fold matches remain distinct candidates when the spelling is ambiguous.
        exact = [item for item in entry_paths if item[0] == word]
        chosen = exact or entry_paths
        normalized_entries = []
        sources = []
        for label, path in chosen:
            entry_url = self._raw_url(path)
            entry_markdown, _ = self.client.get_text(entry_url)
            parsed = parse_english_dictionary_entry(entry_markdown, word, entry_url)
            normalized_entries.extend(parsed["entries"])
            sources.append(parsed["source"])
        return {
            "provider": self.provider_id,
            "queried_form": word,
            "retrieved_at": utc_now(),
            "source": {
                "provider": "figueirego/english-dictionary",
                "provider_url": f"https://github.com/{self.repository}",
                "commit_sha": self._commit_sha,
                "records": sources,
                "license": "per-record; see each source entry",
                "attribution": "See source record metadata and repository LICENSE.md",
                "rights_note": "The browse index is used only to locate the requested entry; no bulk index or dictionary corpus is downloaded.",
            },
            "entries": normalized_entries,
            "raw_schema": "figueirego-english-dictionary-entry-v1",
        }
