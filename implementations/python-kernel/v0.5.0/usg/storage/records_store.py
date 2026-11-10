"""Persistence of the core records (spec Part 2 §2.3, Part 11 §11.3).

Every method states which writer roles it needs. Invariants are enforced here,
at the persistence boundary, *in addition to* object-level checks and
database CHECK constraints (defence in depth):

  I-02 / SG-FND-001   every reference must resolve (registry)
  I-08                assertion needs a source or an authorized origin
  I-09                sources immutable (trigger), text hash verified on read
  SG-EVD-003/009      status changes only through check_epistemic_transition
  SG-LRN-002          lifecycle changes only by the component that owns the stage
  SG-KNW-002/011/012  weights only on ASSOCIATIVE edges with a scoring model; no inverse
                      duplicates; declared logical properties and acyclicity enforced
  SG-FRM-006          frame versions immutable (trigger); instances pin (frame, version)
  VC-S05..S08         bindings validated against the frame library before they are stored
"""

from __future__ import annotations

import dataclasses
import json
import zlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from ..core.ids import IdSpace, Ref
from ..core.kinds import SemKind
from ..core.records import (Anchor, Assertion, Concept, ContentType, Filler, FrameInstance, IntroducedIn, Literal,
                            Referent, RoleBinding, Source)
from ..core.spans import Span
from ..core.values import (Basis, CommitmentKind, Component, EpistemicStatus, EvalContextKind, FillerKind, Genericity,
                           IntroducedInKind, Lifecycle, Number, Origin, ReferentScope, Sensitivity, SourceType,
                           TrustTier, ValueState)
from ..errors import InvariantViolation, PolicyDenied, StorageError
from ..model.frames import FrameDef, FrameLibrary
from ..model.relations import RelationDef, check_edge
from ..util import canonical_json, sha256_hex
from .database import ReadTxn, WriteTxn
from .registry import IdRegistry
from .schema import WriterRole

_DICT_ROLES = frozenset({WriterRole.PROMOTION, WriterRole.RELEASE})


@dataclass(frozen=True)
class Edge:
    src: int
    relation: str
    tgt: int
    domain: str
    qualifiers: Mapping[str, Any]
    weight: float | None
    weight_model: str | None
    status: str


class _LazyAdj:
    """Adjacency of one relation, read lazily from the database (for cycle checks)."""

    def __init__(self, r: ReadTxn, relation_id: int):
        self._r, self._rid = r, relation_id

    def get(self, n: int, default: Iterable[int] = ()) -> set[int]:
        rows = self._r.query(
            "SELECT tgt_id FROM relation_edge WHERE src_id=? AND relation_id=? AND status='ACTIVE'", (n, self._rid))
        return {int(x[0]) for x in rows} or set(default)


def _ref(space: str, n: int) -> Ref:
    return Ref(IdSpace(space), int(n))


class RecordStore:
    def __init__(self, registry: IdRegistry | None = None):
        self.registry = registry or IdRegistry()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _require_dict_writer(txn: WriteTxn) -> None:
        if not (txn.roles & _DICT_ROLES):
            raise PolicyDenied("dictionary tables are written only by PROMOTION or RELEASE (install)", "SG-GOV-008")
        txn.require_role(WriterRole.REGISTRY)

    def _must_resolve(self, r: ReadTxn, ref: Ref | None, what: str) -> None:
        if ref is None:
            return
        if self.registry.resolve_status(r, ref) == "UNKNOWN":
            raise InvariantViolation(f"{what}: reference {ref} does not resolve", "SG-FND-001")

    # ------------------------------------------------------------------ sources (PROVENANCE + REGISTRY)
    def add_source(self, txn: WriteTxn, src: Source, *, idempotent: bool = True) -> Source:
        txn.require_role(WriterRole.PROVENANCE)
        txn.require_role(WriterRole.REGISTRY)
        key = None
        if idempotent:
            meta = canonical_json({"u": src.uri, "a": src.anchor.to_json() if src.anchor else None})
            key = "source:" + sha256_hex(f"{src.text_hash}|{src.language}|{src.type.value}|{meta}")
        ref = self.registry.allocate(txn, IdSpace.SOURCE, record_kind="Source", status="REGISTERED", idempotency_key=key)
        exists = txn.one("SELECT 1 FROM source WHERE source_id=?", (ref.n,))
        if not exists:
            txn.execute(
                "INSERT INTO source(source_id,type,language,text_hash,anchor,trust_tier,sensitivity,genre,uri,stored_text,"
                "text_codec,text_len,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ref.n, src.type.value, src.language, src.text_hash,
                 json.dumps(src.anchor.to_json()) if src.anchor else None, src.trust_tier.value, src.sensitivity.value,
                 src.genre, src.uri, zlib.compress(src.text.encode("utf-8"), 6), "zlib", len(src.text),
                 float(txn.clock.now())))
        return dataclasses.replace(src, ref=ref)

    def get_source(self, r: ReadTxn, ref: Ref) -> Source:
        row = r.one("SELECT * FROM source WHERE source_id=?", (ref.n,))
        if row is None:
            raise StorageError(f"unknown source {ref}")
        text = zlib.decompress(row["stored_text"]).decode("utf-8")
        a = json.loads(row["anchor"]) if row["anchor"] else None
        return Source(text=text, language=row["language"], type=SourceType(row["type"]),
                      trust_tier=TrustTier(row["trust_tier"]), sensitivity=Sensitivity(row["sensitivity"]),
                      genre=row["genre"], anchor=Anchor(**a) if a else None, uri=row["uri"], ref=ref,
                      text_hash=row["text_hash"])  # constructor re-verifies the hash (tamper evidence)

    def set_trust_tier(self, txn: WriteTxn, ref: Ref, new: TrustTier, *, probation_passed: bool = False) -> None:
        """TRUSTED is never reachable at runtime (install-time configuration only)."""
        txn.require_role(WriterRole.PROVENANCE)
        row = txn.one("SELECT trust_tier FROM source WHERE source_id=?", (ref.n,))
        if row is None:
            raise StorageError(f"unknown source {ref}")
        old = TrustTier(row["trust_tier"])
        if new is TrustTier.TRUSTED:
            raise PolicyDenied("TRUSTED is install-time configuration and cannot be granted at runtime", "SG-FND-005")
        if new is TrustTier.STANDARD and old is TrustTier.QUARANTINE and not probation_passed:
            raise PolicyDenied("QUARANTINE -> STANDARD requires automatic probation", "SG-SEC-003")
        txn.execute("UPDATE source SET trust_tier=? WHERE source_id=?", (new.value, ref.n))
        txn.audit(Component.CONTROLLER, "TIER_CHANGED", str(ref), f"{old.value}->{new.value}")

    # ------------------------------------------------------------------ domains, concepts
    def add_domain(self, txn: WriteTxn, name: str, parent: str | None = None) -> int:
        self._require_dict_writer(txn)
        row = txn.one("SELECT domain_id FROM domain WHERE name=?", (name,))
        if row:
            return int(row["domain_id"])
        ref = self.registry.allocate(txn, IdSpace.DOMAIN, record_kind="Domain", status="PROMOTED", idempotency_key=f"domain:{name}")
        pid = txn.scalar("SELECT domain_id FROM domain WHERE name=?", (parent,)) if parent else None
        txn.execute("INSERT INTO domain(domain_id,name,parent_domain) VALUES(?,?,?)", (ref.n, name, pid))
        return ref.n

    def domain_id(self, r: ReadTxn, name: str) -> int | None:
        v = r.scalar("SELECT domain_id FROM domain WHERE name=?", (name,))
        return int(v) if v is not None else None

    def add_concept(self, txn: WriteTxn, concept: Concept, *, domains: Sequence[str] = (), value_domain: Ref | None = None,
                    origin: str = "CURATED", doc: str = "", idempotency_key: str | None = None) -> Ref:
        self._require_dict_writer(txn)
        if concept.lifecycle is not Lifecycle.PROMOTED:
            raise InvariantViolation("dictionary tables hold only PROMOTED concepts (candidates live in the candidate store)", "SG-LRN-002")
        if concept.ref is not None and concept.ref.is_provisional:
            raise InvariantViolation("provisional concepts never enter the dictionary (I-07)", "I-07")
        if value_domain is not None:
            vd = txn.one("SELECT sem_kind FROM concept WHERE concept_id=?", (value_domain.n,))
            if vd is None or vd["sem_kind"] != SemKind.VALUE.value:
                raise InvariantViolation("value_domain must be an existing VALUE concept", "I-11")
        ref = self.registry.allocate(txn, IdSpace.CONCEPT, record_kind="Concept", sem_kind=concept.kind.value,
                                     status="PROMOTED", version=concept.version, idempotency_key=idempotency_key)
        if txn.one("SELECT 1 FROM concept WHERE concept_id=?", (ref.n,)):
            return ref  # idempotent re-proposal
        txn.execute(
            "INSERT INTO concept(concept_id,sem_kind,canonical_label,definition_complete,lifecycle,version,grammar_version,"
            "ontology_release,origin,value_domain,doc) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (ref.n, concept.kind.value, concept.canonical_label, int(concept.definition_complete), concept.lifecycle.value,
             concept.version, concept.grammar_version, concept.ontology_release, origin,
             value_domain.n if value_domain else None, doc))
        for i, d in enumerate(domains):
            did = txn.scalar("SELECT domain_id FROM domain WHERE name=?", (d,))
            if did is None:
                raise InvariantViolation(f"unknown domain {d!r}", "SG-FND-001")
            txn.execute("INSERT INTO concept_domain(concept_id,domain_id,is_primary) VALUES(?,?,?)", (ref.n, did, 1 if i == 0 else 0))
        return ref

    def set_value_domain(self, txn: WriteTxn, concept: Ref, value_domain: Ref) -> None:
        self._require_dict_writer(txn)
        txn.execute("UPDATE concept SET value_domain=? WHERE concept_id=?", (value_domain.n, concept.n))

    def get_concept(self, r: ReadTxn, ref: Ref) -> Concept:
        row = r.one("SELECT * FROM concept WHERE concept_id=?", (ref.n,))
        if row is None:
            raise StorageError(f"unknown concept {ref}")
        return self._concept_from_row(row)

    @staticmethod
    def _concept_from_row(row) -> Concept:
        return Concept(kind=SemKind(row["sem_kind"]), canonical_label=row["canonical_label"],
                       definition_complete=bool(row["definition_complete"]), lifecycle=Lifecycle(row["lifecycle"]),
                       version=int(row["version"]), grammar_version=row["grammar_version"],
                       ontology_release=row["ontology_release"], ref=Ref(IdSpace.CONCEPT, int(row["concept_id"])))

    def find_concepts(self, r: ReadTxn, label: str) -> list[Concept]:
        return [self._concept_from_row(x) for x in r.query(
            "SELECT * FROM concept WHERE canonical_label=? ORDER BY concept_id", (label,))]

    def concept_domains(self, r: ReadTxn, ref: Ref) -> list[str]:
        return [x["name"] for x in r.query(
            "SELECT d.name FROM concept_domain cd JOIN domain d ON d.domain_id=cd.domain_id WHERE cd.concept_id=? "
            "ORDER BY cd.is_primary DESC, d.name", (ref.n,))]

    # ------------------------------------------------------------------ relations and edges
    def add_relation_def(self, txn: WriteTxn, rel: RelationDef) -> Ref:
        self._require_dict_writer(txn)
        ref = self.registry.allocate(txn, IdSpace.RELATION, record_kind="Relation", status="PROMOTED",
                                     idempotency_key=f"relation:{rel.name}")
        if not txn.one("SELECT 1 FROM relation_def WHERE relation_id=?", (ref.n,)):
            txn.execute("INSERT INTO relation_def(relation_id,name,category,body,version,status) VALUES(?,?,?,?,?,?)",
                        (ref.n, rel.name, rel.category.value, canonical_json(rel.to_json()), rel.version, "ACTIVE"))
        return ref

    def get_relation_def(self, r: ReadTxn, name: str) -> tuple[Ref, RelationDef]:
        row = r.one("SELECT relation_id, body FROM relation_def WHERE name=?", (name,))
        if row is None:
            raise StorageError(f"unknown relation {name!r}")
        return Ref(IdSpace.RELATION, int(row["relation_id"])), RelationDef.from_json(json.loads(row["body"]))

    def relation_defs(self, r: ReadTxn) -> dict[str, RelationDef]:
        return {x["name"]: RelationDef.from_json(json.loads(x["body"])) for x in r.query(
            "SELECT name, body FROM relation_def ORDER BY relation_id")}

    def add_edge(self, txn: WriteTxn, src: Ref, relation: str, tgt: Ref, domain: str, *, qualifiers: Mapping[str, Any] | None = None,
                 weight: float | None = None, weight_model: str | None = None) -> bool:
        """Insert an edge after enforcing the relation's declared properties. Returns False if it already exists."""
        self._require_dict_writer(txn)
        rel_ref, rel = self.get_relation_def(txn, relation)
        for ep, what in ((src, "source"), (tgt, "target")):
            if ep.space is not IdSpace.CONCEPT:
                raise InvariantViolation(f"edge {what} {ep} must be a concept", "VC-T05")
            if self.registry.resolve_status(txn, ep) != "ACTIVE":
                raise InvariantViolation(f"edge {what} {ep} is not an active concept", "SG-FND-001")
        kinds = {x["concept_id"]: x["sem_kind"] for x in txn.query(
            "SELECT concept_id, sem_kind FROM concept WHERE concept_id IN (?,?)", (src.n, tgt.n))}
        if rel.domain_kind and kinds.get(src.n) != rel.domain_kind.value:
            raise InvariantViolation(f"{relation}: domain kind {rel.domain_kind.value} required", "VC-T05")
        if rel.range_kind and kinds.get(tgt.n) != rel.range_kind.value:
            raise InvariantViolation(f"{relation}: range kind {rel.range_kind.value} required", "VC-T05")
        did = txn.scalar("SELECT domain_id FROM domain WHERE name=?", (domain,))
        if did is None:
            raise InvariantViolation(f"unknown domain {domain!r}", "SG-FND-001")
        if weight is not None and not weight_model:
            raise InvariantViolation("a weight must record the scoring model that produced it", "SG-KNW-002")
        if txn.one("SELECT 1 FROM relation_edge WHERE src_id=? AND relation_id=? AND tgt_id=? AND domain_id=?",
                   (src.n, rel_ref.n, tgt.n, did)):
            return False
        err = check_edge(rel, src.n, tgt.n, _LazyAdj(txn, rel_ref.n), weight)
        if err:
            raise InvariantViolation(err[1], err[0])
        if rel.symmetric and txn.one("SELECT 1 FROM relation_edge WHERE src_id=? AND relation_id=? AND tgt_id=?", (tgt.n, rel_ref.n, src.n)):
            raise InvariantViolation(f"{relation} is symmetric: the reverse edge already stores this fact", "SG-KNW-011")
        if rel.inverse_of:
            inv_ref, _ = self.get_relation_def(txn, rel.inverse_of)
            if txn.one("SELECT 1 FROM relation_edge WHERE src_id=? AND relation_id=? AND tgt_id=?", (tgt.n, inv_ref.n, src.n)):
                raise InvariantViolation(f"inverse {rel.inverse_of} edge exists: derived inverses are never stored twice", "SG-KNW-011")
        pd = {x["concept_id"]: x["domain_id"] for x in txn.query(
            "SELECT concept_id, domain_id FROM concept_domain WHERE is_primary=1 AND concept_id IN (?,?)", (src.n, tgt.n))}
        xdom = int(src.n in pd and tgt.n in pd and pd[src.n] != pd[tgt.n])
        txn.execute(
            "INSERT INTO relation_edge(src_id,relation_id,tgt_id,domain_id,xdom,qualifiers,weight,weight_model) VALUES(?,?,?,?,?,?,?,?)",
            (src.n, rel_ref.n, tgt.n, did, xdom, canonical_json(dict(qualifiers or {})), weight, weight_model))
        return True

    def _edges(self, r: ReadTxn, where: str, params: Sequence[Any]) -> list[Edge]:
        rows = r.query(
            "SELECT e.src_id, rd.name AS rel, e.tgt_id, d.name AS dom, e.qualifiers, e.weight, e.weight_model, e.status "
            "FROM relation_edge e JOIN relation_def rd ON rd.relation_id=e.relation_id JOIN domain d ON d.domain_id=e.domain_id "
            f"WHERE {where} ORDER BY e.src_id, e.relation_id, e.tgt_id", params)
        return [Edge(int(x["src_id"]), x["rel"], int(x["tgt_id"]), x["dom"], json.loads(x["qualifiers"]), x["weight"],
                     x["weight_model"], x["status"]) for x in rows]

    def edges_from(self, r: ReadTxn, src: Ref, relation: str | None = None) -> list[Edge]:
        if relation is None:
            return self._edges(r, "e.src_id=?", (src.n,))
        return self._edges(r, "e.src_id=? AND rd.name=?", (src.n, relation))

    def edges_to(self, r: ReadTxn, tgt: Ref, relation: str | None = None) -> list[Edge]:
        """Inverse lookups use the target index: inverses are derived, never stored (SG-KNW-011)."""
        if relation is None:
            return self._edges(r, "e.tgt_id=?", (tgt.n,))
        return self._edges(r, "e.tgt_id=? AND rd.name=?", (tgt.n, relation))

    def all_edges(self, r: ReadTxn) -> list[Edge]:
        return self._edges(r, "1=1", ())

    # ------------------------------------------------------------------ frames
    def add_frame(self, txn: WriteTxn, lib: FrameLibrary, name: str, concept_refs: Mapping[str, Ref],
                  frame_refs: dict[str, Ref]) -> Ref:
        """Persist one frame version. Parents must already be persisted. Frame ids persist across versions."""
        self._require_dict_writer(txn)
        rf = lib.resolved(name)
        f = rf.frame
        existing = txn.scalar("SELECT frame_id FROM frame_def WHERE name=? LIMIT 1", (name,))
        if existing is None:
            ref = self.registry.allocate(txn, IdSpace.FRAME, record_kind="Frame", status="PROMOTED", version=f.version,
                                         idempotency_key=f"frame:{name}")
        else:
            ref = Ref(IdSpace.FRAME, int(existing))
            top = int(txn.scalar("SELECT MAX(frame_version) FROM frame_def WHERE frame_id=?", (ref.n,)))
            if f.version <= top:
                raise InvariantViolation(f"frame {name} version {f.version} must exceed stored version {top}", "SG-FRM-006")
        txn.execute(
            "INSERT INTO frame_def(frame_id,frame_version,name,layer,authority,situation_kind,abstract,kernel,status,"
            "content_hash,n_roles,body) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref.n, f.version, name, f.layer, f.authority.value, f.situation_kind.value, int(f.abstract), int(f.kernel),
             "PROMOTED", f.content_hash(), len(rf.roles), canonical_json(f.to_json())))
        for r in rf.roles:
            cref = None
            if r.cls is not None:
                cref = concept_refs.get(r.cls)
                if cref is None:
                    raise InvariantViolation(f"{name}.{r.name}: class {r.cls!r} has no persisted concept", "SG-FND-001")
            txn.execute(
                "INSERT INTO frame_role(frame_id,frame_version,role_index,name,tier,parent_role,requiredness,card_min,card_max,"
                "expected_kind,expected_class,origin_frame) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (ref.n, f.version, r.index, r.name, r.spec.tier, r.spec.parent_role, r.spec.requiredness.value,
                 r.spec.card_min, r.spec.card_max, r.spec.expected_kind.value, cref.n if cref else None, r.origin))
        for link in f.parents:
            pref = frame_refs.get(link.parent)
            if pref is None:
                raise InvariantViolation(f"{name}: parent frame {link.parent} must be persisted first", "SG-FND-001")
            txn.execute(
                "INSERT INTO frame_parent(frame_id,frame_version,parent_frame_id,parent_version,link_kind,role_map) VALUES(?,?,?,?,?,?)",
                (ref.n, f.version, pref.n, lib.get(link.parent).version, link.kind.value, canonical_json([list(x) for x in link.role_map])))
        frame_refs[name] = ref
        return ref

    def frame_ref(self, r: ReadTxn, name: str, version: int | None = None) -> tuple[Ref, int] | None:
        row = (r.one("SELECT frame_id, frame_version FROM frame_def WHERE name=? AND frame_version=?", (name, version))
               if version is not None else
               r.one("SELECT frame_id, frame_version FROM frame_def WHERE name=? ORDER BY frame_version DESC LIMIT 1", (name,)))
        return (Ref(IdSpace.FRAME, int(row["frame_id"])), int(row["frame_version"])) if row else None

    def frame_name(self, r: ReadTxn, frame_id: int, version: int) -> str | None:
        return r.scalar("SELECT name FROM frame_def WHERE frame_id=? AND frame_version=?", (frame_id, version))

    def load_frame_defs(self, r: ReadTxn) -> list[FrameDef]:
        return [FrameDef.from_json(json.loads(x["body"])) for x in r.query(
            "SELECT body FROM frame_def ORDER BY frame_id, frame_version")]

    # ------------------------------------------------------------------ referents, instances (CANDIDATE_STORE + REGISTRY)
    def add_referent(self, txn: WriteTxn, ref_: Referent) -> Ref:
        txn.require_role(WriterRole.CANDIDATE_STORE)
        txn.require_role(WriterRole.REGISTRY)
        if ref_.source is None:
            raise InvariantViolation("a stored referent needs its source", "I-08")
        self._must_resolve(txn, ref_.source, "referent source")
        for c in ref_.instance_of:
            self._must_resolve(txn, c, "referent class")
        self._must_resolve(txn, ref_.introduced_in.ref, "introduced_in")
        ref = self.registry.allocate(txn, IdSpace.REFERENT, record_kind="Referent", sem_kind=ref_.kind.value)
        card = json.dumps(list(ref_.cardinality) if isinstance(ref_.cardinality, tuple) else ref_.cardinality) \
            if ref_.cardinality is not None else None
        txn.execute(
            "INSERT INTO referent(referent_id,source_id,sem_kind,number,cardinality,genericity,scope,introduced_kind,"
            "introduced_space,introduced_id,individual_ids,span_start,span_end) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref.n, ref_.source.n, ref_.kind.value, ref_.number.value, card, ref_.genericity.value, ref_.scope.value,
             ref_.introduced_in.kind.value, ref_.introduced_in.ref.space.value if ref_.introduced_in.ref else None,
             ref_.introduced_in.ref.n if ref_.introduced_in.ref else None, json.dumps(list(ref_.individual_ids)),
             ref_.span.start if ref_.span else None, ref_.span.end if ref_.span else None))
        for c in ref_.instance_of:
            txn.execute("INSERT INTO referent_class(referent_id,concept_space,concept_id) VALUES(?,?,?)", (ref.n, c.space.value, c.n))
        return ref

    def get_referent(self, r: ReadTxn, ref: Ref) -> Referent:
        row = r.one("SELECT * FROM referent WHERE referent_id=?", (ref.n,))
        if row is None:
            raise StorageError(f"unknown referent {ref}")
        classes = tuple(_ref(x["concept_space"], x["concept_id"]) for x in r.query(
            "SELECT concept_space, concept_id FROM referent_class WHERE referent_id=? ORDER BY concept_space, concept_id", (ref.n,)))
        card = json.loads(row["cardinality"]) if row["cardinality"] is not None else None
        if isinstance(card, list):
            card = tuple(card)
        intro_ref = _ref(row["introduced_space"], row["introduced_id"]) if row["introduced_id"] is not None else None
        return Referent(
            kind=SemKind(row["sem_kind"]), instance_of=classes, number=Number(row["number"]), cardinality=card,
            genericity=Genericity(row["genericity"]), scope=ReferentScope(row["scope"]),
            introduced_in=IntroducedIn(IntroducedInKind(row["introduced_kind"]), intro_ref),
            individual_ids=tuple(json.loads(row["individual_ids"])), source=Ref(IdSpace.SOURCE, int(row["source_id"])),
            span=Span(row["span_start"], row["span_end"]) if row["span_start"] is not None else None, ref=ref)

    def add_frame_instance(self, txn: WriteTxn, inst: FrameInstance, lib: FrameLibrary) -> Ref:
        txn.require_role(WriterRole.CANDIDATE_STORE)
        txn.require_role(WriterRole.REGISTRY)
        row = txn.one("SELECT name, content_hash FROM frame_def WHERE frame_id=? AND frame_version=?",
                      (inst.frame.n, inst.frame_version))
        if row is None:
            raise InvariantViolation(f"frame {inst.frame} v{inst.frame_version} is not persisted", "VC-S05")
        name = row["name"]
        if lib.get(name).content_hash() != row["content_hash"]:
            raise InvariantViolation(f"frame library differs from the stored definition of {name} v{inst.frame_version}", "I-12")
        issues = lib.validate_bindings(name, inst.bindings)
        if issues:
            raise InvariantViolation(f"{issues[0].message} (+{len(issues) - 1} more)" if len(issues) > 1 else issues[0].message,
                                     issues[0].code)
        self._must_resolve(txn, inst.source, "instance source")
        for b in inst.bindings:
            if b.filler is not None and b.filler.ref is not None:
                self._must_resolve(txn, b.filler.ref, f"filler of {b.role}")
        ref = self.registry.allocate(txn, IdSpace.INSTANCE, record_kind="FrameInstance", sem_kind="EVENT")
        txn.execute("INSERT INTO frame_instance(instance_id,frame_id,frame_version,source_id,certificate_id) VALUES(?,?,?,?,?)",
                    (ref.n, inst.frame.n, inst.frame_version, inst.source.n if inst.source else None,
                     inst.certificate.n if inst.certificate else None))
        rf = lib.resolved(name)
        for b in inst.bindings:
            f = b.filler
            lit = None
            if f is not None and f.literal is not None:
                lit = canonical_json({"value": f.literal.value, "value_type": f.literal.value_type, "unit": f.literal.unit})
            txn.execute(
                "INSERT INTO binding(instance_id,role_index,role_name,ord,value_state,basis,filler_kind,filler_space,filler_id,"
                "literal,span_start,span_end,rule) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ref.n, rf.index[b.role], b.role, b.ord, b.value_state.value, b.basis.value if b.basis else None,
                 f.kind.value if f else None, f.ref.space.value if f and f.ref else None, f.ref.n if f and f.ref else None,
                 lit, b.span.start if b.span else None, b.span.end if b.span else None, b.rule))
        return ref

    def get_frame_instance(self, r: ReadTxn, ref: Ref) -> FrameInstance:
        row = r.one("SELECT * FROM frame_instance WHERE instance_id=?", (ref.n,))
        if row is None:
            raise StorageError(f"unknown frame instance {ref}")
        bindings = []
        for b in r.query("SELECT * FROM binding WHERE instance_id=? ORDER BY role_index, ord", (ref.n,)):
            filler = None
            if b["filler_kind"] is not None:
                if b["literal"] is not None:
                    d = json.loads(b["literal"])
                    filler = Filler(FillerKind(b["filler_kind"]), literal=Literal(d["value"], d["value_type"], d["unit"]))
                else:
                    filler = Filler(FillerKind(b["filler_kind"]), ref=_ref(b["filler_space"], b["filler_id"]))
            bindings.append(RoleBinding(
                role=b["role_name"], value_state=ValueState(b["value_state"]),
                basis=Basis(b["basis"]) if b["basis"] else None, filler=filler,
                span=Span(b["span_start"], b["span_end"]) if b["span_start"] is not None else None,
                rule=b["rule"], ord=int(b["ord"])))
        return FrameInstance(
            frame=Ref(IdSpace.FRAME, int(row["frame_id"])), frame_version=int(row["frame_version"]),
            bindings=tuple(bindings), source=Ref(IdSpace.SOURCE, int(row["source_id"])) if row["source_id"] else None,
            certificate=Ref(IdSpace.CERTIFICATE, int(row["certificate_id"])) if row["certificate_id"] else None, ref=ref)

    # ------------------------------------------------------------------ assertions
    def add_assertion(self, txn: WriteTxn, a: Assertion) -> Ref:
        txn.require_role(WriterRole.CANDIDATE_STORE)
        txn.require_role(WriterRole.REGISTRY)
        if a.lifecycle not in (Lifecycle.DISCOVERED, Lifecycle.STRUCTURED):
            raise InvariantViolation("a new assertion enters at DISCOVERED/STRUCTURED; later stages are earned", "SG-LRN-002")
        if a.epistemic_status not in (EpistemicStatus.SOURCE_ASSERTED, EpistemicStatus.INFERRED):
            raise InvariantViolation("a new assertion is SOURCE_ASSERTED or INFERRED, never VERIFIED/DISPUTED/UNKNOWN", "SG-EVD-009")
        self._must_resolve(txn, a.content, "assertion content")
        self._must_resolve(txn, a.source, "assertion source")
        self._must_resolve(txn, a.attributed_to, "attributed_to")
        ref = self.registry.allocate(txn, IdSpace.ASSERTION, record_kind="Assertion", status=a.lifecycle.value)
        txn.execute(
            "INSERT INTO assertion(assertion_id,content_type,content_space,content_id,origin,epistemic_status,commitment,"
            "attributed_space,attributed_id,eval_context,eval_context_name,definition_ref,alt_group,source_id,evidence_id,"
            "lifecycle,grammar_version,ontology_release) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref.n, a.content_type.value, a.content.space.value, a.content.n, a.origin.value, a.epistemic_status.value,
             a.commitment.value, a.attributed_to.space.value if a.attributed_to else None,
             a.attributed_to.n if a.attributed_to else None, a.eval_context.value, a.eval_context_name,
             str(a.definition_ref) if a.definition_ref else None, a.alt_group, a.source.n if a.source else None,
             a.evidence.n if a.evidence else None, a.lifecycle.value, a.grammar_version, a.ontology_release))
        return ref

    def get_assertion(self, r: ReadTxn, ref: Ref) -> Assertion:
        x = r.one("SELECT * FROM assertion WHERE assertion_id=?", (ref.n,))
        if x is None:
            raise StorageError(f"unknown assertion {ref}")
        return Assertion(
            content_type=ContentType(x["content_type"]), content=_ref(x["content_space"], x["content_id"]),
            origin=Origin(x["origin"]), epistemic_status=EpistemicStatus(x["epistemic_status"]),
            commitment=CommitmentKind(x["commitment"]),
            attributed_to=_ref(x["attributed_space"], x["attributed_id"]) if x["attributed_id"] is not None else None,
            eval_context=EvalContextKind(x["eval_context"]), eval_context_name=x["eval_context_name"],
            definition_ref=Ref.parse(x["definition_ref"]) if x["definition_ref"] else None, alt_group=x["alt_group"],
            source=Ref(IdSpace.SOURCE, int(x["source_id"])) if x["source_id"] is not None else None,
            evidence=Ref(IdSpace.EVIDENCE, int(x["evidence_id"])) if x["evidence_id"] is not None else None,
            lifecycle=Lifecycle(x["lifecycle"]), grammar_version=x["grammar_version"],
            ontology_release=x["ontology_release"], ref=ref)

    def attach_evidence(self, txn: WriteTxn, ref: Ref, evidence: Ref) -> None:
        txn.require_role(WriterRole.CANDIDATE_STORE)
        a = self.get_assertion(txn, ref)
        if a.lifecycle not in (Lifecycle.DISCOVERED, Lifecycle.STRUCTURED):
            raise InvariantViolation("evidence is attached before validation", "SG-EVD-001")
        self._must_resolve(txn, evidence, "evidence")
        txn.execute("UPDATE assertion SET evidence_id=? WHERE assertion_id=?", (evidence.n, ref.n))

    def set_assertion_status(self, txn: WriteTxn, ref: Ref, new: EpistemicStatus,
                             actor: Component = Component.EVALUATION_PROCESS) -> Assertion:
        """Axis D change. Only the evaluation process may cause it (SG-EVD-003/009)."""
        txn.require_role(WriterRole.EVALUATION)
        a = self.get_assertion(txn, ref)
        updated = a.with_status(new, actor)  # raises on forbidden transitions
        txn.execute("UPDATE assertion SET epistemic_status=? WHERE assertion_id=?", (new.value, ref.n))
        txn.audit(actor, "STATUS_CHANGED", str(ref), f"{a.epistemic_status.value}->{new.value}")
        return updated

    def set_assertion_stage(self, txn: WriteTxn, ref: Ref, new: Lifecycle, actor: Component) -> Assertion:
        """Axis C change. The component must own the target stage (SG-LRN-002)."""
        a = self.get_assertion(txn, ref)
        updated = a.with_stage(new, actor)  # raises on forbidden transitions / missing evidence
        if new is Lifecycle.PROMOTED:
            txn.require_role(WriterRole.PROMOTION)
        elif not (txn.roles & {WriterRole.CANDIDATE_STORE, WriterRole.PROMOTION}):
            raise PolicyDenied("lifecycle changes are written by the candidate store or the promotion controller", "SG-GOV-008")
        txn.execute("UPDATE assertion SET lifecycle=? WHERE assertion_id=?", (new.value, ref.n))
        event = new.value if new in (Lifecycle.PROMOTED, Lifecycle.REJECTED, Lifecycle.DEPRECATED) else "STAGE_CHANGED"
        txn.audit(actor, event, str(ref), f"{a.lifecycle.value}->{new.value}")
        return updated
