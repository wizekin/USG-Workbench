"""Fixed semantic kinds (spec Part 2 §2.2). Adding or changing a kind is a MAJOR
grammar change. Ontology classes (Vehicle, Fluid, ...) are *concepts*, not kinds."""

from __future__ import annotations

from enum import Enum


class SemKind(str, Enum):
    ENTITY = "ENTITY"
    EVENT = "EVENT"
    PROCESS = "PROCESS"
    STATE = "STATE"
    PROPERTY = "PROPERTY"
    VALUE = "VALUE"
    QUANTITY = "QUANTITY"
    RELATION = "RELATION"
    ROLE = "ROLE"
    FRAME = "FRAME"
    PROPOSITION = "PROPOSITION"
    CONSTRAINT = "CONSTRAINT"
    TIME = "TIME"
    FUNCTION = "FUNCTION"
    EXPRESSION = "EXPRESSION"


# Definition kinds MUST NOT fill a role in a frame instance (Kind rule 2).
DEFINITION_KINDS = frozenset({SemKind.ROLE, SemKind.RELATION, SemKind.FRAME, SemKind.CONSTRAINT})

SITUATION_KINDS = frozenset({SemKind.EVENT, SemKind.PROCESS, SemKind.STATE})


def can_fill_role(kind: SemKind) -> bool:
    return kind not in DEFINITION_KINDS


# The five broad sorts of the expression grammar (Part 3 §3.3.1). This is a
# coarse grouping only: kinds sharing a sort (SIT, VAL) remain distinct and
# must still be compared exactly by semantic-kind validation.
class Sort(str, Enum):
    TERM = "TERM"
    SIT = "SIT"
    PROP = "PROP"
    VAL = "VAL"
    TIME = "TIME"


KIND_TO_SORT = {
    SemKind.ENTITY: Sort.TERM,
    SemKind.EVENT: Sort.SIT,
    SemKind.PROCESS: Sort.SIT,
    SemKind.STATE: Sort.SIT,
    SemKind.PROPOSITION: Sort.PROP,
    SemKind.VALUE: Sort.VAL,
    SemKind.QUANTITY: Sort.VAL,
    SemKind.TIME: Sort.TIME,
}
