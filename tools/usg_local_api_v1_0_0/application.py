"""Loopback-only HTTP API for the USG local semantic workbench."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from hashlib import sha256
import json
from pathlib import Path
import socket
import sqlite3
from time import time
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
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.usg_interpretation_v0_1_0.resources import SemanticAssociation
from tools.phase6_broader_semantics_v0_1.engine import compose as compose_phase6_candidate, project_loss_aware as project_phase6_loss_aware, CompositionError
from tools.phase6_broader_semantics_v0_1.extract import extract_candidate_graph
from tools.phase6_broader_semantics_v0_1.runs import SQLitePhase6CandidateRunStore
from tools.usg_interpretation_v0_2_0 import (
    Phase5InterpretationService, SQLiteResourceCatalogue,
    SQLiteInterpretationRunStore, bundled_resource_descriptors,
    canonical_result_bytes,
)

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
        self.phase5_interpretation_service = Phase5InterpretationService()
        with self.store.resource_catalogue_session(
            role=RESOURCE_CATALOGUE_ROLE, write=True
        ) as connection:
            self.resource_catalogue = SQLiteResourceCatalogue(connection)
            self.interpretation_run_store = SQLiteInterpretationRunStore(connection)
            for descriptor in bundled_resource_descriptors():
                existing = self.resource_catalogue.get_resource(descriptor.resource_id)
                if existing is None:
                    self.resource_catalogue.register_resource(descriptor, time())
                elif existing != descriptor:
                    raise RuntimeError(
                        "bundled resource changed under an existing ID; register a new resource ID/version: "
                        + descriptor.resource_id
                    )
            self.phase6_candidate_run_store = SQLitePhase6CandidateRunStore(connection)

    def _catalogue_read(self, operation):
        with self.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE):
            return operation()

    def _catalogue_write(self, operation):
        with self.store.resource_catalogue_session(
            role=RESOURCE_CATALOGUE_ROLE, write=True
        ):
            return operation()

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
                    "phase5_pipeline": "USG-INTERPRET/0.2.0",
                    "phase6_candidate_pipeline": "USG-INTERPRET/0.3.0",
                    "phase6_candidate_capabilities": "CANDIDATE_ONLY",
                    "resource_catalogue": "sqlite-semantic-resource-catalogue/0.1.0",
                }

            if method == "GET" and path == "/v2/resources":
                manifest, digest = self._catalogue_read(
                    lambda: (self.resource_catalogue.manifest(), self.resource_catalogue.digest())
                )
                return 200, {
                    "catalogue_contract": manifest["contract"],
                    "catalogue_version": manifest["version"],
                    "resource_manifest_digest": digest,
                    "manifest": manifest,
                }

            if method == "GET" and path == "/v2/associations":
                source_ref = query.get("source_ref", [None])[0]
                if not source_ref:
                    raise APIRequestError(400, "SOURCE_REF_REQUIRED", "source_ref query parameter is required")
                try:
                    active_limit = int(query.get("active_limit", ["10"])[0])
                    secondary_limit = int(query.get("secondary_limit", ["20"])[0])
                    half_life = float(query.get("half_life_seconds", [str(30 * 24 * 3600)])[0])
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "ASSOCIATION_LIMIT_INVALID", "association limits and half_life_seconds must be numeric") from exc
                results = self._catalogue_read(lambda: self.resource_catalogue.retrieve_associations(
                    source_ref, now=time(), active_limit=active_limit,
                    secondary_limit=secondary_limit, half_life_seconds=half_life,
                ))
                return 200, {
                    "source_ref": source_ref,
                    "count": len(results),
                    "associations": [{
                        "association": {
                            "association_id": item.association.association_id,
                            "source_ref": item.association.source_ref,
                            "target_ref": item.association.target_ref,
                            "relation": item.association.relation,
                            "association_kind": item.association.association_kind,
                            "weight": item.association.weight,
                            "observation_count": item.association.observation_count,
                            "provenance": item.association.provenance,
                            "status": item.association.status,
                        },
                        "activation_score": item.activation_score,
                        "tier": item.tier,
                        "total_observations": item.total_observations,
                        "last_used_at": item.last_used_at,
                        "identity_resolution": False,
                    } for item in results],
                }

            if method == "POST" and path == "/v3/phase6/extract":
                if not isinstance(body, dict) or not isinstance(body.get("source"), str) or not isinstance(body.get("language"), str):
                    raise APIRequestError(400, "PHASE6_EXTRACT_REQUEST_INVALID", "body requires source and language strings")
                persist = body.get("persist", True)
                if not isinstance(persist, bool):
                    raise APIRequestError(400, "PHASE6_EXTRACT_REQUEST_INVALID", "persist must be a boolean")
                try:
                    extraction = extract_candidate_graph(body["source"], body["language"])
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "PHASE6_EXTRACT_INVALID", str(exc)) from exc
                response = {"extraction": extraction, "capability_state": "CANDIDATE_ONLY"}
                if extraction["status"] == "CANDIDATE_PATTERN_MATCH":
                    try:
                        composition = compose_phase6_candidate(body["source"], body["language"], extraction["graph"])
                        projection = project_phase6_loss_aware(composition)
                    except (CompositionError, TypeError, ValueError) as exc:
                        raise APIRequestError(400, "PHASE6_EXTRACT_COMPOSITION_INVALID", str(exc)) from exc
                    stored_result = {"pipeline_contract": composition["pipeline_contract"], "composition": composition, "projection": projection}
                    response.update({"composition": composition, "projection": projection})
                    if persist:
                        manifest_digest = self._catalogue_read(lambda: self.resource_catalogue.digest())
                        metadata = self._catalogue_write(lambda: self.phase6_candidate_run_store.put(
                            body["source"], body["language"], extraction["graph"], stored_result, manifest_digest
                        ))
                        response["persistence"] = metadata
                return 200, response

            if method == "POST" and path == "/v3/phase6/compose":
                if not isinstance(body, dict) or not isinstance(body.get("source"), str) or not isinstance(body.get("language"), str) or not isinstance(body.get("graph"), dict):
                    raise APIRequestError(400, "PHASE6_COMPOSE_REQUEST_INVALID", "body requires source, language, and graph object")
                persist = body.get("persist", True)
                if not isinstance(persist, bool):
                    raise APIRequestError(400, "PHASE6_COMPOSE_REQUEST_INVALID", "persist must be a boolean")
                try:
                    composition = compose_phase6_candidate(body["source"], body["language"], body["graph"])
                    projection = project_phase6_loss_aware(composition)
                except (CompositionError, TypeError, ValueError) as exc:
                    raise APIRequestError(400, "PHASE6_COMPOSE_INVALID", str(exc)) from exc
                result = {"pipeline_contract": composition["pipeline_contract"], "composition": composition, "projection": projection}
                if persist:
                    manifest_digest = self._catalogue_read(lambda: self.resource_catalogue.digest())
                    metadata = self._catalogue_write(lambda: self.phase6_candidate_run_store.put(
                        body["source"], body["language"], body["graph"], result, manifest_digest
                    ))
                    result = {**result, "persistence": metadata}
                return 200, result

            if method == "GET" and path == "/v3/phase6/runs":
                try:
                    limit = int(query.get("limit", ["50"])[0])
                    runs = self._catalogue_read(lambda: self.phase6_candidate_run_store.list(limit))
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "PHASE6_RUN_LIMIT_INVALID", str(exc)) from exc
                return 200, {"count": len(runs), "runs": list(runs)}

            phase6_parts = [unquote(part) for part in path.split("/") if part]
            if method == "GET" and len(phase6_parts) == 4 and phase6_parts[:3] == ["v3", "phase6", "runs"]:
                stored = self._catalogue_read(lambda: self.phase6_candidate_run_store.get(phase6_parts[3]))
                if stored is None:
                    raise APIRequestError(404, "PHASE6_RUN_NOT_FOUND", "Phase 6 candidate run was not found")
                return 200, stored

            if method == "POST" and len(phase6_parts) == 5 and phase6_parts[:3] == ["v3", "phase6", "runs"] and phase6_parts[4] == "replay":
                stored = self._catalogue_read(lambda: self.phase6_candidate_run_store.get(phase6_parts[3]))
                if stored is None:
                    raise APIRequestError(404, "PHASE6_RUN_NOT_FOUND", "Phase 6 candidate run was not found")
                inputs = stored["input"]
                try:
                    composition = compose_phase6_candidate(inputs["source"], inputs["language"], inputs["graph"])
                    projection = project_phase6_loss_aware(composition)
                except (CompositionError, TypeError, ValueError) as exc:
                    raise APIRequestError(409, "PHASE6_REPLAY_FAILED", str(exc)) from exc
                replayed = {"pipeline_contract": composition["pipeline_contract"], "composition": composition, "projection": projection}
                from tools.phase6_broader_semantics_v0_1.runs import canonical_bytes
                from hashlib import sha256 as _sha256
                replay_digest = _sha256(canonical_bytes(replayed)).hexdigest()
                return 200, {"run_id": phase6_parts[3], "stored_result_sha256": stored["result_sha256"],
                             "replayed_result_sha256": replay_digest, "deterministic_match": replay_digest == stored["result_sha256"],
                             "result": replayed}

            if method == "POST" and path == "/v2/interpret":
                if not isinstance(body, dict) or not isinstance(body.get("text"), str) or not isinstance(body.get("language"), str):
                    raise APIRequestError(400, "PHASE5_INTERPRET_REQUEST_INVALID", "body requires text and language strings")
                persist = body.get("persist", True)
                if not isinstance(persist, bool):
                    raise APIRequestError(400, "PHASE5_INTERPRET_REQUEST_INVALID", "persist must be a boolean")
                manifest_digest = self._catalogue_read(lambda: self.resource_catalogue.digest())
                try:
                    result = self.phase5_interpretation_service.interpret(
                        body["text"], body["language"],
                        resource_manifest_digest=manifest_digest,
                    )
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "PHASE5_INTERPRET_REQUEST_INVALID", str(exc)) from exc
                if persist:
                    def persist_if_manifest_unchanged():
                        current_digest = self.resource_catalogue.digest()
                        if current_digest != manifest_digest:
                            raise APIRequestError(
                                409, "RESOURCE_MANIFEST_CHANGED",
                                "resource catalogue changed while interpretation was running; retry"
                            )
                        return self.interpretation_run_store.put(result)
                    metadata = self._catalogue_write(persist_if_manifest_unchanged)
                    result = {**result, "persistence": metadata}
                return 200, result

            if method == "GET" and path == "/v2/interpretations":
                limit_raw = query.get("limit", ["50"])[0]
                try:
                    limit = int(limit_raw)
                except (TypeError, ValueError) as exc:
                    raise APIRequestError(400, "RUN_LIMIT_INVALID", "limit must be an integer") from exc
                runs = self._catalogue_read(lambda: self.interpretation_run_store.list(limit))
                return 200, {"count": len(runs), "runs": list(runs)}

            if method == "POST" and path == "/v2/associations":
                if not isinstance(body, dict):
                    raise APIRequestError(400, "ASSOCIATION_INVALID", "body must be an association object")
                try:
                    association = SemanticAssociation(
                        body["association_id"], body["source_ref"], body["target_ref"],
                        body["relation"], body.get("association_kind", "CONTEXTUAL"),
                        body["weight"], body.get("observation_count", 0),
                        body["provenance"], "PROVISIONAL",
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise APIRequestError(400, "ASSOCIATION_INVALID", str(exc)) from exc
                self._catalogue_write(
                    lambda: self.resource_catalogue.register_association(association, time())
                )
                return 201, {
                    "association_id": association.association_id,
                    "status": "PROVISIONAL",
                    "identity_resolution": False,
                }

            if method == "POST" and path.startswith("/v2/associations/") and path.endswith("/use"):
                association_id = unquote(path[len("/v2/associations/"):-len("/use")].strip("/"))
                if not association_id:
                    raise APIRequestError(400, "ASSOCIATION_ID_REQUIRED", "association ID is required")
                context_ref = body.get("context_ref") if isinstance(body, dict) else None
                self._catalogue_write(lambda: self.resource_catalogue.record_use(
                    association_id, time(), context_ref
                ))
                return 201, {"association_id": association_id, "usage_recorded": True}

            if method == "POST" and path.startswith("/v2/interpretations/") and path.endswith("/replay"):
                run_id = unquote(path[len("/v2/interpretations/"):-len("/replay")].strip("/"))
                stored = self._catalogue_read(lambda: self.interpretation_run_store.get(run_id))
                if stored is None:
                    raise APIRequestError(404, "INTERPRETATION_RUN_NOT_FOUND", "interpretation run was not found")
                previous = stored["result"]
                current_manifest = self._catalogue_read(lambda: self.resource_catalogue.digest())
                if current_manifest != previous["resource_manifest_digest"]:
                    raise APIRequestError(409, "REPLAY_RESOURCE_MISMATCH", "current resource manifest differs from the stored run")
                replayed = self.phase5_interpretation_service.interpret(
                    previous["source"]["text"], previous["source"]["language"],
                    resource_manifest_digest=current_manifest,
                )
                replay_digest = sha256(canonical_result_bytes(replayed)).hexdigest()
                if self._catalogue_read(lambda: self.resource_catalogue.digest()) != current_manifest:
                    raise APIRequestError(409, "REPLAY_RESOURCE_CHANGED", "resource catalogue changed during replay")
                return 200, {
                    "run_id": run_id,
                    "stored_result_sha256": stored["result_sha256"],
                    "replayed_result_sha256": replay_digest,
                    "deterministic_match": replay_digest == stored["result_sha256"],
                    "result": replayed,
                }

            parts_v2 = [unquote(part) for part in path.split("/") if part]
            if method == "GET" and len(parts_v2) == 3 and parts_v2[:2] == ["v2", "interpretations"]:
                run_id = parts_v2[2]
                stored = self._catalogue_read(lambda: self.interpretation_run_store.get(run_id))
                if stored is None:
                    raise APIRequestError(404, "INTERPRETATION_RUN_NOT_FOUND", "interpretation run was not found")
                return 200, stored
            if method == "GET" and len(parts_v2) == 4 and parts_v2[:2] == ["v2", "interpretations"] and parts_v2[3] == "export":
                stored = self._catalogue_read(lambda: self.interpretation_run_store.get(parts_v2[2]))
                if stored is None:
                    raise APIRequestError(404, "INTERPRETATION_RUN_NOT_FOUND", "interpretation run was not found")
                return 200, stored["result"]

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
        except (ValueError, TypeError, KeyError, sqlite3.IntegrityError) as exc:
            return 400, {"error": "REQUEST_INVALID", "message": str(exc)}
        except RuntimeError as exc:
            return 409, {"error": "RESOURCE_OR_RUN_STORE_ERROR", "message": str(exc)}


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
