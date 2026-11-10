"""Loopback-only HTTP API for the USG local semantic workbench."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from tools.document_analysis_services_v1_0_0 import DocumentAnalysisService
from tools.usg_interpretation_v0_1_0 import InterpretationService
from tools.semantic_graph_store_v1_0_0 import (
    CanonicalDocumentStore, DocumentNotFoundError, GraphStoreError,
    InvalidDocumentError, RevisionConflictError,
)
from tools.semantic_query_interface_v1_0_0 import PersistentQueryService

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_SCHEMA_PATH = ROOT / "specifications" / "usg-sem-1.0.schema.json"


class APIRequestError(ValueError):
    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        super().__init__(message)


class USGApplication:
    """Application dispatcher shared by HTTP and CLI; one SQLite store owner."""

    def __init__(self, database_path: str | Path):
        self.store = CanonicalDocumentStore(database_path)
        self.query_service = PersistentQueryService(self.store)
        self.analysis_service = DocumentAnalysisService()
        self.interpretation_service = InterpretationService()
        self.schema = json.loads(DOCUMENT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.validator = Draft202012Validator(self.schema, format_checker=FormatChecker())

    def close(self):
        self.store.close()

    def _validate(self, document: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self.validator.iter_errors(document), key=lambda e: e.json_path)
        if errors:
            return {
                "completion_status": "INVALID_INPUT",
                "diagnostics": [
                    {"path": e.json_path, "message": e.message} for e in errors
                ],
            }
        # Reuse the canonical store's complete source-hash, typed-reference,
        # grounding, and schema validation without creating a durable revision.
        with CanonicalDocumentStore(":memory:") as validator_store:
            stored = validator_store.put_document(document)
        return {
            "completion_status": "VALID",
            "document_id": stored.document_id,
            "document_sha256": stored.digest,
            "canonicalization_profile": stored.canonicalization_profile,
            "diagnostics": [],
            "safety": {"truth_promotion": False, "canonical_document_mutated": False},
        }

    @staticmethod
    def _revision(query: dict[str, list[str]]) -> int | None:
        values = query.get("revision")
        if not values:
            return None
        try:
            revision = int(values[0])
        except (TypeError, ValueError) as exc:
            raise APIRequestError(400, "REVISION_INVALID", "revision must be a positive integer") from exc
        if revision < 1:
            raise APIRequestError(400, "REVISION_INVALID", "revision must be a positive integer")
        return revision

    def dispatch(self, method: str, target: str, body: Any = None) -> tuple[int, Any]:
        parsed = urlsplit(target)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)

        try:
            if method == "GET" and path == "/health":
                return 200, {
                    "status": "ok",
                    "service": "USG-LOCAL-API/1.0.0",
                    "storage": "SQLite",
                    "canonical_profile": "USG-SEM/1.0",
                }

            if method == "POST" and path == "/v1/validate":
                if not isinstance(body, dict):
                    raise APIRequestError(400, "DOCUMENT_REQUIRED", "request body must be a USG-SEM/1.0 document")
                result = self._validate(body)
                return (200 if result["completion_status"] == "VALID" else 422), result

            if method == "POST" and path == "/v1/documents":
                if not isinstance(body, dict) or not isinstance(body.get("document"), dict):
                    raise APIRequestError(400, "DOCUMENT_REQUIRED", "body must contain a document object")
                expected = body.get("expected_revision")
                if expected is not None and (isinstance(expected, bool) or not isinstance(expected, int) or expected < 0):
                    raise APIRequestError(400, "EXPECTED_REVISION_INVALID", "expected_revision must be a non-negative integer")
                stored = self.store.put_document(body["document"], expected_revision=expected)
                return 201 if stored.status == "STORED" else 200, {
                    **stored.metadata(),
                    "document": stored.document,
                    "idempotent": stored.status == "UNCHANGED",
                }

            if method == "POST" and path == "/v1/query":
                if not isinstance(body, dict) or not isinstance(body.get("document_id"), str) or not isinstance(body.get("query"), dict):
                    raise APIRequestError(400, "QUERY_REQUEST_INVALID", "body requires document_id and query")
                revision = body.get("revision")
                if revision is not None and (isinstance(revision, bool) or not isinstance(revision, int) or revision < 1):
                    raise APIRequestError(400, "REVISION_INVALID", "revision must be a positive integer")
                return 200, self.query_service.run(body["document_id"], body["query"], revision=revision)

            if method == "POST" and path == "/v1/interpret":
                if not isinstance(body, dict) or not isinstance(body.get("text"), str) or not isinstance(body.get("language"), str):
                    raise APIRequestError(400, "INTERPRET_REQUEST_INVALID", "body requires text and language strings")
                persist = body.get("persist", True)
                if not isinstance(persist, bool):
                    raise APIRequestError(400, "INTERPRET_REQUEST_INVALID", "persist must be a boolean")
                try:
                    result = self.interpretation_service.interpret(body["text"], body["language"])
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "INTERPRET_REQUEST_INVALID", str(exc)) from exc
                if persist:
                    stored = self.store.put_document(result["document"])
                    result["persistence"] = {
                        **stored.metadata(),
                        "idempotent": stored.status == "UNCHANGED",
                    }
                return 200, result

            parts = [unquote(part) for part in path.split("/") if part]
            if len(parts) >= 3 and parts[0:2] == ["v1", "documents"]:
                document_id = parts[2]
                revision = self._revision(query)
                if method == "GET" and len(parts) == 3:
                    stored = self.store.get_document(document_id, revision=revision)
                    return 200, {**stored.metadata(), "document": stored.document}
                if method == "GET" and len(parts) == 4 and parts[3] == "export":
                    stored = self.store.get_document(document_id, revision=revision)
                    return 200, stored.document
                if method == "GET" and len(parts) == 4 and parts[3] == "check":
                    return 200, self.store.verify_integrity(document_id, revision=revision)
                if method == "GET" and len(parts) == 4 and parts[3] == "revisions":
                    return 200, {"document_id": document_id, "revisions": self.store.list_revisions(document_id)}
                if method == "GET" and len(parts) == 4 and parts[3] in {"conditions", "contradictions"}:
                    stored = self.store.get_document(document_id, revision=revision)
                    if parts[3] == "conditions":
                        return 200, self.analysis_service.conditions(stored.document)
                    return 200, self.analysis_service.contradictions(stored.document)

            raise APIRequestError(404, "ROUTE_NOT_FOUND", "no route matches this request")
        except APIRequestError as exc:
            return exc.status, {"error": exc.code, "message": str(exc)}
        except RevisionConflictError as exc:
            return 409, {
                "error": "REVISION_CONFLICT",
                "message": str(exc),
                "document_id": exc.document_id,
                "current_revision": exc.current_revision,
                "expected_revision": exc.expected_revision,
            }
        except DocumentNotFoundError as exc:
            return 404, {"error": "DOCUMENT_NOT_FOUND", "message": str(exc)}
        except InvalidDocumentError as exc:
            return 422, {"error": "DOCUMENT_INVALID", "diagnostics": list(exc.diagnostics)}
        except GraphStoreError as exc:
            return 409, {"error": "STORAGE_INTEGRITY_ERROR", "message": str(exc)}
        except (ValueError, TypeError, KeyError) as exc:
            return 400, {"error": "REQUEST_INVALID", "message": str(exc)}


class _RequestHandler(BaseHTTPRequestHandler):
    server_version = "USG-Local-API/1.0.0"

    def _respond(self, status: int, payload: Any):
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self._respond(*self.server.application.dispatch("GET", self.path))

    def do_POST(self):
        length = self.headers.get("Content-Length")
        if length is None:
            self._respond(411, {"error": "CONTENT_LENGTH_REQUIRED", "message": "Content-Length is required"})
            return
        try:
            content_length = int(length)
            if content_length < 0:
                raise ValueError("negative Content-Length")
            raw = self.rfile.read(content_length)
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._respond(400, {"error": "JSON_INVALID", "message": "request body must be valid UTF-8 JSON"})
            return
        self._respond(*self.server.application.dispatch("POST", self.path, body))

    def log_message(self, format, *args):
        # Keep local output useful without logging document content.
        super().log_message(format, *args)


class USGHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, application):
        self.application = application
        self.address_family = socket.AF_INET6 if ":" in address[0] else socket.AF_INET
        super().__init__(address, _RequestHandler)


def create_server(application: USGApplication, host: str = "127.0.0.1", port: int = 8765):
    if host not in {"127.0.0.1", "::1"}:
        raise ValueError("USG local API may bind only to 127.0.0.1 or ::1")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer from 0 through 65535")
    server = USGHTTPServer((host, port), application)
    if not ip_is_loopback(server.server_address[0]):
        server.server_close()
        raise ValueError("resolved server address is not loopback")
    return server


def ip_is_loopback(value: str) -> bool:
    import ipaddress
    return ipaddress.ip_address(value).is_loopback
