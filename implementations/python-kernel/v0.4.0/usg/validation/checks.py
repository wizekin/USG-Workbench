from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from ..core.values import CheckResult


class Level(IntEnum):
    L1_STRUCTURAL = 1
    L2_TYPE = 2
    L3_LOGICAL = 3
    L4_EVIDENCE = 4
    L5_CONTEXTUAL = 5


@dataclass(frozen=True)
class CheckDef:
    check_id: str
    level: Level
    name: str


L1, L2, L3, L4, L5 = Level.L1_STRUCTURAL, Level.L2_TYPE, Level.L3_LOGICAL, Level.L4_EVIDENCE, Level.L5_CONTEXTUAL

CHECKS: tuple[CheckDef, ...] = (
    CheckDef("VC-S01", L1, "candidate schema validity"),
    CheckDef("VC-S02", L1, "record header and source consistency"),
    CheckDef("VC-S03", L1, "every id resolves"),
    CheckDef("VC-S04", L1, "every cited rule id is registered"),
    CheckDef("VC-S05", L1, "frame exists at the pinned version and is instantiable"),
    CheckDef("VC-S06", L1, "every bound role is defined by the frame (closed role list)"),
    CheckDef("VC-S07", L1, "every REQUIRED role bound or in an explicit hole state"),
    CheckDef("VC-S08", L1, "role cardinality"),
    CheckDef("VC-S09", L1, "sort discipline"),
    CheckDef("VC-S10", L1, "spans lie within the stored text and the unit"),
    CheckDef("VC-S11", L1, "no ERROR node in a committed expression"),
    CheckDef("VC-S12", L1, "no free variables"),
    CheckDef("VC-S13", L1, "no variable shadowing"),
    CheckDef("VC-S14", L1, "ALT well-formed"),
    CheckDef("VC-S15", L1, "no provisional id in a trusted expression"),
    CheckDef("VC-S16", L1, "nesting depth and acyclic structure"),
    CheckDef("VC-T01", L2, "filler sort/kind compatible with the role"),
    CheckDef("VC-T02", L2, "class compatibility (three-valued)"),
    CheckDef("VC-T03", L2, "value in the property's domain; quantities carry units"),
    CheckDef("VC-T04", L2, "no bare concept id as a role filler"),
    CheckDef("VC-T05", L2, "relation domain and range"),
    CheckDef("VC-T06", L2, "disjoint roles do not share a referent"),
    CheckDef("VC-T07", L2, "a coercion or figurative reading cites a registered mapping"),
    CheckDef("VC-T08", L2, "a VALUE is not used where a PROPERTY is expected"),
    CheckDef("VC-G01", L3, "relations declared acyclic contain no cycle"),
    CheckDef("VC-G02", L3, "declared relation properties hold"),
    CheckDef("VC-G03", L3, "no contradiction inside one context"),
    CheckDef("VC-G04", L3, "frame multiple-inheritance conflicts"),
    CheckDef("VC-G05", L3, "ESSENTIAL consequences do not contradict explicit bindings"),
    CheckDef("VC-G06", L3, "temporal consistency"),
    CheckDef("VC-G07", L3, "quantifier, negation and modal scope well-formed"),
    CheckDef("VC-G08", L3, "presupposed content emitted in its context"),
    CheckDef("VC-G09", L3, "opaque contexts respected"),
    CheckDef("VC-G10", L3, "canonicalization preserves validity"),
    CheckDef("VC-V01", L4, "every element is supported (span, declared inference or authorized source)"),
    CheckDef("VC-V02", L4, "cited span text lexically supports the claimed element"),
    CheckDef("VC-V03", L4, "basis labels match the derivation"),
    CheckDef("VC-V04", L4, "derivation chain complete and outcome consistent"),
    CheckDef("VC-V05", L4, "deterministic steps replay to the claimed output"),
    CheckDef("VC-V06", L4, "background content is never labelled source-stated"),
    CheckDef("VC-V07", L4, "negation, modality, conditional, quantifier and tense cues are reflected by operators"),
    CheckDef("VC-V08", L4, "numeric cues match literals"),
    CheckDef("VC-V09", L4, "inference premises are registered and valid"),
    CheckDef("VC-C01", L5, "word sense plausible given context"),
    CheckDef("VC-C02", L5, "coreference plausible"),
    CheckDef("VC-C03", L5, "operator scope plausible"),
    CheckDef("VC-C04", L5, "retained alternatives are real; none silently dropped"),
    CheckDef("VC-C05", L5, "metamorphic consistency with paraphrase variants"),
    CheckDef("VC-C06", L5, "consistency with existing trusted knowledge"),
    CheckDef("VC-C07", L5, "automated panel verdict"),
)

CHECK_IDS = frozenset(c.check_id for c in CHECKS)
_LEVEL = {c.check_id: c.level for c in CHECKS}


def level_of(check_id: str) -> Level:
    return _LEVEL[check_id]


@dataclass(frozen=True)
class CheckOutcome:
    check_id: str
    result: CheckResult
    detail: str = ""
    element: str | None = None  # a role name, a path or a rule id: where the problem is

    @property
    def level(self) -> Level:
        return _LEVEL[self.check_id]

    def to_json(self) -> dict:
        return {"check": self.check_id, "level": int(self.level), "result": self.result.value, "detail": self.detail,
                "element": self.element}
