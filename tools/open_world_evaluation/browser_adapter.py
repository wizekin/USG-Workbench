"""Playwright adapter for the registered JavaScript Semantic Workbench target.

The browser is local and headless. No Ollama model is configured or required;
the workbench's deterministic local rule fallback is the target under test.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = ROOT / "implementations" / "semantic-workbench-js" / "v0.5.4"
ADAPTER_ID = "playwright-js-semantic-workbench"
ADAPTER_VERSION = "0.1.0"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_claim(claim: dict[str, Any]) -> dict[str, Any]:
    def entity(value):
        if not isinstance(value, dict):
            return None
        return {
            key: value.get(key)
            for key in ("text", "surfaceText", "type", "reference")
            if value.get(key) is not None
        }

    conditions = []
    for condition in claim.get("conditions", []) or []:
        if not isinstance(condition, dict):
            continue
        proposition = condition.get("proposition") or {}
        conditions.append({
            "marker": condition.get("marker"),
            "scope": condition.get("scope"),
            "effect": condition.get("effect"),
            "proposition": {
                "subject": entity(proposition.get("subject")),
                "predicate": proposition.get("predicate"),
                "object": entity(proposition.get("object")),
                "polarity": proposition.get("polarity"),
                "tense": proposition.get("tense"),
                "modality": proposition.get("modality"),
            },
            "consequence": condition.get("consequence"),
            "evidence_text": condition.get("evidenceText"),
        })
    result = {
        "subject": entity(claim.get("subject")),
        "predicate": claim.get("predicate"),
        "object": entity(claim.get("object")),
        "polarity": claim.get("polarity"),
        "tense": claim.get("tense"),
        "modality": claim.get("modality"),
        "modal_scope": claim.get("modalScope"),
        "time": claim.get("time"),
        "quantifier_scope": claim.get("quantifierScope"),
        "comparison_frame": claim.get("comparisonFrame"),
        "event_attributes": claim.get("eventAttributes", []),
        "conditions": conditions,
        "completeness": claim.get("completeness"),
        "evidence": {
            key: (claim.get("evidence") or {}).get(key)
            for key in ("quote", "start", "end", "verified")
            if (claim.get("evidence") or {}).get(key) is not None
        },
        "provenance": claim.get("provenance"),
        "source_kind": claim.get("sourceKind"),
        "rule_id": claim.get("ruleId"),
        "confidence": claim.get("confidence"),
        "note": claim.get("note"),
    }
    return result


def stable_workbench_projection(record: dict[str, Any], source_text: str) -> dict[str, Any]:
    claims = record.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("Workbench output claims must be an array")
    stable_claims = [
        _stable_claim(item) for item in claims if isinstance(item, dict)
    ]
    unresolved = record.get("unresolved", [])
    if not isinstance(unresolved, list):
        raise ValueError("Workbench unresolved output must be an array")
    return {
        "pipeline_contract": "USG-WB-SEM/1.0",
        "pipeline_version": "0.5.4",
        "source": {
            "text": source_text,
            "sha256": _sha256(source_text),
            "language": "en",
        },
        "engine": record.get("engine"),
        "intent": record.get("intent"),
        "interpretation": record.get("interpretation"),
        "claims": stable_claims,
        "unresolved": [str(item) for item in unresolved],
        "warnings": [str(item) for item in record.get("warnings", [])],
        "claim_count": len(stable_claims),
        "unresolved_count": len(unresolved),
        "semantic_validation": {
            "status": (record.get("semanticValidation") or {}).get("status"),
            "valid": (record.get("semanticValidation") or {}).get("valid"),
        },
    }


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def interpret_in_browser(case: dict[str, Any]) -> dict[str, Any]:
    """Launch a fresh local Workbench server and browser for one English case."""
    text = case["input"]["text"]
    language = case["input"].get("language_hint", "en")
    if language != "en":
        return {
            "outcome": "unsupported",
            "reason": "JavaScript Semantic Workbench v0.5.4 exposes an English-only interpreter UI.",
            "execution_metadata": {"adapter": ADAPTER_ID, "version": ADAPTER_VERSION},
        }
    if len(text) > 12_000:
        return {
            "outcome": "unsupported",
            "reason": "Workbench v0.5.4 limits interpretation input to 12,000 characters.",
            "execution_metadata": {"adapter": ADAPTER_ID, "version": ADAPTER_VERSION},
        }

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for the JS Workbench browser target; install the browser adapter dependencies."
        ) from exc

    port = _free_loopback_port()
    env = dict(os.environ)
    env["USG_PORT"] = str(port)
    server = subprocess.Popen(
        ["node", "server.js"],
        cwd=WORKBENCH,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    browser = None
    console_messages: list[str] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.on("console", lambda message: console_messages.append(
                message.text[:500] if message.type == "error" else ""
            ) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)[:1000]))
            response = page.goto(
                f"http://127.0.0.1:{port}/",
                wait_until="domcontentloaded",
                timeout=15_000,
            )
            if response is None or not response.ok:
                raise RuntimeError(
                    f"Workbench browser navigation failed: HTTP {response.status if response else 'no response'}"
                )
            page.locator('button[data-view="interpret"]').click(timeout=5_000)
            page.locator("#source-text").fill(text)
            page.locator("#analyze-button").click(timeout=5_000)
            page.locator("#interpret-results").wait_for(state="visible", timeout=15_000)
            page.locator('button[data-result-tab="raw"]').click(timeout=5_000)
            raw = page.locator("#raw-json").text_content(timeout=5_000) or ""
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Workbench returned invalid interpretation JSON: {exc}") from exc
            stable = stable_workbench_projection(record, text)
            if stable["claim_count"] and not stable["unresolved_count"]:
                outcome = "completed"
            elif stable["claim_count"] or stable["unresolved_count"]:
                outcome = "partial"
            else:
                outcome = "unsupported"
            return {
                "outcome": outcome,
                "target_result": stable,
                "execution_metadata": {
                    "adapter": ADAPTER_ID,
                    "adapter_version": ADAPTER_VERSION,
                    "browser": "chromium",
                    "browser_version": browser.version,
                    "workbench_version": "0.5.4",
                    "ui_status": page.locator("#result-status").inner_text(),
                    "page_errors": page_errors,
                    "console_error_count": len([item for item in console_messages if item]),
                    "ollama_used": False,
                    "interpretation_source": "local_rule_fallback",
                },
            }
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
