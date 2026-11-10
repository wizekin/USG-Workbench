"""Starter relation catalogue (spec Part 2 §2.8). Part of the sealed Foundation Package."""

from __future__ import annotations

from ..core.kinds import SemKind
from ..model.relations import RelationCategory as C
from ..model.relations import RelationDef as R

E, EV = SemKind.ENTITY, SemKind.EVENT

RELATIONS: tuple[R, ...] = (
    R("SUBCLASS_OF", C.LOGICAL, reflexive=True, transitive=True, cycles_allowed=True,
      description="A ⊑ B. Mutual subclassing is flagged as a probable equivalence, not an error."),
    R("PROPER_SUBCLASS_OF", C.LOGICAL, irreflexive=True, asymmetric=True, transitive=True, sub_relation_of="SUBCLASS_OF"),
    R("INSTANCE_OF", C.LOGICAL, description="referent -> concept"),
    R("PROPER_PART_OF", C.LOGICAL, irreflexive=True, asymmetric=True, transitive=True, inverse_of="HAS_PART",
      description="idealised strict parthood"),
    R("HAS_PART", C.LOGICAL, irreflexive=True, asymmetric=True, transitive=True, inverse_of="PROPER_PART_OF"),
    R("PHYSICAL_COMPONENT_OF", C.LOGICAL, irreflexive=True, asymmetric=True, sub_relation_of="PROPER_PART_OF",
      description="transitivity per subtype requires domain review"),
    R("MATERIAL_PORTION_OF", C.LOGICAL, irreflexive=True, asymmetric=True, sub_relation_of="PROPER_PART_OF"),
    R("ORGANIZATIONAL_MEMBER_OF", C.LOGICAL, irreflexive=True, asymmetric=True,
      description="not transitive: employee-of is not physical composition"),
    R("INFORMATIONAL_COMPONENT_OF", C.LOGICAL, irreflexive=True, asymmetric=True, sub_relation_of="PROPER_PART_OF"),
    R("HAS_FUNCTION", C.LOGICAL, description="performer -> FUNCTION; mode PURPOSE/CAPABILITY/CONTEXTUAL; never implies IS_A (SG-FRM-005)"),
    R("TYPICALLY_HAS", C.EPISTEMIC, defeasible=True, description="typical, not exceptionless"),
    R("KNOWS", C.LOGICAL, cycles_allowed=True, irreflexive=True, description="a valid social cycle"),
    R("DISJOINT_WITH", C.LOGICAL, symmetric=True, irreflexive=True, cycles_allowed=True,
      description="provably no shared instances"),
    R("ASSOCIATED_WITH", C.ASSOCIATIVE, symmetric=True, cycles_allowed=True,
      description="retrieval aid only; weights record their scoring model (SG-KNW-002)"),
    R("DRIVES_FLOW_OF", C.LOGICAL, cycles_allowed=True, description="driver -> fluid"),
    R("FLOWS_THROUGH", C.LOGICAL, cycles_allowed=True, description="fluid -> conduit"),
    R("MEASURES", C.LOGICAL, cycles_allowed=True, description="instrument -> measured property"),
)
