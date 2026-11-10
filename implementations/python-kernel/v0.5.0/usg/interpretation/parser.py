"""A conservative semantic compiler for a documented English/Arabic subset.

Every token must be consumed by an explicit rule. Unsupported constructions
produce UNRESOLVED, never a partially asserted sentence with dropped meaning.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import Config
from ..concepts.lexicon import resolve
from ..core.values import Basis, Outcome
from ..foundation.builder import build_foundation
from ..grammar.annot import explicit, grammatical
from ..grammar.canon import canonicalize
from ..grammar.node import (Ann, Node, alt, and_, apply, aspect, assert_, cond, error, holds, hole, kind,
                            modal, not_, prop, q, ref, relate, role_entries, speech_time, tense, time_rel,
                            value, var, walk)
from ..grammar.timeval import resolve_node
from ..security.text import tripwires
from ..validation.certificate import Candidate, CertStep, DerivationCertificate, StepType
from ..validation.validator import with_presuppositions


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int

    @property
    def lower(self):
        return self.text.casefold()


@dataclass(frozen=True)
class Mention:
    handle: str
    label: str
    concept: str
    span: tuple[int, int]
    number: str = "SINGULAR"
    cardinality: int | None = None
    introduced_in: str = "WORLD"


@dataclass(frozen=True)
class Interpretation:
    candidate: Candidate
    mentions: tuple[Mention, ...]
    issues: tuple[str, ...]
    unknown_words: tuple[str, ...] = ()


class Unsupported(Exception):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, detail


# frame, subject role, object role, morphology. Closed resource, not a statistical model.
VERBS = {}
PARTICIPLES = set()
def _verbs(frame, subject, object_, present, past, participle=None):
    for form in present.split():
        VERBS[form] = (frame, subject, object_, "PRESENT", False)
    for form in past.split():
        VERBS[form] = (frame, subject, object_, "PAST", True)
    for form in (participle or past).split():
        PARTICIPLES.add(form)
        VERBS.setdefault(form, (frame, subject, object_, "PAST", True))

_verbs("GIVE", "AGENT", "THEME", "give gives", "gave", "given")
_verbs("RETURN", "AGENT", "THEME", "return returns", "returned")
_verbs("LEND", "AGENT", "THEME", "lend lends", "lent")
_verbs("COMMERCIAL_TRANSACTION", "BUYER", "GOODS", "buy buys purchase purchases", "bought purchased")
_verbs("COMMERCIAL_TRANSACTION", "SELLER", "GOODS", "sell sells", "sold")
_verbs("EAT", "EATER", "FOOD", "eat eats", "ate", "eaten")
_verbs("OPEN", "AGENT", "UNDERGOER", "open opens", "opened")
_verbs("CLOSE", "AGENT", "UNDERGOER", "close closes", "closed")
_verbs("HEAT", "AGENT", "UNDERGOER", "heat heats", "heated")
_verbs("COOL", "AGENT", "UNDERGOER", "cool cools", "cooled")
_verbs("FREEZE", "AGENT", "UNDERGOER", "freeze freezes", "froze", "frozen")
_verbs("SEE", "EXPERIENCER", "STIMULUS", "see sees", "saw", "seen")
_verbs("PERCEIVE", "EXPERIENCER", "STIMULUS", "perceive perceives hear hears", "perceived heard")
_verbs("EXAMINATION", "EXAMINER", "EXAMINED_ENTITY", "examine examines", "examined")
_verbs("TREAT", "PRACTITIONER", "TREATED_ENTITY", "treat treats", "treated")
_verbs("OWN", "OWNER", "OWNED_ENTITY", "own owns", "owned")
_verbs("WORK", "WORKER", None, "work works", "worked")
_verbs("MOVE", "MOVER", None, "move moves go goes walk walks travel travels", "moved went walked travelled traveled")
_verbs("BELIEVE", "EXPERIENCER", "CONTENT", "believe believes", "believed")
_verbs("KNOW", "EXPERIENCER", "CONTENT", "know knows", "knew", "known")
_verbs("WANT", "EXPERIENCER", "CONTENT", "want wants", "wanted")
_verbs("ATTEMPT", "AGENT", "CONTENT", "try tries attempt attempts", "tried attempted")
_verbs("OFFER", "OFFERER", "CONTENT", "offer offers", "offered")
_verbs("COMMUNICATE", "SPEAKER", "CONTENT", "say says tell tells", "said told")
PAST_AUX = {"did", "was", "were", "had"}
AUX = PAST_AUX | {"do", "does", "is", "are", "am", "has", "have", "will", "may", "might", "must", "can", "could", "should"}
DETS = {"a", "an", "the", "this", "that", "these", "those"}
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
ADJECTIVES = {"young": ("AgeGroup", "Young"), "old": ("AgeGroup", "Old"), "red": ("Color", "Red"), "blue": ("Color", "Blue"), "green": ("Color", "Green")}
QUANTS = {"every": "FORALL", "each": "FORALL", "all": "FORALL", "no": "NO", "some": "EXISTS"}


class DeterministicInterpreter:
    def __init__(self, foundation=None, config=None, aliases=None):
        self.foundation = foundation or build_foundation()
        self.config = config or Config()
        self.aliases = dict(aliases or {})
        self.resolve = resolve

    def interpret(self, source, unit, discourse=()):
        state = _ParseState(self, source, unit, tuple(discourse))
        return state.run()


class _ParseState:
    def __init__(self, parser, source, unit, discourse):
        self.parser, self.source, self.unit = parser, source, unit
        self.mentions, self.properties, self.quantifiers, self.unknown, self.issues = [], [], [], [], []
        self.discourse = discourse
        self.tokens = [Token(m.group(), unit.start + m.start(), unit.start + m.end())
                       for m in re.finditer(r"(?:[^\W\d_]|[\u064b-\u0652\u0670])+(?:['’](?:[^\W\d_]|[\u064b-\u0652\u0670])+)?|\d+(?:\.\d+)?|[^\s\w\u064b-\u0652\u0670]", source.text[unit.start:unit.end], re.UNICODE)]
        self.tokens = [t for t in self.tokens if t.text not in ".!?؟。"]

    def run(self):
        outcome, expr = Outcome.RESOLVED, None
        try:
            if self.unit.end - self.unit.start > self.parser.config["max_unit_chars"]:
                raise Unsupported("UNIT_TOO_LONG")
            if any(ch in self.source.span_text(self.unit) for ch in '?؟'):
                raise Unsupported('NONASSERTIVE_QUESTION')
            if tripwires(self.source.span_text(self.unit)):
                raise Unsupported("INJECTION_CUE")
            if self.source.language not in {"en", "ar"}:
                raise Unsupported("UNSUPPORTED_LANGUAGE", self.source.language)
            ts = self.tokens
            if self.source.language == "ar":
                expr = self.arabic(ts)
            else:
                expr = self.clause(ts)
            if len(self.quantifiers) > 1:
                raise Unsupported('QUANTIFIER_SCOPE_AMBIGUOUS')
            if self.properties:
                expr = and_(expr, *self.properties)
            for quant, name, restrictor, count in reversed(self.quantifiers):
                expr = grammatical(q(quant, name, restrictor, expr, n=count), "SG-INT-022")
            expr = with_presuppositions(assert_(expr, origin="SOURCE_TEXT"), self.parser.foundation.frames)
            expr = canonicalize(expr, anchor=self.source.anchor, relations=self.parser.foundation.relations)
            if any(n.op == "ALT" for _, n in walk(expr)):
                outcome = Outcome.AMBIGUOUS
        except Unsupported as ex:
            outcome = Outcome.UNRESOLVED
            self.issues.append(ex.code)
            expr = assert_(error(ex.code, ex.detail or "outside the deterministic grammar", (self.unit.start, self.unit.end)))
        steps = self.certificate_steps(expr)
        cert = DerivationCertificate(self.source.text_hash, producer_kind="RULE_ENGINE", steps=steps,
                                     unresolved=tuple(self.issues), outcome=outcome)
        return Interpretation(Candidate(self.source, self.unit, expr, cert), tuple(self.mentions), tuple(self.issues), tuple(self.unknown))

    def np(self, ts, context="WORLD"):
        if not ts:
            return hole()
        original = list(ts)
        quant, count = None, None
        if ts[0].lower in QUANTS:
            quant, ts = QUANTS[ts[0].lower], ts[1:]
        elif ts[0].lower in DETS:
            ts = ts[1:]
        if ts and (ts[0].lower in NUMBERS or ts[0].text.isdigit()):
            count = NUMBERS.get(ts[0].lower, int(ts[0].text) if ts[0].text.isdigit() else None)
            ts = ts[1:]
            quant = "EXACTLY"
        if quant and context != "WORLD":
            raise Unsupported("QUANTIFIER_SCOPE_AMBIGUOUS")
        adjectives = []
        while ts and ts[0].lower in ADJECTIVES:
            adjectives.append(ts[0])
            ts = ts[1:]
        if adjectives and context != "WORLD":
            raise Unsupported("MODIFIER_SCOPE_GAP")
        if len(ts) != 1:
            raise Unsupported("NOUN_PHRASE_GAP", " ".join(t.text for t in original))
        t = ts[0]
        if t.lower in {"he", "she", "it", "they", "him", "her", "them"}:
            # Do not guess gender, salience, or actual-world identity. Resolve only
            # a unique compatible discourse referent in this task's context.
            pool = self.discourse if t.lower in {"he", "she", "him", "her"} else (*self.discourse, *self.mentions)
            def compatible(m):
                person = self.parser.foundation.ontology.is_subclass(m.concept, "Person")
                if t.lower in {"he", "she", "him", "her"}:
                    return person and m.number == "SINGULAR"
                if t.lower == "it":
                    return not person and m.number != "PLURAL"
                return m.number == "PLURAL"
            candidates = list({m.handle: m for m in pool if m.introduced_in == context and compatible(m)}.values())
            if len(candidates) != 1:
                raise Unsupported("COREFERENCE_AMBIGUOUS")
            m = candidates[0]
            return grammatical(ref(m.handle), "SG-INT-030", (t.start, t.end))
        resolution = self.parser.resolve(t.text, self.source.language)
        if len(resolution.concepts) != 1:
            self.unknown.append(t.text)
            raise Unsupported("LEXICAL_AMBIGUITY" if resolution.concepts else "UNKNOWN_WORD", t.text)
        concept = resolution.concepts[0]
        handle = f"W:s{self.unit.start}:{len(self.mentions) + 1}"
        mention = Mention(handle, t.text, concept, (t.start, t.end), "PLURAL" if count and count > 1 or t.lower.endswith("s") else "SINGULAR", count, context)
        self.mentions.append(mention)
        entity = explicit(ref(handle), (t.start, t.end))
        if quant:
            name = f"x{len(self.quantifiers)}"
            entity = explicit(var(name), (t.start, t.end))
        modifiers = []
        for a in adjectives:
            property_, val = ADJECTIVES[a.lower]
            modifiers.append(grammatical(prop(entity, property_, explicit(value(val), (a.start, a.end))), "SG-INT-001", (a.start, a.end)))
        if quant:
            restrictor = grammatical(relate("INSTANCE_OF", entity, explicit(kind(concept), (t.start, t.end))), "SG-INT-001")
            if modifiers:
                restrictor = and_(restrictor, *modifiers)
            self.quantifiers.append((quant, name, restrictor, count))
        else:
            self.properties.extend(modifiers)
        return entity

    def clause(self, ts, context="WORLD", forced_subject=None, nesting=0):
        if nesting > 3 or not ts:
            raise Unsupported("CLAUSE_GAP")
        words = [t.lower for t in ts]
        if any(w in {"every", "all", "each", "no"} for w in words) and any(w in {"a", "an"} for w in words):
            raise Unsupported("QUANTIFIER_SCOPE_AMBIGUOUS")
        if words[0] == "if":
            comma = next((i for i, t in enumerate(ts) if t.text == ","), -1)
            if comma < 0:
                raise Unsupported("CONDITIONAL_GAP")
            return grammatical(cond(self.clause(ts[1:comma], "CONDITIONAL", nesting=nesting+1),
                                    self.clause(ts[comma+1:], "CONDITIONAL", nesting=nesting+1)), "SG-INT-020", (ts[0].start, ts[0].end))
        if "because" in words:
            i = words.index("because")
            effect = self.clause(ts[:i], context, nesting=nesting+1)
            cause = self.clause(ts[i+1:], context, nesting=nesting+1)
            return holds(grammatical(apply("CAUSATION", 1, {"CAUSE": cause, "EFFECT": effect}), "SG-INT-031", (ts[i].start, ts[i].end)))
        if any(t.text in {",", ";", ":", '"', "'", "(", ")"} or t.lower in {"and", "or", "unless", "although", "only"} for t in ts):
            raise Unsupported("SCOPE_GAP")
        # Expand a closed set of contractions without changing original offsets.
        expanded = []
        for t in ts:
            if t.lower in {"didn't", "doesn't", "don't", "isn't", "wasn't", "can't", "won't"}:
                base = {"can't": "can", "won't": "will"}.get(t.lower, t.lower[:-3])
                expanded.extend((Token(base, t.start, t.end), Token("not", t.start, t.end)))
            else:
                expanded.append(t)
        ts = expanded
        words = [t.lower for t in ts]
        vi = next((i for i, w in enumerate(words) if w in VERBS or w in self.parser.aliases), None)
        # Bare 'be open' is a property, not an opening event. Unmarked
        # 'be closed' has a passive/result-state ambiguity we do not erase.
        copular = next((i for i,w in enumerate(words) if w in {'is','are','was','were'}), None)
        if copular is not None and words[copular+1:] == ['open']:
            return self.copula(ts, context)
        if copular is not None and words[copular+1:] == ['closed']:
            raise Unsupported('PASSIVE_STATE_AMBIGUOUS')
        # State predicate and property copulas.
        if vi is None:
            return self.copula(ts, context)
        verb = ts[vi]
        entry = VERBS[self.parser.aliases.get(verb.lower, verb.lower)]
        frame, subject_role, object_role, time, participle = entry
        prefix, tail = ts[:vi], ts[vi+1:]
        trailing_time = tail[-1] if tail and tail[-1].lower in {"yesterday", "today", "tomorrow"} else None
        if trailing_time:
            tail = tail[:-1]
        aux = [t for t in prefix if t.lower in AUX]
        aux_words = tuple(t.lower for t in aux)
        allowed_aux = {(), ('do',), ('does',), ('did',), ('is',), ('are',), ('was',), ('were',),
                       ('has',), ('have',), ('had',), ('will',), ('will','have'), ('may',), ('might',),
                       ('must',), ('can',), ('could',), ('should',), ('may','have'), ('might','have')}
        if aux_words not in allowed_aux:
            raise Unsupported('AUXILIARY_GAP')
        perfect = any(w in {'has','have','had'} for w in aux_words)
        if perfect and verb.lower not in PARTICIPLES:
            raise Unsupported('AUXILIARY_MORPHOLOGY_GAP')
        negs = [t for t in prefix if t.lower in {"not", "never"}]
        subject_tokens = [t for t in prefix if t.lower not in AUX | {"not", "never"}]
        if len(negs) > 1:
            raise Unsupported("NEGATION_SCOPE_GAP")
        if negs:
            context = "NEGATED"
        modal_tokens = [t for t in aux if t.lower in {"may", "might", "must", "can", "could", "should"}]
        if len(modal_tokens) > 1:
            raise Unsupported("MODAL_SCOPE_GAP")
        if modal_tokens:
            context = "HYPOTHETICAL"
        if any(t.lower == "will" for t in aux):
            context = "HYPOTHETICAL"
        subject = forced_subject if forced_subject is not None else self.np(subject_tokens, context)
        if forced_subject is None and not subject_tokens:
            raise Unsupported("SUBJECT_MISSING")
        passive = any(t.lower in {"is", "are", "was", "were"} for t in aux) and participle
        bindings = {}
        if passive:
            if object_role is None or object_role == "CONTENT":
                raise Unsupported("PASSIVE_GAP")
            bindings[object_role] = subject
            by = next((i for i, t in enumerate(tail) if t.lower == "by"), None)
            if by is None:
                bindings[subject_role] = hole()
            else:
                bindings[subject_role] = self.np(tail[by+1:], context)
                tail = tail[:by]
        else:
            bindings[subject_role] = subject
        if frame in {"BELIEVE", "KNOW", "COMMUNICATE"}:
            if tail and tail[0].lower == "that":
                tail = tail[1:]
            bindings["CONTENT"] = self.clause(tail, "CONTENT_OF", nesting=nesting+1)
            tail = []
        elif frame in {"WANT", "ATTEMPT"}:
            if not tail or tail[0].lower != "to":
                raise Unsupported("CONTROL_GAP")
            content = self.clause(tail[1:], "CONTENT_OF", forced_subject=subject, nesting=nesting+1)
            if content.op == "TENSE":
                content = content.args[1]
            if content.op != "HOLDS":
                raise Unsupported("CONTROL_GAP")
            bindings["CONTENT"] = content.args[0]
            tail = []
        elif frame in {"GIVE", "LEND", "RETURN", "OFFER"}:
            recipient_role = "OFFEREE" if frame == "OFFER" else "RECIPIENT"
            to = next((i for i, t in enumerate(tail) if t.lower == "to"), None)
            if to is not None:
                theme = self.np(tail[:to], context) if not passive else subject
                recipient = self.np(tail[to+1:], context)
            elif not passive:
                split = self.np_boundary(tail)
                recipient, theme = self.np(tail[:split], context), self.np(tail[split:], context)
            else:
                if tail:
                    recipient, theme = subject, self.np(tail, context)
                else:
                    recipient, theme = hole(), subject
            bindings[recipient_role] = recipient
            if frame == "OFFER":
                offered = apply("GIVE", 1, {"AGENT": subject, "SOURCE": subject, "RECIPIENT": recipient, "THEME": theme})
                bindings["CONTENT"] = grammatical(offered, "SG-INT-040", (verb.start, verb.end))
            else:
                bindings["THEME"] = theme
                bindings["SOURCE"] = grammatical(bindings.get("AGENT", hole()), "SG-INT-012", (verb.start, verb.end))
            tail = []
        else:
            preps = {"with", "at", "in", "from", "to", "for"}
            i = next((i for i, t in enumerate(tail) if t.lower in preps or t.lower in {"yesterday", "today", "tomorrow"}), len(tail))
            obj, tail = tail[:i], tail[i:]
            if not passive and object_role:
                if not obj:
                    if frame in {"OPEN", "CLOSE", "HEAT", "COOL", "FREEZE"}:
                        bindings.pop(subject_role, None)
                        bindings[object_role] = subject
                    else:
                        bindings[object_role] = hole()
                else:
                    bindings[object_role] = self.np(obj, context)
            elif obj:
                raise Unsupported("EXTRA_ARGUMENT")
        temporal = explicit(time_rel(trailing_time.lower.upper()), (trailing_time.start, trailing_time.end)) if trailing_time else speech_time()
        while tail:
            prep = tail[0]
            if prep.lower in {"yesterday", "today", "tomorrow"} and len(tail) == 1:
                temporal = explicit(time_rel(prep.lower.upper()), (prep.start, prep.end))
                tail = []
                break
            j = next((i for i, t in enumerate(tail[1:], 1) if t.lower in {"with", "at", "in", "from", "to", "for"}), len(tail))
            role = {"WORK": {"at": "WORKPLACE", "in": "WORKPLACE", "for": "EMPLOYER"},
                    "MOVE": {"from": "SOURCE_LOCATION", "to": "DESTINATION_LOCATION"},
                    "COMMERCIAL_TRANSACTION": {"from": "SELLER", "to": "BUYER", "for": "MONEY"},
                    "TREAT": {"with": "INTERVENTION"}, "EXAMINATION": {"with": "INSTRUMENT", "at": "LOCATION"},
                    "SEE": {"with": "INSTRUMENT"}, "PERCEIVE": {"with": "INSTRUMENT"}}.get(frame, {}).get(prep.lower)
            if role is None or role in bindings:
                raise Unsupported("ADJUNCT_GAP")
            bindings[role] = self.np(tail[1:j], context)
            tail = tail[j:]
        # Explicitly represent every missing required role, never invent its filler.
        rf = self.parser.foundation.frames.resolved(frame)
        for role in rf.roles:
            if role.required and role.name not in bindings:
                bindings[role.name] = hole()
        sit = grammatical(apply(frame, rf.frame.version, bindings), "SG-INT-040", (verb.start, verb.end))
        if perfect:
            sit = grammatical(aspect('PERFECT', sit), 'SG-INT-051', (aux[0].start,aux[-1].end))
        proposition = holds(sit)
        if negs:
            proposition = grammatical(not_(proposition), "SG-INT-020", (negs[0].start, negs[0].end))
        if perfect:
            time = 'PAST' if 'had' in aux_words else 'PRESENT'
        if any(t.lower in PAST_AUX for t in aux):
            time = "PAST"
        if any(t.lower == "will" for t in aux):
            time = "FUTURE"
        proposition = grammatical(tense(time, temporal, proposition), "SG-INT-051", (verb.start, verb.end))
        if modal_tokens:
            t = modal_tokens[0]
            force = "NECESSITY" if t.lower in {"must", "should"} else "POSSIBILITY"
            flavors = ("EPISTEMIC", "DEONTIC") if t.lower in {"may", "must", "should"} else ("DYNAMIC", "EPISTEMIC")
            proposition = alt("modal_flavor", [grammatical(modal(force, f, proposition), "SG-INT-021", (t.start, t.end)) for f in flavors])
        return proposition

    def np_boundary(self, ts):
        for i, t in enumerate(ts):
            if len(self.parser.resolve(t.text, self.source.language).concepts) == 1:
                return i + 1
        for i in range(1, len(ts)):
            if ts[i].lower in DETS or ts[i].lower in NUMBERS or ts[i].text.isdigit():
                return i
        return 1 if len(ts) > 1 else len(ts)

    def copula(self, ts, context):
        i = next((i for i, t in enumerate(ts) if t.lower in {"is", "are", "was", "were"}), None)
        if i is None:
            raise Unsupported("FRAME_GAP")
        subject = self.np(ts[:i], context)
        rest = ts[i+1:]
        negative = rest and rest[0].lower == "not"
        if negative:
            rest = rest[1:]
        if len(rest) == 1 and rest[0].lower in {**ADJECTIVES, 'open': ('Openness','OpenState')}:
            pr, val = {**ADJECTIVES, 'open': ('Openness','OpenState')}[rest[0].lower]
            p = grammatical(prop(subject, pr, explicit(value(val), (rest[0].start, rest[0].end))), "SG-INT-001", (rest[0].start, rest[0].end))
        elif len(rest) >= 3 and rest[0].lower == "allergic" and rest[1].lower == "to":
            p = holds(grammatical(apply("ALLERGIC", 1, {"EXPERIENCER": subject, "STIMULUS": self.np(rest[2:], context)}), "SG-INT-040", (rest[0].start, rest[0].end)))
        elif rest and rest[0].lower in {"in", "at"}:
            p = holds(grammatical(apply("LOCATED", 1, {"LOCATED_ENTITY": subject, "LOCATION": self.np(rest[1:], context)}), "SG-INT-040", (rest[0].start, rest[0].end)))
        else:
            obj = self.np(rest, context)
            mention = self.mentions[-1]
            p = grammatical(relate("INSTANCE_OF", subject, explicit(kind(mention.concept), mention.span)), "SG-INT-001", mention.span)
        if negative:
            p = grammatical(not_(p), "SG-INT-020", (ts[i+1].start, ts[i+1].end))
        return grammatical(tense("PAST" if ts[i].lower in {"was", "were"} else "PRESENT", speech_time(), p), "SG-INT-051", (ts[i].start, ts[i].end))

    def arabic(self, ts):
        # Closed morphological paradigms; original Unicode offsets are retained.
        verbs={
            'أكل':('EAT','EATER','FOOD','PAST'),'اكل':('EAT','EATER','FOOD','PAST'),
            'يأكل':('EAT','EATER','FOOD','PRESENT'),'ياكل':('EAT','EATER','FOOD','PRESENT'),
            'فتح':('OPEN','AGENT','UNDERGOER','PAST'),'يفتح':('OPEN','AGENT','UNDERGOER','PRESENT'),
            'أغلق':('CLOSE','AGENT','UNDERGOER','PAST'),'يغلق':('CLOSE','AGENT','UNDERGOER','PRESENT'),
            'عالج':('TREAT','PRACTITIONER','TREATED_ENTITY','PAST'),'يعالج':('TREAT','PRACTITIONER','TREATED_ENTITY','PRESENT'),
            'فحص':('EXAMINATION','EXAMINER','EXAMINED_ENTITY','PAST'),'يفحص':('EXAMINATION','EXAMINER','EXAMINED_ENTITY','PRESENT'),
            'رأى':('SEE','EXPERIENCER','STIMULUS','PAST'),'يرى':('SEE','EXPERIENCER','STIMULUS','PRESENT'),
            'امتلك':('OWN','OWNER','OWNED_ENTITY','PAST'),'يمتلك':('OWN','OWNER','OWNED_ENTITY','PRESENT')}
        def form(token):
            return ''.join(c for c in token.text if not ('\u064b'<=c<='\u0652' or c in {'\u0670','\u0640'}))
        temporal=None
        if ts and form(ts[-1]) in {'أمس','اليوم','غدا','غداً'}:
            temporal=ts[-1];ts=ts[:-1]
        negs=[t for t in ts if form(t) in {'لم','لن'}]
        if len(negs)>1:raise Unsupported('ARABIC_NEGATION_SCOPE_GAP')
        ts=[t for t in ts if t not in negs]
        if len(ts)!=3:raise Unsupported('ARABIC_CONSTRUCTION_GAP')
        vi=next((i for i,t in enumerate(ts) if form(t) in verbs),None)
        if vi not in {0,1}:raise Unsupported('ARABIC_CONSTRUCTION_GAP')
        subject,obj=(ts[1],ts[2]) if vi==0 else (ts[0],ts[2])
        frame,sr,ore,time=verbs[form(ts[vi])]
        if negs:
            if time!='PRESENT' or negs[0].end>ts[vi].start:
                raise Unsupported('ARABIC_NEGATION_MORPHOLOGY_GAP')
            time='FUTURE' if form(negs[0])=='لن' else 'PAST'
        context='HYPOTHETICAL' if time=='FUTURE' else 'NEGATED' if negs else 'WORLD'
        bindings={sr:self.np([subject],context),ore:self.np([obj],context)}
        for role in self.parser.foundation.frames.resolved(frame).roles:
            if role.required and role.name not in bindings:bindings[role.name]=hole()
        sit=grammatical(apply(frame,1,bindings),'SG-INT-040',(ts[vi].start,ts[vi].end))
        proposition=holds(sit)
        if negs:proposition=grammatical(not_(proposition),'SG-INT-020',(negs[0].start,negs[0].end))
        reference=speech_time()
        if temporal:
            relative={'أمس':'yesterday','اليوم':'today','غدا':'tomorrow'}[form(temporal)]
            reference=grammatical(time_rel(relative),'SG-INT-051',(temporal.start,temporal.end))
        return grammatical(tense(time,reference,proposition),'SG-INT-051',(ts[vi].start,ts[vi].end))

    def certificate_steps(self, expr):
        out, seen = [], set()
        def step(typ, rule, spans=(), inputs=(), output=""):
            out.append(CertStep(f"s{len(out)}", typ, rule, Basis.GRAMMATICAL, tuple(spans), tuple(inputs), output))
        for m in self.mentions:
            step(StepType.REFERENT_CREATION, "SG-INT-001", (m.span,), (("referent", m.handle),), m.concept)
        for _, n in walk(expr):
            if n.op == "REF" and n.get("ref") not in {m.handle for m in self.mentions} and n.get("ref") not in seen:
                seen.add(n.get("ref"))
                step(StepType.COREFERENCE, "SG-INT-030", n.ann.spans if n.ann else (), (("referent", n.get("ref")),))
            if n.op == "APPLY":
                step(StepType.FRAME_SELECTION, "SG-INT-040", n.ann.spans if n.ann else (), (("frame", n.get("frame")),), n.get("frame"))
                for role, o, filler in role_entries(n):
                    if filler.op != "HOLE":
                        step(StepType.ROLE_ASSIGNMENT, "SG-INT-012", filler.ann.spans if filler.ann else (), (("frame", n.get("frame")), ("role", f"{role}#{o}")), role)
            elif n.op in {"TENSE", "NOT", "MODAL", "Q", "COND"}:
                rule = {"TENSE": "SG-INT-051", "NOT": "SG-INT-020", "MODAL": "SG-INT-021", "Q": "SG-INT-022", "COND": "SG-INT-020"}[n.op]
                step(StepType.OPERATOR_ATTACHMENT, rule, n.ann.spans if n.ann else (), output=n.op)
        return tuple(out)
