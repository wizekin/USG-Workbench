"""Incremental retrieval orchestration and explicit USG candidate export."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import unicodedata
from typing import Any, Iterable

from .analysis import analyze_bundle
from .cache import LexicalCache
from .providers import (
    DictionaryApiDevProvider,
    EnglishDictionaryGitHubProvider,
    FreeDictionaryApiProvider,
    ProviderNotFound,
    ProviderRateLimited,
    utc_now,
)


SUCCESS_TTL_SECONDS = 30 * 24 * 60 * 60
NEGATIVE_TTL_SECONDS = 60 * 60
DEFAULT_PROVIDER_ORDER = (
    "freedictionaryapi",
    "dictionaryapi_dev",
    "english_dictionary_github",
)


def normalize_lookup_form(word: str) -> str:
    if not isinstance(word, str):
        raise TypeError("word must be a string")
    value = unicodedata.normalize("NFC", word).strip()
    if not value or len(value) > 200 or any(ord(char) < 32 for char in value):
        raise ValueError("word must contain 1–200 visible characters")
    return value


def lexical_cache_key(word: str) -> str:
    # Case is retained because the GitHub source has distinct entries such as A and a.
    return "en-v1:" + unicodedata.normalize("NFC", word)


class ExternalLexicalService:
    def __init__(
        self,
        cache: LexicalCache | None = None,
        providers: Iterable[Any] | None = None,
    ):
        self.cache = cache or LexicalCache()
        if providers is None:
            github_sha = self.cache.get_state("english_dictionary_github", "main_commit")
            providers = (
                FreeDictionaryApiProvider(),
                DictionaryApiDevProvider(),
                EnglishDictionaryGitHubProvider(commit_sha=github_sha),
            )
        self.providers = {provider.provider_id: provider for provider in providers}

    def lookup(
        self,
        word: str,
        *,
        refresh: bool = False,
        offline: bool = False,
        providers: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        form = normalize_lookup_form(word)
        key = lexical_cache_key(form)
        self.cache.record_access(key, form)
        cached = self.cache.get_record(key)
        if cached and not refresh:
            payload = cached["payload"]
            payload["cache"] = {"hit": True, "stale": False, "fetched_at": cached["fetched_at"]}
            if cached["analysis"] is not None:
                payload["analysis"] = cached["analysis"]
            return payload
        stale = self.cache.get_record(key, allow_expired=True) if refresh or offline else None
        if offline:
            if stale:
                payload = stale["payload"]
                payload["cache"] = {"hit": True, "stale": stale["is_stale"], "offline": True}
                payload["analysis"] = stale["analysis"]
                return payload
            return {
                "schema_version": "usg-external-lexical/0.1.0",
                "queried_form": form,
                "status": "cache_miss_offline",
                "sources": [],
                "entries": [],
                "provider_statuses": [],
                "cache": {"hit": False, "offline": True},
            }

        selected = list(providers) if providers is not None else list(DEFAULT_PROVIDER_ORDER)
        unknown = [provider for provider in selected if provider not in self.providers]
        if unknown:
            raise ValueError("Unknown provider(s): " + ", ".join(unknown))
        source_records: list[dict[str, Any]] = []
        entries: list[dict[str, Any]] = []
        statuses = []
        for provider_id in selected:
            provider = self.providers[provider_id]
            try:
                if provider_id == "freedictionaryapi":
                    # Their published cap is 1,000 requests/hour/IP; leave a safety margin.
                    self.cache.reserve_provider_request(provider_id, maximum=900, window_seconds=3600)
                result = provider.lookup(form)
                source = dict(result.get("source") or {})
                source.setdefault("provider", provider_id)
                source_records.append(source)
                for entry in result.get("entries", []):
                    if not isinstance(entry, dict):
                        continue
                    normalized = dict(entry)
                    normalized["provider"] = provider_id
                    normalized["source_id"] = source.get("source_entry_id") or source.get("snapshot_id") or provider_id
                    entries.append(normalized)
                statuses.append({"provider": provider_id, "status": "ok", "entry_count": len(result.get("entries", []))})
                if provider_id == "english_dictionary_github":
                    commit_sha = getattr(provider, "_commit_sha", None)
                    if commit_sha:
                        self.cache.set_state(provider_id, "main_commit", commit_sha)
            except ProviderNotFound as exc:
                statuses.append({"provider": provider_id, "status": "not_found", "message": str(exc)})
            except (ProviderRateLimited, RuntimeError) as exc:
                statuses.append({"provider": provider_id, "status": "rate_limited_or_budget_limited", "message": str(exc)})
            except Exception as exc:  # One provider failure must not discard another provider's result.
                statuses.append({"provider": provider_id, "status": "error", "message": f"{type(exc).__name__}: {exc}"})

        if entries:
            status = "found_with_provider_warnings" if any(item["status"] != "ok" for item in statuses) else "found"
        elif statuses and all(item["status"] == "not_found" for item in statuses):
            status = "not_found"
        else:
            status = "provider_failure_or_no_data"
        bundle = {
            "schema_version": "usg-external-lexical/0.1.0",
            "queried_form": form,
            "lookup_key": key,
            "created_at": utc_now(),
            "status": status,
            "sources": source_records,
            "entries": entries,
            "provider_statuses": statuses,
            "cache": {"hit": False, "stale_fallback_available": bool(stale)},
            "integration_boundary": {
                "runtime_lexical_resource_modified": False,
                "automatic_promotion": False,
                "note": "This bundle is external evidence and candidate knowledge, not an accepted runtime USG lexical resource.",
            },
        }
        analysis = analyze_bundle(bundle)
        bundle["analysis"] = analysis
        self.cache.save_analysis_observations(key, analysis["definition_pattern_observations"])
        ttl = SUCCESS_TTL_SECONDS if entries else NEGATIVE_TTL_SECONDS
        if entries or status == "not_found":
            self.cache.put_record(key, form, bundle, analysis, status=status, ttl_seconds=ttl)
        elif stale:
            payload = stale["payload"]
            payload["cache"] = {"hit": True, "stale": True, "refresh_failed": statuses}
            payload["refresh_status"] = status
            payload["analysis"] = stale["analysis"]
            return payload
        return bundle

    def analyze(self, word: str, **kwargs) -> dict[str, Any]:
        result = self.lookup(word, **kwargs)
        if "analysis" in result:
            return result["analysis"]
        return analyze_bundle(result)

    def export_usg_candidates(self, word: str, **kwargs) -> dict[str, Any]:
        """Build a versioned candidate package; never edits canonical USG resources."""
        bundle = self.lookup(word, **kwargs)
        candidates = []
        for entry in bundle.get("entries", []):
            for sense in entry.get("senses", []) or []:
                if not isinstance(sense, dict):
                    continue
                candidates.append({
                    "candidate_id": sense.get("sense_id"),
                    "lemma": entry.get("lemma"),
                    "language": entry.get("language", "en"),
                    "part_of_speech": sense.get("part_of_speech") or entry.get("part_of_speech"),
                    "definition": sense.get("definition"),
                    "examples": sense.get("examples", []),
                    "features": sense.get("tags", []),
                    "source_provider": entry.get("provider"),
                    "source_id": entry.get("source_id"),
                    "source_sense_id": sense.get("source_sense_id"),
                    "relations": sense.get("relations", []),
                    "promotion_status": "candidate_only",
                })
        digest = hashlib.sha256(
            repr(sorted((item.get("candidate_id"), item.get("definition")) for item in candidates)).encode("utf-8")
        ).hexdigest()
        return {
            "contract": "USG-LEXICAL-CANDIDATES/0.1.0",
            "queried_form": bundle.get("queried_form"),
            "candidate_count": len(candidates),
            "candidates": candidates,
            "source_provenance": bundle.get("sources", []),
            "validation": bundle.get("analysis", {}).get("validation"),
            "content_digest": digest,
            "promotion_allowed": False,
            "integration_note": "This adapter is deliberately non-mutating. A separate conformance-tested mapping must be approved before any candidate can enter a runtime LexicalResource.",
        }

    def activity(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.cache.activity(limit=limit)

    def close(self) -> None:
        self.cache.close()
