from __future__ import annotations

import json
from collections import defaultdict

from ..autonomy.panel import AutomatedPanel, Verdict, wilson_upper
from ..autonomy.policy import ActionClass, AutonomyMode, AutonomyPolicy, VerifierClass as VC
from ..config import Config
from ..core.ids import IdSpace
from ..core.values import Component, Outcome
from ..errors import BudgetExceeded, InvariantViolation, PolicyDenied
from ..grammar.node import Node, role_entries, walk
from ..grammar.serialize import canonical_string, node_from_json
from ..interpretation.parser import DeterministicInterpreter, VERBS
from ..storage.registry import IdRegistry
from ..storage.schema import WriterRole as W
from ..util import canonical_json, sha256_hex
from .dsl import RuleProposal


def structural_signature(expr):
    """Typed role topology, preserving operator distinctions and co-occurrence.

    Ignoring instance IDs is a retrieval abstraction, never proof of equivalence.
    """
    ids = {}
    def abstract(n):
        p = n.params_dict()
        if n.op == "REF":
            ids.setdefault(p["ref"], len(ids))
            p["ref"] = f"W:pattern:{ids[p['ref']]+1}"
        return Node(n.op, tuple(abstract(a) for a in n.args), p)
    return sha256_hex(canonical_string(abstract(expr)))


def bounded_match(pattern, target, max_steps=20_000, max_depth=4):
    bindings, steps = {}, 0
    def match(p, t, depth):
        nonlocal steps
        steps += 1
        if steps > max_steps or depth > max_depth:
            raise InvariantViolation("graph matching budget exhausted", "SG-GEN-007")
        if p.op == "VAR":
            if p.sort != t.sort:
                return False
            name = p.get("name")
            if name in bindings:
                return bindings[name] == t
            bindings[name] = t
            return True
        if p.op != t.op or p.params != t.params or len(p.args) != len(t.args):
            return False
        return all(match(a, b, depth+1) for a, b in zip(p.args, t.args))
    return dict(bindings) if match(pattern, target, 0) else None


def analogy(left, right):
    """A transparent proposed mapping. Unshared structure is explicitly retained."""
    def relations(expr):
        return {(n.get("frame"), role) for _, n in walk(expr) if n.op == "APPLY" for role, _, _ in role_entries(n)}
    a, b = relations(left), relations(right)
    return {"status": "CANDIDATE", "shared": sorted(a & b), "unshared_left": sorted(a-b),
            "unshared_right": sorted(b-a), "licenses_equivalence": False}


class LearningEngine:
    def __init__(self, db, config=None):
        self.db, self.config = db, config or Config()
        self.policy = AutonomyPolicy(self.config)

    def discover(self):
        """Bounded batch mining from formally admitted candidates, independent origins only."""
        with self.db.read() as r:
            rows = r.query("SELECT c.*,s.text_hash,s.uri FROM candidate c JOIN source s USING(source_id) WHERE c.lifecycle='VALIDATED_FORMALLY' ORDER BY c.candidate_id DESC LIMIT ?", (self.config["gen_max_candidates"] * 10,))
        count = 0
        with self.db.write(W.CANDIDATE_STORE, W.REGISTRY) as t:
            t.execute("UPDATE provisional SET status='EXPIRED' WHERE status='ACTIVE' AND expires_at<=?", (self.db.clock.now(),))
            t.execute("UPDATE learning_candidate SET stage='DEFERRED' WHERE stage NOT IN ('PROMOTED','REJECTED','DEFERRED') AND expires_at<=?", (self.db.clock.now(),))
            # Group near copies together as a poisoning/independence safeguard.
            clusters = []
            for row in rows:
                from ..core.ids import Ref
                from ..storage.records_store import RecordStore
                from ..runtime import USG
                source = RecordStore().get_source(t, Ref(IdSpace.SOURCE, row["source_id"]))
                words = set(source.text.casefold().split())
                origin = USG._origin(source)
                for old_words, old_origin in clusters:
                    if len(words & old_words) / max(1, len(words | old_words)) >= self.config["near_duplicate_threshold"]:
                        origin = old_origin
                        break
                clusters.append((words, origin))
                expr = node_from_json(json.loads(row["payload"])["expression"])
                sig = structural_signature(expr)
                t.execute("INSERT OR IGNORE INTO pattern_occurrence VALUES(?,?,?,?)", (sig, origin, row["source_id"], row["candidate_id"]))
                origins = t.scalar("SELECT COUNT(*) FROM pattern_occurrence WHERE signature=?", (sig,))
                if origins < self.config["pattern_min_independent_origins"]:
                    continue
                if t.scalar("SELECT COUNT(*) FROM learning_candidate WHERE stage IN ('STRUCTURED','SHADOW')") >= self.config["gen_max_candidates"]:
                    break
                existing = t.one("SELECT candidate_id FROM learning_candidate WHERE signature=?", (sig,))
                if existing:
                    continue
                cid = IdRegistry().allocate(t, IdSpace.CANDIDATE, record_kind="GeneralizationCandidate")
                t.execute("INSERT INTO learning_candidate VALUES(?,?,?,?,?,?,?,?)", (cid.n, sig, ActionClass.CONCEPT_GENERALIZATION.value,
                          canonical_json({"classification": "STRUCTURAL_ABSTRACTION", "independent_origins": origins, "signature": sig,
                                          "world_claim": False, "specifics_preserved": True}), "SHADOW", None, self.db.clock.now(),
                          self.db.clock.now() + 86400*self.config["shadow_candidate_ttl_days"]))
                t.audit(Component.GENERALIZATION_ENGINE, "PATTERN_CANDIDATE", str(cid), "SHADOW_ONLY")
                count += 1
        return {"new_shadow_patterns": count, "scanned": len(rows), "automatic_world_claims": 0}

    def propose(self, proposal):
        p = proposal if isinstance(proposal, RuleProposal) else RuleProposal.from_json(proposal)
        body = canonical_json(p.to_json())
        sig = sha256_hex(body)
        with self.db.write(W.CANDIDATE_STORE, W.REGISTRY) as t:
            row = t.one("SELECT candidate_id FROM learning_candidate WHERE signature=?", (sig,))
            if row:
                return row[0]
            if t.scalar("SELECT COUNT(*) FROM learning_candidate WHERE stage NOT IN ('REJECTED','DEFERRED','PROMOTED')") >= self.config['gen_max_candidates']:
                raise BudgetExceeded("learning candidate capacity exhausted")
            cid = IdRegistry().allocate(t, IdSpace.CANDIDATE, record_kind="RuleProposal")
            t.execute("INSERT INTO learning_candidate VALUES(?,?,?,?,?,?,?,?)", (cid.n, sig, ActionClass.INTERP_RULE.value, body, "STRUCTURED", None,
                      self.db.clock.now(), self.db.clock.now()+86400*self.config["shadow_candidate_ttl_days"]))
            t.audit(Component.PROPOSAL_SERVICE, "RULE_PROPOSED", str(cid), sig)
        return cid.n

    def veto(self, candidate_id, counterexample):
        if not counterexample:
            raise ValueError("counterexample required")
        with self.db.write(W.CANDIDATE_STORE) as t:
            t.execute("UPDATE learning_candidate SET stage='REJECTED',veto=? WHERE candidate_id=?", (counterexample[:2000], candidate_id))
            t.audit(Component.VALIDATOR, "CANDIDATE_VETO", f"CANDIDATE:{candidate_id}", sha256_hex(counterexample))
        with self.db.read() as r:
            bundles = r.query("SELECT bundle_id FROM promotion_bundle WHERE candidate_id=? AND state<>'ROLLED_BACK'", (candidate_id,))
        for row in bundles:
            self.rollback(row[0], "counterexample")

    def stage_rule(self, candidate_id):
        """Automated tests stage a candidate for canary; they cannot activate it."""
        from ..benchmark.corpus import cases, semantic_fingerprint
        from ..core.records import Source
        from ..core.spans import Span
        from ..grammar.typecheck import Typechecker
        from ..validation.validator import Validator, ValidationContext
        with self.db.read() as r:
            row = r.one("SELECT * FROM learning_candidate WHERE candidate_id=?", (candidate_id,))
        if not row or row["veto"] or row["stage"] != "STRUCTURED" or row["action"] != "INTERP_RULE":
            raise PolicyDenied("candidate cannot enter canary")
        if row["expires_at"] <= self.db.clock.now():
            raise PolicyDenied("candidate expired")
        p = RuleProposal.from_json(json.loads(row["payload"]))
        from ..concepts.lexicon import VETTED_VERB_ALIASES
        if VETTED_VERB_ALIASES.get(p.trigger) != p.equivalent_verb:
            with self.db.write(W.CANDIDATE_STORE) as t:
                t.execute("UPDATE learning_candidate SET stage='DEFERRED' WHERE candidate_id=?", (candidate_id,))
                t.audit(Component.VALIDATOR, "NO_LEXICAL_PROOF", str(candidate_id))
            return {"staged": False, "reason": "NO_INDEPENDENT_LEXICAL_PROOF"}
        parser = DeterministicInterpreter(aliases={p.trigger: p.equivalent_verb})
        def parse(text, language="en"):
            return parser.interpret(Source(text, language=language), Span(0, len(text)))
        positive = [parse(t) for t in p.positive]
        valid = all(x.candidate.certificate.outcome is Outcome.RESOLVED for x in positive)
        def formal(x):
            m = {m.handle: m for m in x.mentions}
            return not Validator(ValidationContext(Typechecker(parser.foundation.frames, classes_of=lambda r: [m[r].concept] if r in m else ()),
                                resolves_ref=lambda r: r in m, surface_of=lambda r: [m[r].label] if r in m else [])).validate(x.candidate).failed()
        replay = valid and all(formal(x) for x in positive)
        negatives = all(parse(t).candidate.certificate.outcome is Outcome.UNRESOLVED for t in p.negative)
        contrast = all(semantic_fingerprint(parse(a)) != semantic_fingerprint(parse(b)) for a, b in p.contrastive)
        heldout = all(semantic_fingerprint(parse(c.text, c.language)) == c.expected for c in cases(split="test") if c.outcome == "RESOLVED")
        regression = heldout and negatives
        # Metamorphic alias substitution must preserve the approved verb reading.
        import re
        base = DeterministicInterpreter()
        def substitution_matches(text, interpreted):
            replaced = re.sub(r"\b" + p.trigger + r"\b", p.equivalent_verb, text)
            reference = base.interpret(Source(replaced), Span(0, len(replaced)))
            return semantic_fingerprint(interpreted) == semantic_fingerprint(reference)
        metamorphic = all(substitution_matches(text, x) for text, x in zip(p.positive, positive))
        tests = {VC.DETERMINISTIC_REPLAY: replay, VC.REGRESSION_SUITE: regression, VC.SYNTHETIC_HELDOUT: heldout, VC.METAMORPHIC: contrast and metamorphic}
        verifiers = {cls: (lambda candidate, cls=cls, passed=passed: Verdict(cls, passed, sha256_hex(canonical_json([row["signature"], cls.value, passed])), hard_failure=not passed)) for cls, passed in tests.items()}
        panel = AutomatedPanel(verifiers, self.policy).evaluate(ActionClass.INTERP_RULE, p, rollback_plan=True, canary_complete=True)
        if not panel.approved:
            self.veto(candidate_id, panel.reason)
            return {"staged": False, "panel": panel.to_json()}
        with self.db.write(W.PROMOTION) as t:
            # Check again under lock so an intervening veto cannot be bypassed.
            current = t.one("SELECT stage,veto FROM learning_candidate WHERE candidate_id=?", (candidate_id,))
            if current["stage"] != "STRUCTURED" or current["veto"]:
                raise PolicyDenied("candidate changed during testing")
            cur = t.execute("INSERT INTO promotion_bundle(candidate_id,state,panel,created_at) VALUES(?,'CANARY',?,?)", (candidate_id, canonical_json(panel.to_json()), self.db.clock.now()))
            t.execute("UPDATE learning_candidate SET stage='REVIEWED_SEMANTICALLY' WHERE candidate_id=?", (candidate_id,))
            t.audit(Component.PROMOTION_CONTROLLER, "CANARY_STARTED", str(cur.lastrowid), row["signature"])
            return {"staged": True, "bundle_id": cur.lastrowid, "panel": panel.to_json()}

    def observe_canary(self, bundle_id, *, error=False, observation_key=None):
        with self.db.write(W.PROMOTION) as t:
            row = t.one("SELECT * FROM promotion_bundle WHERE bundle_id=? AND state IN ('CANARY','ACTIVE')", (bundle_id,))
            if not row:
                return "INACTIVE"
            if observation_key is not None:
                if not isinstance(observation_key,str) or not 1<=len(observation_key)<=200:raise ValueError('canary observation identity')
                old=t.one('SELECT error FROM canary_observation WHERE bundle_id=? AND observation_key=?',(bundle_id,observation_key))
                if old:
                    if old[0]!=int(error):raise ValueError('canary observation changed')
                    return row['state']
                t.execute('INSERT INTO canary_observation VALUES(?,?,?)',(bundle_id,observation_key,int(error)))
            candidate = t.one("SELECT expires_at,veto FROM learning_candidate WHERE candidate_id=?", (row["candidate_id"],))
            if candidate["veto"] or (row["state"] == "CANARY" and candidate["expires_at"] <= self.db.clock.now()):
                error = True
            t.execute("UPDATE promotion_bundle SET observations=observations+1,errors=errors+? WHERE bundle_id=?", (int(error), bundle_id))
            n, errors = row["observations"]+1, row["errors"]+int(error)
            if error:
                state = "ROLLED_BACK"
            elif n >= self.config["canary_units"] and wilson_upper(errors, n) <= self.config["canary_error_ub_max"]:
                state = "ACTIVE"
            else:
                state = row["state"]
            t.execute("UPDATE promotion_bundle SET state=? WHERE bundle_id=?", (state, bundle_id))
            if state != row["state"]:
                t.execute("UPDATE learning_candidate SET stage=? WHERE candidate_id=?", ("PROMOTED" if state == "ACTIVE" else "REJECTED", row["candidate_id"]))
                t.audit(Component.PROMOTION_CONTROLLER, state, f"BUNDLE:{bundle_id}")
        if error:
            self.rollback(bundle_id, "canary regression")
        return state

    def rollback(self, bundle_id, reason):
        with self.db.write(W.PROMOTION,W.EVALUATION,W.CANDIDATE_STORE) as t:
            todo, seen = [bundle_id], set()
            while todo:
                bid = todo.pop()
                if bid in seen:
                    continue
                seen.add(bid)
                todo.extend(x[0] for x in t.query("SELECT bundle_id FROM bundle_dependency WHERE dependency=?", (bid,)))
                t.execute("UPDATE promotion_bundle SET state='ROLLED_BACK' WHERE bundle_id=?", (bid,))
                t.execute("UPDATE learning_candidate SET stage='REJECTED',veto=? WHERE candidate_id IN (SELECT candidate_id FROM promotion_bundle WHERE bundle_id=?)", (reason, bid))
                t.execute("UPDATE assertion SET epistemic_status='DISPUTED',lifecycle=CASE WHEN lifecycle='PROMOTED' THEN 'DEPRECATED' ELSE 'DEFERRED' END WHERE assertion_id IN (SELECT assertion_id FROM rule_claim_dependency WHERE bundle_id=?)",(bid,))
                t.audit(Component.PROMOTION_CONTROLLER, "ROLLBACK", f"BUNDLE:{bid}", reason)
        return sorted(seen)

    def active_aliases(self):
        with self.db.read() as r:
            rows = r.query("SELECT c.payload FROM learning_candidate c JOIN promotion_bundle b USING(candidate_id) WHERE b.state='ACTIVE' AND c.stage='PROMOTED' AND c.action='INTERP_RULE' AND c.veto IS NULL ORDER BY b.bundle_id")
        return {p.trigger: p.equivalent_verb for p in (RuleProposal.from_json(json.loads(x[0])) for x in rows)}

    def add_dependency(self, bundle_id, dependency):
        with self.db.write(W.PROMOTION) as t:
            if bundle_id == dependency:
                raise InvariantViolation("cyclic promotion dependency", "SG-LRN-006")
            for bid in (bundle_id, dependency):
                state = t.scalar("SELECT state FROM promotion_bundle WHERE bundle_id=?", (bid,))
                if state not in {"CANARY", "ACTIVE"}:
                    raise PolicyDenied("promotion dependency is not available")
            pending, seen = [dependency], set()
            while pending:
                at = pending.pop()
                if at == bundle_id:
                    raise InvariantViolation("cyclic promotion dependency", "SG-LRN-006")
                if at in seen:
                    continue
                seen.add(at)
                pending.extend(x[0] for x in t.query("SELECT dependency FROM bundle_dependency WHERE bundle_id=?", (at,)))
            t.execute("INSERT OR IGNORE INTO bundle_dependency VALUES(?,?)", (bundle_id,dependency))
            t.audit(Component.PROMOTION_CONTROLLER, "DEPENDENCY_ADDED", f"BUNDLE:{bundle_id}", str(dependency))
