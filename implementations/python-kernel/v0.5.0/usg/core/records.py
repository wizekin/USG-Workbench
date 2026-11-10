"""Core record types (spec Part 2 §2.3–§2.12) with object-level invariant
checks. Persistence is added in Part 2 of the implementation; these classes are
pure data + validation so every later module shares one definition.

Objects are frozen: state changes produce new objects through functions that
enforce the transition rules (``with_status`` / ``with_stage``).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .. import GRAMMAR_VERSION, ONTOLOGY_RELEASE
from ..errors import InvariantViolation
from ..util import sha256_hex
from .ids import IdSpace, Ref
from .kinds import SemKind, can_fill_role
from .spans import Span
from .values import (
    AUTHORIZED_ORIGINS,
    Basis,
    CommitmentKind,
    Component,
    EpistemicStatus,
    EvalContextKind,
    FillerKind,
    Genericity,
    IntroducedInKind,
    Lifecycle,
    Number,
    Origin,
    ReferentScope,
    Sensitivity,
    SourceType,
    TrustTier,
    ValueState,
    check_epistemic_transition,
    check_lifecycle_transition,
)

_LIFE_ORDER = {
    Lifecycle.DISCOVERED: 0,
    Lifecycle.STRUCTURED: 1,
    Lifecycle.VALIDATED_FORMALLY: 2,
    Lifecycle.REVIEWED_SEMANTICALLY: 3,
    Lifecycle.CORROBORATED: 4,
    Lifecycle.PROMOTED: 5,
}


def _require(cond: bool, msg: str, code: str) -> None:
    if not cond:
        raise InvariantViolation(msg, code)


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Anchor:
    """Time anchor for resolving relative expressions (E-14). Unresolved
    relative times stay unresolved when no anchor exists."""

    document_date: str | None = None  # ISO date "2026-10-16"
    time_zone: str | None = None
    calendar: str = "gregorian"
    speech_time: str | None = None

    def to_json(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class Source:
    text: str
    language: str = "en"
    type: SourceType = SourceType.SENTENCE
    trust_tier: TrustTier = TrustTier.QUARANTINE  # safe default (SG-SEC-003)
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    genre: str | None = None
    anchor: Anchor | None = None
    uri: str | None = None
    ref: Ref | None = None
    text_hash: str = ""

    def __post_init__(self):
        _require(isinstance(self.text, str) and self.text != "", "source text must be a non-empty string", "I-09")
        h = sha256_hex(self.text)
        if self.text_hash:
            _require(self.text_hash == h, "source text_hash does not match text", "I-09")
        else:
            object.__setattr__(self, "text_hash", h)
        _require(bool(self.language), "source language required", "I-01")
        if self.ref is not None:
            _require(self.ref.space is IdSpace.SOURCE, "source ref must be in SOURCE space", "I-01")

    def span_text(self, span: Span) -> str:
        return span.text_of(self.text)

    @property
    def remote_shareable(self) -> bool:
        """SG-SEC-008: only PUBLIC material may leave the machine, local-only default."""
        return self.sensitivity is Sensitivity.PUBLIC


# ---------------------------------------------------------------------------
# Concept
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Concept:
    kind: SemKind
    canonical_label: str
    definition_complete: bool = False
    lifecycle: Lifecycle = Lifecycle.DISCOVERED
    version: int = 1
    grammar_version: str = GRAMMAR_VERSION
    ontology_release: str = ONTOLOGY_RELEASE
    ref: Ref | None = None

    def __post_init__(self):
        _require(isinstance(self.kind, SemKind), "concept kind must be a SemKind", "I-01")
        _require(bool(self.canonical_label), "concept needs a label (labels are not identity)", "I-01")
        _require(self.version >= 1, "version must be >= 1", "I-12")
        if self.ref is not None:
            _require(self.ref.space in (IdSpace.CONCEPT, IdSpace.PROVISIONAL), "concept ref space", "I-01")
            if self.ref.is_provisional:
                _require(not self.definition_complete, "provisional concepts are always INCOMPLETE", "SG-IDN-006")


# ---------------------------------------------------------------------------
# Referent (discourse entity)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class IntroducedIn:
    """Context in which a referent was introduced (E-71). Existence commitment
    lives *in that context*, not in the actual world."""

    kind: IntroducedInKind = IntroducedInKind.WORLD
    ref: Ref | None = None  # instance/expr that creates the context

    def __post_init__(self):
        if self.kind is not IntroducedInKind.WORLD:
            _require(self.ref is not None, f"{self.kind.value} context needs a reference", "SG-INT-007")


@dataclass(frozen=True)
class Referent:
    kind: SemKind
    instance_of: tuple[Ref, ...] = ()
    number: Number = Number.UNSPECIFIED
    cardinality: int | tuple[int, int] | None = None
    genericity: Genericity = Genericity.SPECIFIC
    scope: ReferentScope = ReferentScope.DISCOURSE_LOCAL
    introduced_in: IntroducedIn = field(default_factory=IntroducedIn)
    individual_ids: tuple[str, ...] = ()
    source: Ref | None = None
    span: Span | None = None
    ref: Ref | None = None

    def __post_init__(self):
        _require(can_fill_role(self.kind), f"kind {self.kind.value} is a definition kind and cannot be a referent", "I-06")
        for c in self.instance_of:
            _require(c.space in (IdSpace.CONCEPT, IdSpace.PROVISIONAL), "instance_of must reference concepts", "I-06")
        if self.cardinality is not None:
            if isinstance(self.cardinality, tuple):
                lo, hi = self.cardinality
                _require(0 <= lo <= hi, "cardinality range invalid", "I-11")
            else:
                _require(isinstance(self.cardinality, int) and self.cardinality >= 0, "cardinality invalid", "I-11")
            _require(self.number is not Number.MASS, "a mass referent has no count", "I-11")
        if self.scope is ReferentScope.RESOLVED_INDIVIDUAL:
            _require(bool(self.individual_ids), "a RESOLVED_INDIVIDUAL referent needs an external id", "SG-IDN-005")
        if self.source is not None:
            _require(self.source.space is IdSpace.SOURCE, "referent source must be a SOURCE ref", "I-01")
        if self.ref is not None:
            _require(self.ref.space is IdSpace.REFERENT, "referent ref space", "I-01")


# ---------------------------------------------------------------------------
# Fillers and bindings
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Literal:
    value: Any
    value_type: str  # "Text" | "Integer" | "Decimal" | "Boolean" | ...
    unit: str | None = None

    def __post_init__(self):
        _require(self.value_type != "", "literal needs a value type", "I-11")
        _require(not isinstance(self.value, float), "canonical literals use ints/strings, not binary floats", "I-11")


_FILLER_SPACE = {
    FillerKind.REFERENT: {IdSpace.REFERENT},
    FillerKind.INSTANCE: {IdSpace.INSTANCE},
    FillerKind.EXPR: {IdSpace.NODE},
    FillerKind.KIND_REF: {IdSpace.CONCEPT, IdSpace.PROVISIONAL},
    FillerKind.TIME: {IdSpace.NODE},
}


@dataclass(frozen=True)
class Filler:
    """SG-CON-003: a filler is a referent, literal, kind-reference, nested
    description or time — never a bare concept id."""

    kind: FillerKind
    ref: Ref | None = None
    literal: Literal | None = None

    def __post_init__(self):
        if self.kind is FillerKind.LITERAL:
            _require(self.literal is not None and self.ref is None, "LITERAL filler needs a literal only", "SG-CON-003")
            return
        if self.kind is FillerKind.TIME and self.ref is None:
            _require(self.literal is not None, "TIME filler needs a node ref or literal", "SG-CON-003")
            return
        _require(self.ref is not None and self.literal is None, f"{self.kind.value} filler needs a ref", "SG-CON-003")
        _require(self.ref.space in _FILLER_SPACE[self.kind],
                 f"{self.kind.value} filler cannot reference {self.ref.space.value} (no bare concept ids)", "SG-CON-003")

    @staticmethod
    def referent(r: Ref) -> "Filler":
        return Filler(FillerKind.REFERENT, ref=r)

    @staticmethod
    def instance(r: Ref) -> "Filler":
        return Filler(FillerKind.INSTANCE, ref=r)

    @staticmethod
    def kind_ref(concept: Ref) -> "Filler":
        return Filler(FillerKind.KIND_REF, ref=concept)

    @staticmethod
    def lit(value: Any, value_type: str, unit: str | None = None) -> "Filler":
        return Filler(FillerKind.LITERAL, literal=Literal(value, value_type, unit))


@dataclass(frozen=True)
class RoleBinding:
    role: str  # name; the frame resolves it to a role_index (validated in VC-S06)
    value_state: ValueState
    basis: Basis | None = None
    filler: Filler | None = None
    span: Span | None = None
    rule: str | None = None  # interpretation / inference rule id
    ord: int = 0  # position for multi-valued roles

    def __post_init__(self):
        if self.value_state is ValueState.SPECIFIED:
            _require(self.filler is not None, f"SPECIFIED binding of {self.role} needs a filler", "VC-V06")
            _require(self.basis is not None, f"SPECIFIED binding of {self.role} needs a basis", "SG-EVD-006")
            if self.basis is Basis.EXPLICIT:
                _require(self.span is not None, "EXPLICIT basis requires a source span", "SG-EVD-006")
            else:
                _require(self.rule is not None, f"{self.basis.value} basis requires a registered rule", "SG-EVD-006")
        else:
            _require(self.filler is None and self.basis is None,
                     f"hole state {self.value_state.value} must not carry a filler or basis (no invented content)", "VC-V06")
        _require(self.ord >= 0, "binding ord must be >= 0", "I-05")


@dataclass(frozen=True)
class FrameInstance:
    """A *description* of a situation. Its existence asserts nothing; only an
    Assertion does (E-28)."""

    frame: Ref
    frame_version: int
    bindings: tuple[RoleBinding, ...]
    source: Ref | None = None
    certificate: Ref | None = None
    ref: Ref | None = None

    def __post_init__(self):
        _require(self.frame.space in (IdSpace.FRAME, IdSpace.PROVISIONAL), "frame ref space", "I-05")
        _require(self.frame_version >= 1, "frame version must be >= 1", "I-12")
        seen = set()
        for b in self.bindings:
            key = (b.role, b.ord)
            _require(key not in seen, f"duplicate binding for role {b.role} ord {b.ord}", "I-05")
            seen.add(key)

    def binding(self, role: str, ord: int = 0) -> RoleBinding | None:
        for b in self.bindings:
            if b.role == role and b.ord == ord:
                return b
        return None


# ---------------------------------------------------------------------------
# Assertion
# ---------------------------------------------------------------------------
class ContentType(str, Enum):
    INSTANCE = "INSTANCE"
    NODE = "NODE"
    EDGE = "EDGE"
    PROPERTY = "PROPERTY"


@dataclass(frozen=True)
class Assertion:
    content_type: ContentType
    content: Ref
    origin: Origin
    epistemic_status: EpistemicStatus
    commitment: CommitmentKind = CommitmentKind.AUTHOR
    attributed_to: Ref | None = None
    eval_context: EvalContextKind = EvalContextKind.WORLD
    eval_context_name: str | None = None
    definition_ref: Ref | None = None
    alt_group: int | None = None
    source: Ref | None = None
    evidence: Ref | None = None
    lifecycle: Lifecycle = Lifecycle.DISCOVERED
    grammar_version: str = GRAMMAR_VERSION
    ontology_release: str = ONTOLOGY_RELEASE
    ref: Ref | None = None

    def __post_init__(self):
        # I-08
        _require(self.source is not None or self.origin in AUTHORIZED_ORIGINS,
                 "assertion needs a source or an authorized origin", "I-08")
        if self.lifecycle in _LIFE_ORDER and _LIFE_ORDER[self.lifecycle] >= _LIFE_ORDER[Lifecycle.VALIDATED_FORMALLY]:
            _require(self.evidence is not None, "validated assertions need an evidence reference", "I-08")
        # SG-EVD-003: inference vs source-stated must stay separate
        if self.origin is Origin.BACKGROUND_INFERENCE:
            _require(self.epistemic_status is not EpistemicStatus.SOURCE_ASSERTED,
                     "a background inference cannot be SOURCE_ASSERTED", "SG-EVD-003")
        elif self.origin in (Origin.SOURCE_TEXT, Origin.GRAMMATICAL):
            _require(self.epistemic_status is not EpistemicStatus.INFERRED,
                     "source-derived content cannot be INFERRED", "SG-EVD-003")
        if self.commitment is CommitmentKind.ATTRIBUTED:
            _require(self.attributed_to is not None, "ATTRIBUTED commitment needs the committing referent", "SG-EVD-007")
        if self.eval_context is not EvalContextKind.WORLD and self.commitment is CommitmentKind.AUTHOR:
            # allowed (e.g. author states a fiction), but it will never enter the trusted view
            pass
        _require(self.grammar_version != "" and self.ontology_release != "", "assertions pin versions", "I-12")

    @staticmethod
    def new(content_type: ContentType, content: Ref, origin: Origin, **kw: Any) -> "Assertion":
        """Create a fresh assertion with the only statuses a new claim may have."""
        status = EpistemicStatus.INFERRED if origin is Origin.BACKGROUND_INFERENCE else EpistemicStatus.SOURCE_ASSERTED
        return Assertion(content_type, content, origin, status, **kw)

    def with_status(self, new: EpistemicStatus, actor: Component) -> "Assertion":
        check_epistemic_transition(self.epistemic_status, new, actor)
        return dataclasses.replace(self, epistemic_status=new)

    def with_stage(self, new: Lifecycle, actor: Component) -> "Assertion":
        check_lifecycle_transition(self.lifecycle, new, actor)
        return dataclasses.replace(self, lifecycle=new)


@dataclass(frozen=True)
class LanguageAnnotation:
    """Language-specific distinctions that do not change truth conditions
    (SG-CON-004). Features that do (tense, modality, negation, evidential
    markers) belong to grammar operators, not here."""

    language: str
    features: tuple[tuple[str, str], ...] = ()
    span: Span | None = None

    TRUTH_CONDITIONAL = frozenset({"tense", "modality", "negation", "polarity", "evidentiality", "aspect"})

    def __post_init__(self):
        for k, _ in self.features:
            _require(k not in self.TRUTH_CONDITIONAL,
                     f"feature {k!r} changes truth conditions: it belongs in operators (SG-CON-004)", "SG-CON-004")
