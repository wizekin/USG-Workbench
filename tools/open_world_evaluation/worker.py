"""One-case worker for the USG Open-World Evaluation Program.

Scenario text is passed as JSON data over stdin. It is never evaluated as code.
"""

from __future__ import annotations

import json
import importlib
import math
import os
import socket
import sys
from typing import Any

MAX_OUTPUT_BYTES = 4_000_000


def _apply_resource_limits(case: dict[str, Any]) -> None:
    limits = case["resource_limits"]
    try:
        import resource
    except ImportError:
        return

    wall_seconds = max(1, int(math.ceil(float(limits["wall_time_seconds"]))))
    memory_bytes = int(limits["memory_megabytes"]) * 1024 * 1024

    browser_target = case.get("target", {}).get("interface") == "browser_ui"
    file_limit = 256 if browser_target else 64
    for name, value in (
        ("RLIMIT_CPU", (wall_seconds, wall_seconds + 1)),
        ("RLIMIT_FSIZE", (8 * 1024 * 1024, 8 * 1024 * 1024)),
        ("RLIMIT_NOFILE", (file_limit, file_limit)),
        ("RLIMIT_AS", (memory_bytes, memory_bytes)),
    ):
        limit_id = getattr(resource, name, None)
        if limit_id is None:
            continue
        try:
            resource.setrlimit(limit_id, value)
        except (OSError, ValueError):
            # Parent-side wall-clock timeout remains authoritative.
            pass


def _disable_network() -> None:
    """Best-effort Python socket denial; not a kernel network namespace."""
    def denied(*_args: Any, **_kwargs: Any) -> Any:
        raise OSError("network access is disabled for OW scenario execution")

    socket.create_connection = denied
    socket.socket.connect = denied
    socket.socket.connect_ex = denied


def _phase5_resource_digest() -> str:
    """Compute the same catalogue digest used by the local Phase 5 API."""
    import sqlite3
    from tools.usg_interpretation_v0_2_0 import (
        SQLiteResourceCatalogue,
        bundled_resource_descriptors,
    )

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("BEGIN")
        catalogue = SQLiteResourceCatalogue(connection)
        for descriptor in bundled_resource_descriptors():
            catalogue.register_resource(descriptor, registered_at=0.0)
        return catalogue.digest()
    finally:
        connection.rollback()
        connection.close()


def _completion_outcome(result: dict[str, Any]) -> str:
    status = str(result.get("completion_status", "")).upper()
    if status in {"COMPLETE", "COMPLETED"}:
        return "completed"
    if status == "UNSUPPORTED":
        return "unsupported"
    if status == "AMBIGUOUS":
        return "ambiguous"
    if status in {"PARTIAL", "INCOMPLETE", "INCOMPLETE_RESOURCE_LIMIT"}:
        return "partial"
    if status in {"INVALID_INPUT", "INVALID_OUTPUT"}:
        return "invalid_output"
    return "invalid_output"


def _run_import_smoke(target_id: str) -> dict[str, Any] | None:
    """Import allowlisted package entry points; this is an API-availability smoke test only."""
    registry_path = os.path.join(os.path.dirname(__file__), "target_profiles.json")
    with open(registry_path, "r", encoding="utf-8") as stream:
        registry = json.load(stream)
    profile = next(
        (item for item in registry.get("targets", []) if item.get("component_id") == target_id),
        None,
    )
    if profile is None or "smoke_modules" not in profile:
        return None
    modules = profile["smoke_modules"]
    if not modules:
        return {
            "outcome": "not_executed",
            "reason": "profile has no executable Python import adapter; interface requires a dedicated runtime adapter",
            "execution_metadata": {"adapter": "not-implemented"},
        }
    imported = []
    repository_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    for relative_path, module_name in modules:
        package_root = os.path.realpath(os.path.join(repository_root, relative_path))
        if os.path.commonpath([repository_root, package_root]) != repository_root:
            raise ValueError("smoke adapter path escapes repository root")
        if package_root not in sys.path:
            sys.path.insert(0, package_root)
        importlib.import_module(module_name)
        imported.append(module_name)
    return {
        "outcome": "partial",
        "reason": "all registered modules imported; this smoke test does not execute semantic behavior or establish correctness",
        "target_result": {"imported_modules": imported},
        "execution_metadata": {
            "adapter": "allowlisted-python-import-smoke",
            "smoke_only": True,
            "semantic_accuracy_assessed": False,
        },
    }


def execute(case: dict[str, Any]) -> dict[str, Any]:
    target_id = case["target"]["component_id"]
    text = case["input"]["text"]
    language_hint = case["input"].get("language_hint", "en")

    # Both accepted interpreter APIs currently expose only en/ar language
    # profiles. Mixed/other hints are mapped explicitly and recorded.
    if language_hint in {"en", "ar"}:
        language = language_hint
        language_mapping = "exact"
    elif language_hint == "en-ar":
        language = "en"
        language_mapping = "mixed_hint_mapped_to_en_profile"
    elif language_hint == "ar-en":
        language = "ar"
        language_mapping = "mixed_hint_mapped_to_ar_profile"
    else:
        language = "en"
        language_mapping = "unknown_hint_mapped_to_en_profile"

    if target_id not in {"phase4-bounded-interpreter", "phase5-bounded-interpreter", "js-semantic-workbench-v054"}:
        smoke_result = _run_import_smoke(target_id)
        if smoke_result is not None:
            return smoke_result

    if target_id == "phase4-bounded-interpreter":
        from tools.usg_interpretation_v0_1_0 import InterpretationService

        service = InterpretationService()
        result = service.interpret(text, language)
        return {
            "outcome": _completion_outcome(result),
            "target_result": result,
            "execution_metadata": {
                "language_requested": language_hint,
                "language_used": language,
                "language_mapping": language_mapping,
                "adapter": "phase4-python-api",
            },
        }

    if target_id == "phase5-bounded-interpreter":
        from tools.usg_interpretation_v0_2_0 import Phase5InterpretationService

        manifest_digest = _phase5_resource_digest()
        service = Phase5InterpretationService()
        result = service.interpret(
            text,
            language,
            resource_manifest_digest=manifest_digest,
        )
        return {
            "outcome": _completion_outcome(result),
            "target_result": result,
            "execution_metadata": {
                "language_requested": language_hint,
                "language_used": language,
                "language_mapping": language_mapping,
                "adapter": "phase5-python-api",
                "resource_manifest_digest": manifest_digest,
            },
        }

    if target_id == "js-semantic-workbench-v054":
        from tools.open_world_evaluation.browser_adapter import interpret_in_browser
        return interpret_in_browser(case)

    return {
        "outcome": "not_executed",
        "reason": f"no allowlisted OW-3 adapter for target {target_id!r}",
        "execution_metadata": {"adapter": "none"},
    }


def main() -> int:
    raw = sys.stdin.buffer.read(1_000_001)
    if len(raw) > 1_000_000:
        print(json.dumps({
            "outcome": "invalid_output",
            "reason": "worker input exceeded the 1 MB transport ceiling",
        }))
        return 0
    try:
        case = json.loads(raw.decode("utf-8"))
        _apply_resource_limits(case)
        if case.get("resource_limits", {}).get("network_access") is not False:
            raise ValueError("OW-3 worker refuses scenarios with network access enabled")
        _disable_network()
        payload = execute(case)
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_OUTPUT_BYTES:
            payload = {
                "outcome": "invalid_output",
                "reason": "target output exceeded the 4 MB worker output ceiling",
            }
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        sys.stdout.buffer.write(encoded + b"\n")
        return 0
    except Exception as exc:
        print(f"OW worker error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
