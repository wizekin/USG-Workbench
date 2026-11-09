"""Orthogonal evidence, epistemics, independence and conflict views."""
from dataclasses import asdict, dataclass
from ..core.values import EvidenceLabel


@dataclass(frozen=True)
class EvidenceVector:
    source_hash: str
    source_span: tuple[int, int]
    extraction_method: str
    rule_validation: str
    independent_origins: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    review_status: str = "AUTOMATIC_FORMAL_CHECKS"
    source_supported: bool = True
    derived: bool = False
    curated: bool = False

    @property
    def label(self):
        if self.curated:
            return EvidenceLabel.E5_CURATED
        if self.derived:
            return EvidenceLabel.E4_DERIVED
        if not self.source_supported:
            return EvidenceLabel.E0_UNSUPPORTED
        if len(set(self.independent_origins)) >= 2 and not self.uncertainty:
            return EvidenceLabel.E3_CORROBORATED
        return EvidenceLabel.E2_SOURCE_SUPPORTED if not self.uncertainty else EvidenceLabel.E1_HYPOTHESIS

    def to_json(self):
        return {**asdict(self), "label": self.label.name}
