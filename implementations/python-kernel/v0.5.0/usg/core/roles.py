"""Two-tier role system (spec Part 2 §2.6, Enhancement E-04).

Tier 1: a closed set of universal thematic roles owned by the grammar.
Tier 2: frame-specific roles, each of which MUST name its tier-1 parent
(invariant I-04). 'UNDERGOER' replaces the thematic-role literature's
'patient' to avoid colliding with the medical concept Patient."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..errors import InvariantViolation
from .ids import Ref
from .kinds import SemKind


class Requiredness(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


TIER1_ROLES: dict[str, str] = {
    "AGENT": "Intentional initiator or doer",
    "CAUSE": "Non-agentive causer (entity, event or state)",
    "EXPERIENCER": "Entity in a perceptual or mental state",
    "UNDERGOER": "Participant changed or affected",
    "THEME": "Participant moved, transferred, located or discussed",
    "RECIPIENT": "Receiver of a transfer or communication",
    "BENEFICIARY": "Party for whose benefit something is done",
    "INSTRUMENT": "Means used",
    "SOURCE": "Origin of motion, transfer or information",
    "GOAL": "Destination or endpoint",
    "LOCATION": "Place of the situation",
    "PATH": "Route",
    "TIME": "When the situation holds",
    "MANNER": "How",
    "PURPOSE": "Intended outcome",
    "CONTENT": "Situation or proposition believed, said, wanted or known",
    "STIMULUS": "What is perceived or reacted to",
    "COMITATIVE": "Co-participant",
    "MEASURE": "Quantity or degree",
}


@dataclass(frozen=True)
class RoleSpec:
    """A role as used by a frame definition."""

    name: str
    tier: int
    parent_role: str | None
    expected_kind: SemKind = SemKind.ENTITY
    expected_class: Ref | None = None  # concept id; class constraint (soft/extensible)
    requiredness: Requiredness = Requiredness.OPTIONAL
    card_min: int = 0
    card_max: int = 1
    # Roles that may be filled by the same referent only when explicitly allowed.
    coercion_allowed: tuple[str, ...] = ()

    def __post_init__(self):
        if self.tier == 1:
            if self.name not in TIER1_ROLES:
                raise InvariantViolation(f"{self.name!r} is not a tier-1 role", "I-04")
            if self.parent_role is not None:
                raise InvariantViolation("tier-1 roles have no parent", "I-04")
        elif self.tier == 2:
            if self.name in TIER1_ROLES:
                raise InvariantViolation(f"tier-2 role {self.name!r} collides with a tier-1 role name", "I-04")
            if self.parent_role not in TIER1_ROLES:
                raise InvariantViolation(
                    f"tier-2 role {self.name!r} must name a tier-1 parent (got {self.parent_role!r})", "I-04"
                )
        else:
            raise InvariantViolation("role tier must be 1 or 2", "I-04")
        if self.card_min < 0 or self.card_max < max(1, self.card_min):
            raise InvariantViolation(f"bad cardinality ({self.card_min},{self.card_max}) on {self.name}", "I-05")
        if self.requiredness is Requiredness.REQUIRED and self.card_min < 1:
            object.__setattr__(self, "card_min", 1)

    @property
    def tier1_parent(self) -> str:
        return self.name if self.tier == 1 else str(self.parent_role)

    @property
    def display(self) -> str:
        return f"role:{self.name}"


def tier1(name: str, *, required: bool = False, kind: SemKind = SemKind.ENTITY, card_max: int = 1,
          expected_class: Ref | None = None) -> RoleSpec:
    return RoleSpec(name, 1, None, kind, expected_class,
                    Requiredness.REQUIRED if required else Requiredness.OPTIONAL,
                    1 if required else 0, card_max)


def tier2(name: str, parent: str, *, required: bool = False, kind: SemKind = SemKind.ENTITY, card_max: int = 1,
          expected_class: Ref | None = None) -> RoleSpec:
    return RoleSpec(name, 2, parent, kind, expected_class,
                    Requiredness.REQUIRED if required else Requiredness.OPTIONAL,
                    1 if required else 0, card_max)
