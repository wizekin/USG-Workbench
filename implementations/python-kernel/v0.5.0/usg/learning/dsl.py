"""Non-executable rule DSL. The current extension point is literal verb aliases.

An alias can reuse an approved valence pattern; it cannot edit a frame, remove
an operator, run Python/regex, change evidence, or relax validation.
"""
from dataclasses import asdict, dataclass
import re
from ..errors import InvariantViolation


@dataclass(frozen=True)
class RuleProposal:
    name: str
    trigger: str
    equivalent_verb: str
    positive: tuple[str, ...]
    negative: tuple[str, ...]
    contrastive: tuple[tuple[str, str], ...]
    kind: str = "VERB_ALIAS"
    version: int = 1

    def __post_init__(self):
        from ..interpretation.parser import VERBS
        if self.kind != "VERB_ALIAS" or self.version != 1:
            raise InvariantViolation("unsupported declarative rule", "SG-GOV-002")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", self.name):
            raise InvariantViolation("invalid rule name", "SG-GOV-002")
        if not re.fullmatch(r"[a-z]{2,32}", self.trigger) or self.trigger in VERBS or self.equivalent_verb not in VERBS:
            raise InvariantViolation("alias must introduce a new literal form for an approved verb", "SG-GOV-002")
        if not all(re.search(r"\b" + re.escape(self.trigger) + r"\b", text, re.I) for text in self.positive):
            raise InvariantViolation("positive tests must exercise the proposed trigger", "SG-GOV-002")
        if not 2 <= len(self.positive) <= 20 or not 2 <= len(self.negative) <= 20 or not 1 <= len(self.contrastive) <= 10:
            raise InvariantViolation("positive, negative and contrastive tests are required", "SG-GOV-002")
        if any(not isinstance(t, str) or not t or len(t) > 2000 for t in (*self.positive, *self.negative, *(x for pair in self.contrastive for x in pair))):
            raise InvariantViolation("invalid rule test", "SG-GOV-002")
        if any(len(pair) != 2 for pair in self.contrastive):
            raise InvariantViolation("contrastive test needs a pair", "SG-GOV-002")

    def to_json(self):
        return asdict(self)

    @staticmethod
    def from_json(d):
        allowed = {"name", "trigger", "equivalent_verb", "positive", "negative", "contrastive", "kind", "version"}
        if not isinstance(d, dict) or set(d) - allowed:
            raise InvariantViolation("unknown rule DSL fields", "SG-GOV-002")
        try:
            d = dict(d)
            for k in ("positive", "negative"):
                d[k] = tuple(d[k])
            d["contrastive"] = tuple(tuple(p) for p in d["contrastive"])
            return RuleProposal(**d)
        except (KeyError, TypeError, ValueError) as ex:
            raise InvariantViolation("malformed rule proposal", "SG-GOV-002") from ex
