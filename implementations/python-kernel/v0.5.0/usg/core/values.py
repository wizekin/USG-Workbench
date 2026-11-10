"""Enumerations and transition rules for the five orthogonal status axes
(spec Part 1 §1.7.3) plus the components allowed to change them.

Axis A  Interpretation outcome     RESOLVED / AMBIGUOUS / UNRESOLVED
Axis B  Validation result          per check, aggregated
Axis C  Lifecycle stage            DISCOVERED -> ... -> PROMOTED
Axis D  Epistemic status           SOURCE_ASSERTED / INFERRED / VERIFIED / ...
Axis E  Evidence vector            (Part 5/6 modules) with derived E-label

These axes MUST NOT be merged. Transition functions raise InvariantViolation
with the rule code that forbids the change.

NOTE (no-human implementation): the specification's *human* reviewer is
replaced by the component ``AUTOMATED_PANEL`` (see usg.autonomy.policy).
"""

from __future__ import annotations

from enum import Enum, IntEnum

from ..errors import InvariantViolation


# ---------------------------------------------------------------------------
# Components: who is allowed to cause what. A model is never a decider.
# ---------------------------------------------------------------------------
class Component(str, Enum):
    INTERPRETER = "INTERPRETER"
    LEARNING_ENGINE = "LEARNING_ENGINE"
    GENERALIZATION_ENGINE = "GENERALIZATION_ENGINE"
    PROPOSAL_SERVICE = "PROPOSAL_SERVICE"  # turns big-model output into candidates
    CANDIDATE_STORE = "CANDIDATE_STORE"
    VALIDATOR = "VALIDATOR"
    RULE_ENGINE = "RULE_ENGINE"
    AUTOMATED_PANEL = "AUTOMATED_PANEL"  # replaces the human reviewer
    EVALUATION_PROCESS = "EVALUATION_PROCESS"
    PROMOTION_CONTROLLER = "PROMOTION_CONTROLLER"
    REGISTRY = "REGISTRY"
    CONTROLLER = "CONTROLLER"
    MODEL_GATEWAY = "MODEL_GATEWAY"  # local model: logging only, never a decider
    BIG_MODEL_GATEWAY = "BIG_MODEL_GATEWAY"  # remote model: logging only
    SYSTEM = "SYSTEM"
    RELEASE = "RELEASE"  # install-time / sealed


PROPOSERS = frozenset(
    {
        Component.INTERPRETER,
        Component.LEARNING_ENGINE,
        Component.GENERALIZATION_ENGINE,
        Component.PROPOSAL_SERVICE,
        Component.RULE_ENGINE,
    }
)


# ---------------------------------------------------------------------------
# Simple enumerations
# ---------------------------------------------------------------------------
class ValueState(str, Enum):
    SPECIFIED = "SPECIFIED"
    UNSPECIFIED = "UNSPECIFIED"  # source does not express it; never invented
    UNKNOWN = "UNKNOWN"  # source states it is unknown
    NOT_APPLICABLE = "NOT_APPLICABLE"
    WITHHELD = "WITHHELD"


class Basis(str, Enum):
    EXPLICIT = "EXPLICIT"
    GRAMMATICAL = "GRAMMATICAL"
    BACKGROUND = "BACKGROUND"


class Outcome(str, Enum):  # Axis A
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


class CheckResult(str, Enum):  # Axis B (per check)
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_CHECKED = "NOT_CHECKED"


class Aggregate(str, Enum):  # Axis B (aggregated)
    INVALID = "INVALID"
    UNCERTAIN = "UNCERTAIN"
    FORMALLY_VALID = "FORMALLY_VALID"


class Origin(str, Enum):
    SOURCE_TEXT = "SOURCE_TEXT"
    GRAMMATICAL = "GRAMMATICAL"
    BACKGROUND_INFERENCE = "BACKGROUND_INFERENCE"
    IMPORTED_RESOURCE = "IMPORTED_RESOURCE"
    CURATED = "CURATED"  # shipped in the sealed Foundation Package at install time


AUTHORIZED_ORIGINS = frozenset({Origin.IMPORTED_RESOURCE, Origin.CURATED})


class CommitmentKind(str, Enum):
    AUTHOR = "AUTHOR"
    ATTRIBUTED = "ATTRIBUTED"
    NONE = "NONE"


class EvalContextKind(str, Enum):
    WORLD = "WORLD"
    FICTION = "FICTION"
    HYPOTHETICAL = "HYPOTHETICAL"
    HISTORICAL_BELIEF = "HISTORICAL_BELIEF"
    DOMAIN_MODEL = "DOMAIN_MODEL"


class RiskClass(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

    def raised(self, steps: int = 1) -> "RiskClass":
        return RiskClass(min(int(RiskClass.VERY_HIGH), int(self) + steps))


class TrustTier(str, Enum):
    QUARANTINE = "QUARANTINE"
    STANDARD = "STANDARD"
    TRUSTED = "TRUSTED"


class SourceType(str, Enum):
    DOCUMENT = "DOCUMENT"
    SENTENCE = "SENTENCE"
    RESOURCE = "RESOURCE"
    CURATED = "CURATED"
    USER_INPUT = "USER_INPUT"


class Sensitivity(str, Enum):
    PUBLIC = "PUBLIC"  # only label that may ever be sent to a remote model
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"


class Number(str, Enum):
    SINGULAR = "SINGULAR"
    PLURAL = "PLURAL"
    MASS = "MASS"
    UNSPECIFIED = "UNSPECIFIED"


class Genericity(str, Enum):
    SPECIFIC = "SPECIFIC"
    GENERIC = "GENERIC"


class ReferentScope(str, Enum):
    DISCOURSE_LOCAL = "DISCOURSE_LOCAL"
    RESOLVED_INDIVIDUAL = "RESOLVED_INDIVIDUAL"


class IntroducedInKind(str, Enum):
    WORLD = "WORLD"
    CONTENT_OF = "CONTENT_OF"
    NEGATED = "NEGATED"
    CONDITIONAL = "CONDITIONAL"
    HYPOTHETICAL = "HYPOTHETICAL"


class FillerKind(str, Enum):
    """What may fill a role (SG-CON-003). A bare concept id is NOT a filler kind."""

    REFERENT = "REFERENT"
    INSTANCE = "INSTANCE"  # nested frame-instance description
    EXPR = "EXPR"  # nested expression node (proposition etc.)
    LITERAL = "LITERAL"
    TIME = "TIME"
    KIND_REF = "KIND_REF"  # KIND(concept) for generic statements


class EvidenceLabel(IntEnum):
    """Derived workflow label (Part 6 §6.4.2). Not a probability, not a total order of reliability."""

    E0_UNSUPPORTED = 0
    E1_HYPOTHESIS = 1
    E2_SOURCE_SUPPORTED = 2
    E3_CORROBORATED = 3
    E4_DERIVED = 4
    E5_CURATED = 5


# ---------------------------------------------------------------------------
# Axis C: lifecycle
# ---------------------------------------------------------------------------
class Lifecycle(str, Enum):
    DISCOVERED = "DISCOVERED"
    STRUCTURED = "STRUCTURED"
    VALIDATED_FORMALLY = "VALIDATED_FORMALLY"
    REVIEWED_SEMANTICALLY = "REVIEWED_SEMANTICALLY"  # by the AUTOMATED_PANEL
    CORROBORATED = "CORROBORATED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    DEPRECATED = "DEPRECATED"


_CHAIN = [
    Lifecycle.DISCOVERED,
    Lifecycle.STRUCTURED,
    Lifecycle.VALIDATED_FORMALLY,
    Lifecycle.REVIEWED_SEMANTICALLY,
    Lifecycle.CORROBORATED,
    Lifecycle.PROMOTED,
]
_ORDER = {s: i for i, s in enumerate(_CHAIN)}

_STAGE_OWNER: dict[Lifecycle, frozenset[Component]] = {
    Lifecycle.DISCOVERED: PROPOSERS | {Component.CANDIDATE_STORE},
    Lifecycle.STRUCTURED: frozenset({Component.CANDIDATE_STORE}),
    Lifecycle.VALIDATED_FORMALLY: frozenset({Component.VALIDATOR}),
    Lifecycle.REVIEWED_SEMANTICALLY: frozenset({Component.AUTOMATED_PANEL}),
    Lifecycle.CORROBORATED: frozenset({Component.EVALUATION_PROCESS}),
    Lifecycle.PROMOTED: frozenset({Component.PROMOTION_CONTROLLER}),
    Lifecycle.REJECTED: frozenset(
        {
            Component.VALIDATOR,
            Component.AUTOMATED_PANEL,
            Component.PROMOTION_CONTROLLER,
            Component.CONTROLLER,
            Component.EVALUATION_PROCESS,
            Component.REGISTRY,
        }
    ),
    Lifecycle.DEFERRED: frozenset(
        {Component.CONTROLLER, Component.PROMOTION_CONTROLLER, Component.AUTOMATED_PANEL, Component.VALIDATOR}
    ),
    Lifecycle.DEPRECATED: frozenset({Component.PROMOTION_CONTROLLER, Component.REGISTRY}),
}


def check_lifecycle_transition(frm: Lifecycle | None, to: Lifecycle, actor: Component) -> None:
    """Enforce SG-LRN-002 / SG-FND-004: stages are owned by components; no
    engine can advance a candidate beyond STRUCTURED; nothing moves backwards;
    PROMOTED can only be reached by the PROMOTION_CONTROLLER."""

    if actor not in _STAGE_OWNER[to]:
        raise InvariantViolation(f"{actor.value} may not set lifecycle stage {to.value}", "SG-LRN-002")
    if frm is None:
        if to is not Lifecycle.DISCOVERED:
            raise InvariantViolation("a new record must start at DISCOVERED", "SG-LRN-002")
        return
    if frm in (Lifecycle.REJECTED, Lifecycle.DEPRECATED):
        raise InvariantViolation(f"{frm.value} is terminal", "SG-LRN-002")
    if frm is Lifecycle.PROMOTED:
        if to is not Lifecycle.DEPRECATED:
            raise InvariantViolation("PROMOTED may only move to DEPRECATED", "SG-LRN-002")
        return
    if frm is Lifecycle.DEFERRED:
        if to in (Lifecycle.DISCOVERED, Lifecycle.STRUCTURED, Lifecycle.REJECTED):
            return
        raise InvariantViolation("DEFERRED may only re-enter at DISCOVERED/STRUCTURED or be REJECTED", "SG-LRN-002")
    if to in (Lifecycle.REJECTED, Lifecycle.DEFERRED):
        return
    if to is Lifecycle.DEPRECATED:
        raise InvariantViolation("only PROMOTED records can be DEPRECATED", "SG-LRN-002")
    if _ORDER[to] <= _ORDER[frm]:
        raise InvariantViolation(f"lifecycle cannot move {frm.value} -> {to.value}", "SG-LRN-002")


# ---------------------------------------------------------------------------
# Axis D: epistemic status (Part 6 §6.3)
# ---------------------------------------------------------------------------
class EpistemicStatus(str, Enum):
    SOURCE_ASSERTED = "SOURCE_ASSERTED"
    INFERRED = "INFERRED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class DisputeKind(str, Enum):
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"
    CONTRADICTED_BY_AUTHORITY = "CONTRADICTED_BY_AUTHORITY"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    POPULATION_DEPENDENT = "POPULATION_DEPENDENT"
    DEFINITION_DEPENDENT = "DEFINITION_DEPENDENT"
    INCOMPLETE_EVIDENCE = "INCOMPLETE_EVIDENCE"
    PARSING_SUSPECT = "PARSING_SUSPECT"


_E = EpistemicStatus
_EP_ALLOWED: dict[tuple[EpistemicStatus | None, EpistemicStatus], frozenset[Component]] = {
    (None, _E.SOURCE_ASSERTED): frozenset({Component.VALIDATOR}),
    (None, _E.INFERRED): frozenset({Component.RULE_ENGINE}),
    (_E.SOURCE_ASSERTED, _E.VERIFIED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.SOURCE_ASSERTED, _E.DISPUTED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.SOURCE_ASSERTED, _E.UNKNOWN): frozenset({Component.EVALUATION_PROCESS}),
    (_E.INFERRED, _E.VERIFIED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.INFERRED, _E.DISPUTED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.DISPUTED, _E.VERIFIED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.DISPUTED, _E.UNKNOWN): frozenset({Component.EVALUATION_PROCESS}),
    (_E.VERIFIED, _E.DISPUTED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.UNKNOWN, _E.VERIFIED): frozenset({Component.EVALUATION_PROCESS}),
    (_E.UNKNOWN, _E.DISPUTED): frozenset({Component.EVALUATION_PROCESS}),
}


def check_epistemic_transition(frm: EpistemicStatus | None, to: EpistemicStatus, actor: Component) -> None:
    """SG-EVD-003 / SG-EVD-009. INFERRED never becomes SOURCE_ASSERTED; nothing
    reaches VERIFIED except through the EVALUATION_PROCESS (never because it
    was extracted, learned, repeated, retrieved or promoted)."""

    if frm is _E.INFERRED and to is _E.SOURCE_ASSERTED:
        raise InvariantViolation("an inference is never relabelled as source-stated", "SG-EVD-003")
    if to is _E.VERIFIED and actor is not Component.EVALUATION_PROCESS:
        raise InvariantViolation(f"{actor.value} may not mark a claim VERIFIED", "SG-EVD-009")
    allowed = _EP_ALLOWED.get((frm, to))
    if allowed is None:
        raise InvariantViolation(f"epistemic transition {frm} -> {to.value} is not allowed", "SG-EVD-003")
    if actor not in allowed:
        raise InvariantViolation(f"{actor.value} may not cause {frm} -> {to.value}", "SG-EVD-009")


def eligible_for_trusted_view(
    status: EpistemicStatus, commitment: CommitmentKind, context: EvalContextKind
) -> bool:
    """SG-EVD-007: only VERIFIED claims the author commits to, in the actual
    world (or a declared domain model), enter the trusted knowledge view."""

    return (
        status is EpistemicStatus.VERIFIED
        and commitment is CommitmentKind.AUTHOR
        and context in (EvalContextKind.WORLD, EvalContextKind.DOMAIN_MODEL)
    )
