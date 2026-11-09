"""Functional ontology (spec Part 4 §4.8): six PRIMITIVE functions plus two
DERIVED composites. Functions live in the FN namespace as concepts of kind
FUNCTION and are SEALED: FN_PRIMITIVE_CHANGE is a forbidden runtime action
(SG-FRM-009). TRANSPORT keeps its name; TRANSFER is reserved for the frame
family (E-07)."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.kinds import SemKind
from ..ontology import ConceptSeed

FN_PRIMITIVES = ("FN.DETECT", "FN.DECIDE", "FN.ACT", "FN.STORE", "FN.TRANSPORT", "FN.TRANSFORM")
FN_DERIVED = ("FN.PROCESS_INFORMATION", "FN.REGULATE")


@dataclass(frozen=True)
class FunctionSeed:
    name: str
    parents: tuple[str, ...] = ()
    definition: str = ""
    roles: tuple[str, ...] = ()
    derived: bool = False
    composed_of: tuple[str, ...] = ()  # derived composites are defined from primitives

    def to_concept(self) -> ConceptSeed:
        return ConceptSeed(self.name, SemKind.FUNCTION, self.parents, ("UNIVERSAL_CORE",), doc=self.definition)


_F = FunctionSeed
FUNCTIONS: tuple[FunctionSeed, ...] = (
    _F("FN.DETECT", definition="registers a state or quantity of something", roles=("DETECTOR", "TARGET_PROPERTY", "SIGNAL")),
    _F("FN.DECIDE", definition="selects among alternatives using criteria", roles=("DECIDER", "OPTIONS", "CRITERIA", "OUTCOME")),
    _F("FN.ACT", definition="changes the state of something in the environment", roles=("ACTUATOR", "TARGET", "CHANGE")),
    _F("FN.STORE", definition="holds a resource or state over time", roles=("HOLDER", "HELD", "DURATION")),
    _F("FN.TRANSPORT", definition="moves or carries something between locations or parts",
       roles=("DRIVER", "TRANSPORTED", "SOURCE", "DESTINATION", "CONDUIT")),
    _F("FN.TRANSFORM", definition="converts one thing into another", roles=("TRANSFORMER", "INPUT", "OUTPUT", "BYPRODUCT")),
    # derived composites (not primitives)
    _F("FN.PROCESS_INFORMATION", ("FN.TRANSFORM",), "FN.TRANSFORM whose INPUT and OUTPUT are information",
       derived=True, composed_of=("FN.TRANSFORM",)),
    _F("FN.REGULATE", (), "LOOP composite DETECT -> DECIDE -> ACT that keeps a quantity near a target",
       derived=True, composed_of=("FN.DETECT", "FN.DECIDE", "FN.ACT")),
    # sub-functions: a pump DRIVES flow, a pipe CONDUCTS it (a rule 'everything that moves fluid is a pump' is refuted)
    _F("FN.TRANSPORT_MATTER", ("FN.TRANSPORT",)),
    _F("FN.TRANSPORT_FLUID", ("FN.TRANSPORT_MATTER",)),
    _F("FN.DRIVE_FLUID_FLOW", ("FN.TRANSPORT_FLUID",), "supplies the force that moves a fluid"),
    _F("FN.CONDUCT_FLUID", ("FN.TRANSPORT_FLUID",), "channels a fluid without driving it"),
    _F("FN.TRANSPORT_ENERGY", ("FN.TRANSPORT",)),
    _F("FN.TRANSPORT_INFORMATION", ("FN.TRANSPORT",)),
    _F("FN.MEASURE", ("FN.DETECT",)),
    _F("FN.MEASURE_HUMIDITY", ("FN.MEASURE",)),
    _F("FN.STORE_ENERGY", ("FN.STORE",)),
    _F("FN.STORE_INFORMATION", ("FN.STORE",)),
)

# (performer concept, function, mode) -> HAS_FUNCTION edges; never implies IS_A (SG-FRM-005)
SEED_FUNCTION_EDGES: tuple[tuple[str, str, str], ...] = (
    ("Heart", "FN.DRIVE_FLUID_FLOW", "PURPOSE"),
    ("Pump", "FN.DRIVE_FLUID_FLOW", "PURPOSE"),
    ("Fan", "FN.DRIVE_FLUID_FLOW", "PURPOSE"),
    ("Pipe", "FN.CONDUCT_FLUID", "PURPOSE"),
    ("BloodVessel", "FN.CONDUCT_FLUID", "PURPOSE"),
)
