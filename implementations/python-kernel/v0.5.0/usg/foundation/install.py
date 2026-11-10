"""Install / load / verify the Foundation Package in the database.

* ``install_foundation`` runs in ONE transaction with roles (REGISTRY, RELEASE):
  the package is install-time, CURATED content (origin CURATED, lifecycle PROMOTED).
  It is idempotent for an identical package and refuses to replace a different one
  (the package is sealed; a different package is a new release + migration).
* ``load_foundation`` rebuilds the in-memory Foundation purely from database rows.
* ``verify_foundation`` recomputes the content hash from the rows and compares it
  to the hash recorded at install: any later edit of dictionary rows is detected.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Mapping

from ..core.ids import IdSpace, Ref
from ..core.kinds import SemKind
from ..core.records import Concept
from ..core.values import Component, Lifecycle
from ..errors import InvariantViolation, StorageError
from ..model.frames import FrameLibrary
from ..model.relations import RelationDef
from ..ontology import ConceptSeed, Ontology
from ..storage.database import Database
from ..storage.records_store import RecordStore
from ..storage.schema import WriterRole
from .builder import Foundation, SeedEdge, build_foundation

META_HASH = "foundation_hash"
META_VERSION = "foundation_version"
FOUNDATION_VERSION = "0.2"


@dataclass
class InstallReport:
    already_installed: bool
    content_hash: str
    concept_refs: dict[str, Ref] = field(default_factory=dict)
    frame_refs: dict[str, Ref] = field(default_factory=dict)
    relation_refs: dict[str, Ref] = field(default_factory=dict)
    n_concepts: int = 0
    n_frames: int = 0
    n_edges: int = 0


def install_foundation(db: Database, store: RecordStore | None = None, foundation: Foundation | None = None) -> InstallReport:
    store = store or RecordStore()
    fnd = foundation or build_foundation()
    h = fnd.content_hash()
    with db.write(WriterRole.REGISTRY, WriterRole.RELEASE) as txn:
        existing = txn.scalar("SELECT value FROM meta WHERE key=?", (META_HASH,))
        if existing is not None:
            if existing != h:
                raise StorageError("a different Foundation Package is already installed; it is sealed (new release + migration required)")
            return InstallReport(True, h)

        for d in fnd.domains:
            store.add_domain(txn, d)

        onto = fnd.ontology
        concept_refs: dict[str, Ref] = {}
        for name in onto.concepts():
            seed = onto.seed(name)
            ref = store.add_concept(
                txn, Concept(seed.kind, name, seed.complete, Lifecycle.PROMOTED), domains=seed.domains,
                doc=seed.doc, idempotency_key=f"concept:{name}")
            concept_refs[name] = ref
        for name in onto.concepts():  # value domains reference other concepts: second pass
            vd = onto.seed(name).value_domain
            if vd:
                store.set_value_domain(txn, concept_refs[name], concept_refs[vd])

        relation_refs = {n: store.add_relation_def(txn, rel) for n, rel in fnd.relations.items()}

        n_edges = 0
        for e in fnd.edges:
            if store.add_edge(txn, concept_refs[e.src], e.relation, concept_refs[e.tgt], e.domain, qualifiers=dict(e.qualifiers)):
                n_edges += 1

        frame_refs: dict[str, Ref] = {}
        for name in fnd.frames.topo_order():
            store.add_frame(txn, fnd.frames, name, concept_refs, frame_refs)

        txn.execute("INSERT INTO meta(key,value) VALUES(?,?)", (META_HASH, h))
        txn.execute("INSERT INTO meta(key,value) VALUES(?,?)", (META_VERSION, FOUNDATION_VERSION))
        txn.audit(Component.RELEASE, "FOUNDATION_INSTALLED", "foundation", f"{len(concept_refs)} concepts, {len(frame_refs)} frames, hash {h[:12]}")
        return InstallReport(False, h, concept_refs, frame_refs, relation_refs, len(concept_refs), len(frame_refs), n_edges)


def load_foundation(db: Database, store: RecordStore | None = None) -> Foundation:
    """Rebuild the in-memory Foundation from database rows only."""
    store = store or RecordStore()
    with db.read() as r:
        labels = {int(x["concept_id"]): x["canonical_label"] for x in r.query("SELECT concept_id, canonical_label FROM concept")}
        domain_names = {int(x["domain_id"]): x["name"] for x in r.query("SELECT domain_id, name FROM domain")}
        parents: dict[str, list[str]] = {n: [] for n in labels.values()}
        disjoint: dict[str, list[str]] = {n: [] for n in labels.values()}
        edges: list[SeedEdge] = []
        for e in store.all_edges(r):
            s, t = labels[e.src], labels[e.tgt]
            if e.relation == "SUBCLASS_OF":
                parents[s].append(t)
            elif e.relation == "DISJOINT_WITH":
                disjoint[s].append(t)
            edges.append(SeedEdge(s, e.relation, t, e.domain, tuple(sorted((k, str(v)) for k, v in e.qualifiers.items()))))
        onto = Ontology()
        for row in r.query("SELECT * FROM concept ORDER BY concept_id"):
            cid = int(row["concept_id"])
            name = row["canonical_label"]
            doms = tuple(x["name"] for x in r.query(
                "SELECT d.name FROM concept_domain cd JOIN domain d ON d.domain_id=cd.domain_id WHERE cd.concept_id=? "
                "ORDER BY cd.is_primary DESC, d.name", (cid,)))
            vd = labels[int(row["value_domain"])] if row["value_domain"] is not None else None
            onto.add(ConceptSeed(name, SemKind(row["sem_kind"]), tuple(parents[name]), doms, tuple(disjoint[name]),
                                 bool(row["definition_complete"]), vd, row["doc"]))
            onto.bind_ref(name, Ref(IdSpace.CONCEPT, cid))
        relations = store.relation_defs(r)
        frames = store.load_frame_defs(r)
        domains = tuple(domain_names.values())
    lib = FrameLibrary(onto, relations).add_all(frames).finalize()
    return Foundation(onto, relations, lib, domains, tuple(edges))


def verify_foundation(db: Database, store: RecordStore | None = None) -> bool:
    """True iff the dictionary rows still hash to what was installed."""
    with db.read() as r:
        recorded = r.scalar("SELECT value FROM meta WHERE key=?", (META_HASH,))
    if recorded is None:
        return False
    try:
        return load_foundation(db, store).content_hash() == recorded
    except (InvariantViolation, StorageError, KeyError, ValueError, TypeError):
        return False  # a package that can no longer be rebuilt consistently has failed verification
