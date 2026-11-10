"""Conservative USG-SEM assertion/evidence projections from interpreted spans."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .source import SourceSnapshot
from .compose import SemanticComposition


ASSERTION_EVIDENCE_ADAPTER_VERSION = "assertion-evidence-adapter/0.1.0"


@dataclass(frozen=True)
class AssertionEvidenceProjection:
    assertions: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    adapter_version: str = ASSERTION_EVIDENCE_ADAPTER_VERSION


def project_assertions_and_evidence(
    source: SourceSnapshot,
    composition: SemanticComposition,
) -> AssertionEvidenceProjection:
    """Create discovery-stage records without asserting author commitment or truth.

    Evidence quote alignment is EXACT when sliced directly from the preserved
    source. Semantic support remains NOT_ESTABLISHED. The assertion lifecycle
    remains DISCOVERED with UNKNOWN epistemic status and NONE commitment.
    """
    if not isinstance(source, SourceSnapshot):
        raise TypeError("source must be a SourceSnapshot")
    if composition.status != "COMPOSED" or len(composition.candidates) != 1:
        return AssertionEvidenceProjection((), ())
    candidate = composition.candidates[0]
    if candidate.status != "RESOLVED" or not candidate.root_ref:
        return AssertionEvidenceProjection((), ())
    root = next((x for x in candidate.nodes if x.node_id == candidate.root_ref), None)
    if root is None or root.source_span[1] > len(source.text):
        return AssertionEvidenceProjection((), ())
    start, end = root.source_span
    if start < 0 or end <= start:
        return AssertionEvidenceProjection((), ())
    quote = source.text[start:end]
    evidence_id = "evidence:" + root.node_id
    assertion_id = "assertion:" + root.node_id
    evidence = {
        "id": evidence_id,
        "sourceRef": source.source_id,
        "span": {
            "start": start,
            "end": end,
            "offsetUnit": "unicode_code_point",
        },
        "quote": quote,
        "alignmentStatus": "EXACT",
        "semanticSupportStatus": "NOT_ESTABLISHED",
        "supportingRuleRefs": [],
    }
    assertion = {
        "id": assertion_id,
        "expressionRef": root.node_id,
        "origin": "SOURCE_TEXT",
        "epistemicStatus": "UNKNOWN",
        "commitment": "NONE",
        "evaluationContext": {"kind": "UNKNOWN"},
        "lifecycleStage": "DISCOVERED",
        "sourceRef": source.source_id,
        "evidenceRefs": [evidence_id],
    }
    return AssertionEvidenceProjection((assertion,), (evidence,))


__all__ = ["ASSERTION_EVIDENCE_ADAPTER_VERSION", "AssertionEvidenceProjection",
           "project_assertions_and_evidence"]
