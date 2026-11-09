"""Small deterministic open-world reasoner with explicit premise traces."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from ..core.ids import Ref
from ..grammar.node import role_entries
from ..grammar.serialize import node_from_json


@dataclass(frozen=True)
class Inference:
    relation: str
    subject: str
    object: str
    rule: str
    premises: tuple[str, ...]
    epistemic_status: str = "INFERRED"
    support_cap: str = "SOURCE_ASSERTED"

    def to_json(self):
        return asdict(self)


class KernelReasoner:
    def __init__(self, service, max_steps=20000, max_results=1000):
        if type(max_steps) is not int or type(max_results) is not int or not 1<=max_steps<=1000000 or not 1<=max_results<=100000:raise ValueError('inference budget')
        self.service, self.max_steps, self.max_results = service, max_steps, max_results

    def run(self, view="trusted", scope=None):
        if view not in {"trusted", "source"}:
            raise ValueError("reasoning requires an explicit knowledge view")
        rows = self.service.query(view=view, limit=1000)
        facts, origins = {}, {}
        onto = self.service.foundation.ontology
        with self.service.db.read() as r:
            for row in rows:
                expr = node_from_json(row["expression"])
                for n in self._positive(expr):
                    if n.op == "RELATE" and all(a.op in {"REF", "KIND"} for a in n.args):
                        a, b = (str(a.get("ref") if a.op == "REF" else a.get("concept")) for a in n.args)
                        facts[(n.get("relation"), a, b)] = (row["assertion"],)
                    if n.op == "APPLY":
                        for role, _, f in role_entries(n):
                            if f.op != "REF":
                                continue
                            rid = Ref.parse(f.get("ref"))
                            classes = r.query("SELECT c.canonical_label FROM referent_class rc JOIN concept c ON c.concept_id=rc.concept_id WHERE rc.referent_id=?", (rid.n,))
                            for c in classes:
                                facts[("INSTANCE_OF", str(rid), c[0])] = (row["assertion"],)
        from .entailments import frame_entailments
        state_results=[]
        for row in rows:
            state_results.extend(frame_entailments(node_from_json(row['expression']),self.service.foundation.frames,row['assertion'],
                                 'VERIFIED' if view=='trusted' else 'SOURCE_ASSERTED',limit=max(0,self.max_results-len(state_results))))
            if len(state_results)>=self.max_results:break
        definition_results=[]
        if scope is not None and len(state_results)<self.max_results:
            from ..concepts.definitions import DefinitionStore
            from ..grammar.node import Node
            from ..grammar.serialize import node_to_json
            definitions=DefinitionStore(self.service)
            for (relation, subject, cls), premises in list(facts.items()):
                if relation!='INSTANCE_OF' or not onto.has(cls):continue
                for item in definitions.inherit(cls,scope):
                    def substitute(n):
                        if n.op=='VAR' and n.get('name')=='self':return Node('REF',(),{'ref':subject})
                        return Node(n.op,tuple(substitute(a) for a in n.args),n.params,n.ann)
                    definition_results.append({'expression':node_to_json(substitute(node_from_json(item['expression']))),
                        'premises':list(premises)+[f"DEFINITION:{item['definition']}"], 'rule':'SG-KNW-004',
                        'epistemic_status':'INFERRED','eval_context':'DOMAIN_MODEL','scope':scope})
                    if len(definition_results)+len(state_results)>=self.max_results:break
                if len(definition_results)+len(state_results)>=self.max_results:break
        initial = set(facts)
        todo, results, steps = deque(facts), [], 0
        while todo and steps < self.max_steps and len(results)+len(state_results)+len(definition_results) < self.max_results:
            relation, a, b = todo.popleft()
            steps += 1
            premises = facts[(relation, a, b)]
            derived = []
            if relation == "INSTANCE_OF" and onto.has(b):
                derived.extend(("INSTANCE_OF", a, parent, "SG-KNW-010", premises) for parent in sorted(onto.ancestors(b)))
            if relation == 'INSTANCE_OF' and onto.has(b):
                for edge in self.service.foundation.edges:
                    if edge.relation=='HAS_FUNCTION' and onto.is_subclass(b,edge.src):
                        derived.append(('HAS_FUNCTION',a,edge.tgt,'SG-FRM-005',premises+(f'CONCEPT:{edge.src}',)))
            if relation == 'HAS_FUNCTION' and onto.has(b):
                derived.extend(('HAS_FUNCTION',a,parent,'SG-KNW-010',premises) for parent in sorted(onto.ancestors(b)) if onto.kind_of(parent).value=='FUNCTION')
            rd = self.service.foundation.relations.get(relation)
            if rd and rd.category.value == "LOGICAL":
                if rd.inverse_of:
                    derived.append((rd.inverse_of, b, a, "SG-KNW-011", premises))
                if rd.symmetric:
                    derived.append((relation, b, a, "SG-KNW-012", premises))
                if rd.transitive:
                    # Iterate over a snapshot; open world never infers negation.
                    for (other, x, y), supporting in list(facts.items()):
                        if other == relation and x == b and y != a:
                            derived.append((relation, a, y, "SG-KNW-012", tuple(sorted(set(premises+supporting)))))
            for rel, x, y, rule, proof in derived:
                key = (rel, x, y)
                if key not in facts:
                    facts[key] = proof
                    todo.append(key)
                    results.append(Inference(rel, x, y, rule, proof, support_cap="VERIFIED" if view == "trusted" else "SOURCE_ASSERTED").to_json())
                    if len(results)+len(state_results)+len(definition_results) >= self.max_results:
                        break
        return {"view": view, "inferences": results, "state_entailments":state_results, "definition_entailments":definition_results, "steps": steps, "truncated": bool(todo), "absence_means": "UNKNOWN"}

    def _positive(self, n):
        # Stop at attitudes, negation, modalities, alternatives, hypotheticals,
        # quantifiers, future tense and nested descriptions. They are not facts
        # in the author's actual-world context.
        if n.op in {"ASSERT", "AND"}:
            for a in n.args:
                yield from self._positive(a)
        elif n.op == "TENSE" and n.get("tense") != "FUTURE":
            yield from self._positive(n.args[1])
        elif n.op == "HOLDS" and n.args[0].op in {"APPLY","ASPECT"}:
            ap = n.args[0]
            if ap.op=='ASPECT':ap=ap.args[0]
            if ap.op!='APPLY':return
            if ap.get("frame") not in {"BELIEVE", "KNOW", "WANT", "ATTEMPT", "OFFER", "COMMUNICATE", "CAUSATION"}:
                yield ap
        elif n.op in {"RELATE", "PROPERTY"}:
            yield n
