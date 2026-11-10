"""Seed classes, properties and values (Foundation Package, spec Part 4 §4.12.1).

A deliberately small curated set: just enough for the 20 kernel frames, their
type constraints, the benchmark and cross-domain tests. Everything else enters
through the (gated) learning pipeline. Part of the sealed package."""

from __future__ import annotations

from ..core.kinds import SemKind as K
from ..ontology import ConceptSeed as S

U, MED, BIO, ENG, ECO = "UNIVERSAL_CORE", "MEDICINE", "BIOLOGY", "ENGINEERING", "ECONOMICS"

DOMAINS = (U, "LANGUAGE", MED, BIO, ENG, ECO, "PHYSICS", "CHEMISTRY")

ENTITY_CLASSES: tuple[S, ...] = (
    S("Entity", K.ENTITY),
    S("PhysicalEntity", K.ENTITY, ("Entity",), disjoint_with=("AbstractEntity",)),
    S("AbstractEntity", K.ENTITY, ("Entity",)),
    S("Agent", K.ENTITY, ("Entity",), doc="anything that can act intentionally"),
    S("AnimateEntity", K.ENTITY, ("PhysicalEntity",), disjoint_with=("AbstractEntity", "Artifact", "Substance", "Location")),
    S("Person", K.ENTITY, ("AnimateEntity", "Agent")),
    S("Organization", K.ENTITY, ("Agent",), disjoint_with=("Person",)),
    S("Animal", K.ENTITY, ("AnimateEntity",), (BIO,)),
    S("PhysicalObject", K.ENTITY, ("PhysicalEntity",)),
    S("Substance", K.ENTITY, ("PhysicalEntity",)),
    S("Fluid", K.ENTITY, ("Substance",), ("PHYSICS",)),
    S("Liquid", K.ENTITY, ("Fluid",), ("PHYSICS",), disjoint_with=("Gas",)),
    S("Gas", K.ENTITY, ("Fluid",), ("PHYSICS",)),
    S("Blood", K.ENTITY, ("Liquid",), (BIO, MED)),
    S("Water", K.ENTITY, ("Liquid",), ("CHEMISTRY",)),
    S("Air", K.ENTITY, ("Gas",), ("PHYSICS",)),
    S("EdibleEntity", K.ENTITY, ("PhysicalEntity",)),
    S("Food", K.ENTITY, ("EdibleEntity", "Substance")),
    S("Apple", K.ENTITY, ("EdibleEntity", "PhysicalObject")),
    S("Location", K.ENTITY, ("PhysicalEntity",)),
    S("Hospital", K.ENTITY, ("Location", "Organization"), (MED,), doc="institution and place: multiple inheritance"),
    S("Company", K.ENTITY, ("Organization",), (ECO,)),
    S("Artifact", K.ENTITY, ("PhysicalObject",), (ENG,)),
    S("Vehicle", K.ENTITY, ("Artifact",), (ENG,)),
    S("Car", K.ENTITY, ("Vehicle",), (ENG,)),
    S("Device", K.ENTITY, ("Artifact",), (ENG,)),
    S("Engine", K.ENTITY, ("Device",), (ENG,)),
    S("Pump", K.ENTITY, ("Device",), (ENG,)),
    S("Fan", K.ENTITY, ("Device",), (ENG,)),
    S("Pipe", K.ENTITY, ("Artifact",), (ENG,)),
    S("Telescope", K.ENTITY, ("Device",), (ENG,)),
    S("Door", K.ENTITY, ("Artifact",)),
    S("Book", K.ENTITY, ("Artifact",)),
    S("Medication", K.ENTITY, ("Substance",), (MED,)),
    S("Tablet", K.ENTITY, ("Medication",), (MED,)),
    S("Doctor", K.ENTITY, ("Person",), (MED,)),
    S("Patient", K.ENTITY, ("Person",), (MED,), doc="a concept (type); the thematic role is UNDERGOER"),
    S("BodyPart", K.ENTITY, ("PhysicalObject",), (BIO,)),
    S("Heart", K.ENTITY, ("BodyPart",), (BIO, MED)),
    S("BloodVessel", K.ENTITY, ("BodyPart",), (BIO,)),
    S("Information", K.ENTITY, ("AbstractEntity",)),
    S("Argument", K.ENTITY, ("Information",), doc="abstract: cannot be bought or eaten"),
    S("Money", K.ENTITY, ("AbstractEntity",), (ECO,)),
)

PROPERTIES_AND_VALUES: tuple[S, ...] = (
    S("Color", K.PROPERTY, value_domain="ColorValue"),
    S("ColorValue", K.VALUE),
    S("Red", K.VALUE, ("ColorValue",), disjoint_with=("Blue", "Green")),
    S("Blue", K.VALUE, ("ColorValue",), disjoint_with=("Green",)),
    S("Green", K.VALUE, ("ColorValue",)),
    S("AgeGroup", K.PROPERTY, value_domain="AgeGroupValue"),
    S("AgeGroupValue", K.VALUE),
    S("Young", K.VALUE, ("AgeGroupValue",), disjoint_with=("Old",)),
    S("Old", K.VALUE, ("AgeGroupValue",)),
    S("Openness", K.PROPERTY, value_domain="OpennessValue"),
    S("OpennessValue", K.VALUE),
    S("OpenState", K.VALUE, ("OpennessValue",), disjoint_with=("ClosedState",)),
    S("ClosedState", K.VALUE, ("OpennessValue",)),
    S("Phase", K.PROPERTY, value_domain="PhaseValue", doc="physical phase of matter"),
    S("PhaseValue", K.VALUE),
    S("PhaseSolid", K.VALUE, ("PhaseValue",), ("PHYSICS",), disjoint_with=("PhaseLiquid", "PhaseGas")),
    S("PhaseLiquid", K.VALUE, ("PhaseValue",), ("PHYSICS",), disjoint_with=("PhaseGas",)),
    S("PhaseGas", K.VALUE, ("PhaseValue",), ("PHYSICS",)),
    S("Temperature", K.PROPERTY, (), ("PHYSICS",)),
    S("Allergy", K.STATE, (), (MED,), doc="experiencer state, used by EXPERIENCE_STATE pins"),
)

SEED_CONCEPTS: tuple[S, ...] = ENTITY_CLASSES + PROPERTIES_AND_VALUES
