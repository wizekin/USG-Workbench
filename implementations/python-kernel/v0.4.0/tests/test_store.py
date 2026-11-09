import dataclasses
import sqlite3
import unittest

from usg.core.ids import IdSpace, Ref
from usg.core.kinds import SemKind
from usg.core.records import (Anchor, Assertion, Concept, ContentType, Filler, FrameInstance, IntroducedIn, Referent,
                              RoleBinding, Source)
from usg.core.spans import Span
from usg.core.values import (Basis, CommitmentKind, Component, EpistemicStatus, FillerKind, IntroducedInKind, Lifecycle,
                             Number, Origin, ReferentScope, Sensitivity, TrustTier, ValueState)
from usg.errors import InvariantViolation, PolicyDenied, StorageError
from usg.foundation.builder import build_foundation
from usg.foundation.install import install_foundation, load_foundation, verify_foundation
from usg.model.frames import FrameLibrary
from usg.storage.audit import verify_chain
from usg.storage.registry import IdRegistry
from usg.storage.records_store import RecordStore
from usg.storage.schema import WriterRole as W
from tests.helpers import make_db

TEXT = "The doctor gave the patient medication."


class Base(unittest.TestCase):
    def setUp(self):
        self.db, self.clock = make_db()
        self.store = RecordStore()
        self.reg = self.store.registry
        self.fnd = build_foundation()
        self.lib = self.fnd.frames
        self.rep = install_foundation(self.db, self.store, self.fnd)
        self.c = self.rep.concept_refs

    def src(self, text=TEXT, **kw):
        with self.db.write(W.REGISTRY, W.PROVENANCE) as t:
            return self.store.add_source(t, Source(text, **kw))

    def referent(self, source, cls, span, **kw):
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            return self.store.add_referent(t, Referent(SemKind.ENTITY, (self.c[cls],), source=source.ref, span=span, **kw))

    def audit_events(self):
        with self.db.read() as r:
            return [x["event"] for x in r.query("SELECT event FROM audit_log ORDER BY seq")]


class SourceTests(Base):
    def test_roundtrip_compression_and_idempotence(self):
        s = self.src(anchor=Anchor(document_date="2026-10-16"), uri="doc://1", sensitivity=Sensitivity.PUBLIC)
        with self.db.read() as r:
            back = self.store.get_source(r, s.ref)
            self.assertEqual(back.text, TEXT)
            self.assertEqual(back.anchor.document_date, "2026-10-16")
            self.assertEqual(back.sensitivity, Sensitivity.PUBLIC)
            self.assertEqual(back.text_hash, s.text_hash)
            raw = r.scalar("SELECT stored_text FROM source")
            self.assertIsInstance(raw, bytes)
            self.assertNotEqual(raw, TEXT.encode())  # compressed
        again = self.src(anchor=Anchor(document_date="2026-10-16"), uri="doc://1", sensitivity=Sensitivity.PUBLIC)
        self.assertEqual(again.ref, s.ref)  # same input, same id
        other = self.src(uri="doc://2")
        self.assertNotEqual(other.ref, s.ref)

    def test_sources_are_immutable_and_never_deleted(self):
        s = self.src()
        raw = self.db.raw_unsafe_connection()
        for sql in ("UPDATE source SET stored_text=x'00'", "UPDATE source SET text_hash='x'", "UPDATE source SET language='fr'",
                    "DELETE FROM source"):
            with self.assertRaises(sqlite3.DatabaseError, msg=sql):
                raw.execute(sql)

    def test_tamper_is_detected_on_read(self):
        import zlib
        s = self.src()
        raw = self.db.raw_unsafe_connection()
        raw.execute("DROP TRIGGER source_immutable")
        raw.execute("UPDATE source SET stored_text=?", (zlib.compress(b"The doctor gave the patient poison.xx"),))
        with self.assertRaises(InvariantViolation):
            with self.db.read() as r:
                self.store.get_source(r, s.ref)

    def test_trust_tier_rules(self):
        s = self.src(trust_tier=TrustTier.QUARANTINE)
        with self.assertRaises(PolicyDenied):
            with self.db.write(W.PROVENANCE) as t:
                self.store.set_trust_tier(t, s.ref, TrustTier.TRUSTED, probation_passed=True)  # never at runtime
        with self.assertRaises(PolicyDenied):
            with self.db.write(W.PROVENANCE) as t:
                self.store.set_trust_tier(t, s.ref, TrustTier.STANDARD)  # needs automatic probation
        with self.db.write(W.PROVENANCE) as t:
            self.store.set_trust_tier(t, s.ref, TrustTier.STANDARD, probation_passed=True)
            self.store.set_trust_tier(t, s.ref, TrustTier.QUARANTINE)  # lowering is always allowed
        self.assertEqual(self.audit_events().count("TIER_CHANGED"), 2)

    def test_only_provenance_role_writes_sources(self):
        with self.assertRaises(PolicyDenied):
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
                self.store.add_source(t, Source(TEXT))


class FoundationInstallTests(Base):
    def test_install_counts_and_idempotence(self):
        self.assertFalse(self.rep.already_installed)
        self.assertEqual((self.rep.n_concepts, self.rep.n_frames), (81, 57))
        self.assertTrue(install_foundation(self.db, self.store, self.fnd).already_installed)
        with self.db.read() as r:
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM concept"), 81)
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM frame_def"), 57)
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM relation_def"), len(self.fnd.relations))
            self.assertEqual(r.scalar("SELECT COUNT(DISTINCT lifecycle) FROM concept"), 1)
            self.assertEqual(r.scalar("SELECT lifecycle FROM concept LIMIT 1"), "PROMOTED")
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM concept_domain WHERE is_primary=1"), 81)
        self.assertIn("FOUNDATION_INSTALLED", self.audit_events())

    def test_load_matches_built_and_verifies(self):
        self.assertTrue(verify_foundation(self.db, self.store))
        loaded = load_foundation(self.db, self.store)
        self.assertEqual(loaded.content_hash(), self.fnd.content_hash())
        self.assertEqual(sorted(loaded.frames.names()), sorted(self.fnd.frames.names()))
        self.assertEqual(loaded.frames.resolved("GIVE").role_names(), self.lib.resolved("GIVE").role_names())
        self.assertEqual(loaded.ontology.refs["Person"], self.c["Person"])
        self.assertEqual(loaded.ontology.classes_compatible(["Argument"], "PhysicalEntity").value, "INCOMPATIBLE")

    def test_dictionary_tamper_is_detected(self):
        self.assertTrue(verify_foundation(self.db, self.store))
        raw = self.db.raw_unsafe_connection()
        # (1) tamper that keeps the package loadable: only the hash can catch it
        raw.execute("UPDATE concept SET doc='edited' WHERE canonical_label='Argument'")
        self.assertFalse(verify_foundation(self.db, self.store))
        raw.execute("UPDATE concept SET doc='abstract: cannot be bought or eaten' WHERE canonical_label='Argument'")
        self.assertTrue(verify_foundation(self.db, self.store))  # restoring the exact content restores verification
        # (2) tamper that makes the package structurally inconsistent
        raw.execute("UPDATE concept SET canonical_label='Persona' WHERE canonical_label='Person'")
        self.assertFalse(verify_foundation(self.db, self.store))

    def test_different_package_is_refused(self):
        self.db.raw_unsafe_connection().execute("UPDATE meta SET value='deadbeef' WHERE key='foundation_hash'")
        with self.assertRaises(StorageError):
            install_foundation(self.db, self.store, self.fnd)
        self.assertFalse(verify_foundation(self.db, self.store))

    def test_frame_versions_are_immutable(self):
        raw = self.db.raw_unsafe_connection()
        with self.assertRaises(sqlite3.DatabaseError):
            raw.execute("UPDATE frame_def SET body='{}' WHERE name='GIVE'")
        with self.assertRaises(sqlite3.DatabaseError):
            raw.execute("DELETE FROM frame_def WHERE name='GIVE'")

    def test_frame_rows_roles_and_parents(self):
        with self.db.read() as r:
            fid, ver = self.store.frame_ref(r, "GIVE")
            names = [x["name"] for x in r.query("SELECT name FROM frame_role WHERE frame_id=? ORDER BY role_index", (fid.n,))]
            self.assertEqual(names, list(self.lib.resolved("GIVE").role_names()))
            row = r.one("SELECT * FROM frame_role WHERE frame_id=? AND name='RECIPIENT'", (fid.n,))
            self.assertEqual(row["expected_class"], self.c["Agent"].n)
            par = r.one("SELECT link_kind, parent_frame_id FROM frame_parent WHERE frame_id=?", (fid.n,))
            self.assertEqual(par["link_kind"], "SPECIALIZES")
            self.assertEqual(par["parent_frame_id"], self.store.frame_ref(r, "TRANSFER")[0].n)
            self.assertEqual(self.store.frame_name(r, fid.n, 1), "GIVE")

    def test_new_frame_version_keeps_the_id_and_must_increase(self):
        f = self.lib.get("EAT")
        lib2 = FrameLibrary(self.fnd.ontology, self.fnd.relations)
        for n in self.lib.names():
            lib2.add(dataclasses.replace(f, version=2) if n == "EAT" else self.lib.get(n))
        lib2.finalize()
        with self.db.write(W.REGISTRY, W.PROMOTION) as t:
            ref = self.store.add_frame(t, lib2, "EAT", self.c, dict(self.rep.frame_refs))
        self.assertEqual(ref, self.rep.frame_refs["EAT"])  # same frame id
        with self.db.read() as r:
            self.assertEqual(self.store.frame_ref(r, "EAT")[1], 2)
            self.assertEqual(self.store.frame_ref(r, "EAT", 1)[1], 1)  # v1 still resolvable
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.PROMOTION) as t:
                self.store.add_frame(t, lib2, "EAT", self.c, dict(self.rep.frame_refs))  # same version again


class DictionaryTests(Base):
    def new_concept(self, label="Heater", parents=("Device",), roles=(W.REGISTRY, W.PROMOTION), lifecycle=Lifecycle.PROMOTED):
        with self.db.write(*roles) as t:
            ref = self.store.add_concept(t, Concept(SemKind.ENTITY, label, False, lifecycle), domains=["ENGINEERING"],
                                         idempotency_key=f"c:{label}")
            for p in parents:
                self.store.add_edge(t, ref, "SUBCLASS_OF", self.c[p], "ENGINEERING")
            return ref

    def test_promotion_may_extend_the_dictionary(self):
        ref = self.new_concept()
        with self.db.read() as r:
            self.assertEqual(self.store.get_concept(r, ref).canonical_label, "Heater")
            self.assertEqual(self.store.concept_domains(r, ref), ["ENGINEERING"])
            self.assertEqual([c.ref for c in self.store.find_concepts(r, "Heater")], [ref])
            self.assertEqual([e.tgt for e in self.store.edges_from(r, ref, "SUBCLASS_OF")], [self.c["Device"].n])
            self.assertIn(ref.n, {e.src for e in self.store.edges_to(r, self.c["Device"], "SUBCLASS_OF")})

    def test_only_promoted_concepts_enter_the_dictionary(self):
        for lc in (Lifecycle.DISCOVERED, Lifecycle.STRUCTURED, Lifecycle.VALIDATED_FORMALLY):
            with self.assertRaises(InvariantViolation):
                self.new_concept("X" + lc.value, lifecycle=lc)

    def test_wrong_roles_cannot_write_the_dictionary(self):
        with self.assertRaises(PolicyDenied):
            self.new_concept("Z", roles=(W.REGISTRY, W.CANDIDATE_STORE))
        with self.assertRaises(PolicyDenied):
            with self.db.write(W.PROMOTION) as t:  # no REGISTRY role: cannot allocate
                self.store.add_concept(t, Concept(SemKind.ENTITY, "Q", False, Lifecycle.PROMOTED))

    def test_unknown_domain_rejected(self):
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.PROMOTION) as t:
                self.store.add_concept(t, Concept(SemKind.ENTITY, "Q", False, Lifecycle.PROMOTED), domains=["NOPE"])

    def edge(self, a, rel, b, **kw):
        with self.db.write(W.REGISTRY, W.PROMOTION) as t:
            return self.store.add_edge(t, self.c[a], rel, self.c[b], kw.pop("domain", "UNIVERSAL_CORE"), **kw)

    def test_edge_constraints(self):
        self.assertTrue(self.edge("Pipe", "PROPER_PART_OF", "Pump"))
        self.assertFalse(self.edge("Pipe", "PROPER_PART_OF", "Pump"))  # duplicate: idempotent
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Pump", "PROPER_PART_OF", "Pipe")  # asymmetric
        self.assertEqual(cm.exception.code, "VC-G02")
        self.edge("Pump", "PROPER_PART_OF", "Engine")
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Engine", "PROPER_PART_OF", "Pipe")  # closes Pipe < Pump < Engine < Pipe
        self.assertEqual(cm.exception.code, "VC-G01")
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Pipe", "PROPER_PART_OF", "Pipe")
        self.assertEqual(cm.exception.code, "VC-G02")

    def test_inverse_and_symmetric_facts_are_stored_once(self):
        self.edge("Pipe", "PROPER_PART_OF", "Pump")
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Pump", "HAS_PART", "Pipe")  # derived inverse must not be stored too
        self.assertEqual(cm.exception.code, "SG-KNW-011")
        self.edge("Dog" if False else "Car", "DISJOINT_WITH", "Fan")
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Fan", "DISJOINT_WITH", "Car")
        self.assertEqual(cm.exception.code, "SG-KNW-011")

    def test_weights_only_on_associative_edges_with_a_scoring_model(self):
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Pipe", "PROPER_PART_OF", "Pump", weight=0.9, weight_model="m")
        self.assertEqual(cm.exception.code, "SG-KNW-002")
        with self.assertRaises(InvariantViolation) as cm:
            self.edge("Doctor", "ASSOCIATED_WITH", "Hospital", weight=0.8)  # model missing
        self.assertEqual(cm.exception.code, "SG-KNW-002")
        self.assertTrue(self.edge("Doctor", "ASSOCIATED_WITH", "Hospital", weight=0.8, weight_model="cooc-v1", domain="MEDICINE"))
        with self.db.read() as r:
            e = self.store.edges_from(r, self.c["Doctor"], "ASSOCIATED_WITH")[0]
            self.assertEqual((e.weight, e.weight_model, e.domain), (0.8, "cooc-v1", "MEDICINE"))

    def test_cross_domain_edges_are_flagged(self):
        self.edge("Pump", "ASSOCIATED_WITH", "Doctor", weight=0.1, weight_model="m")
        with self.db.read() as r:
            self.assertEqual(r.scalar("SELECT xdom FROM relation_edge WHERE src_id=? AND tgt_id=?", (self.c["Pump"].n, self.c["Doctor"].n)), 1)
            self.assertEqual(r.scalar("SELECT xdom FROM relation_edge WHERE src_id=? AND tgt_id=?", (self.c["Car"].n, self.c["Vehicle"].n)), 0)

    def test_bad_endpoints_and_domains(self):
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.PROMOTION) as t:
                self.store.add_edge(t, Ref(IdSpace.CONCEPT, 99999), "SUBCLASS_OF", self.c["Car"], "UNIVERSAL_CORE")
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.PROMOTION) as t:
                self.store.add_edge(t, Ref(IdSpace.REFERENT, 1), "SUBCLASS_OF", self.c["Car"], "UNIVERSAL_CORE")
        with self.assertRaises(InvariantViolation):
            self.edge("Car", "SUBCLASS_OF", "Vehicle", domain="NOPE")
        with self.assertRaises(StorageError):
            self.edge("Car", "NOT_A_RELATION", "Vehicle")


class InstanceTests(Base):
    def setUp(self):
        super().setUp()
        self.s = self.src()
        self.doctor = self.referent(self.s, "Doctor", Span(4, 10))
        self.patient = self.referent(self.s, "Patient", Span(20, 27))
        self.med = self.referent(self.s, "Medication", Span(28, 38))

    def give(self, agent=None, source=None, recipient=None, theme=None, extra=()):
        fid = self.rep.frame_refs["GIVE"]
        R = lambda ref: Filler.referent(ref)
        b = [RoleBinding("AGENT", ValueState.SPECIFIED, Basis.EXPLICIT, R(agent or self.doctor), Span(4, 10)),
             RoleBinding("SOURCE", ValueState.SPECIFIED, Basis.GRAMMATICAL, R(source or self.doctor), rule="SG-INT-012"),
             RoleBinding("RECIPIENT", ValueState.SPECIFIED, Basis.EXPLICIT, R(recipient or self.patient), Span(20, 27)),
             RoleBinding("THEME", ValueState.SPECIFIED, Basis.EXPLICIT, R(theme or self.med), Span(28, 38))]
        return FrameInstance(fid, 1, tuple(b) + tuple(extra), source=self.s.ref)

    def add_instance(self, inst):
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            return self.store.add_frame_instance(t, inst, self.lib)

    def test_referent_roundtrip(self):
        with self.db.read() as r:
            d = self.store.get_referent(r, self.doctor)
            self.assertEqual(d.instance_of, (self.c["Doctor"],))
            self.assertEqual(d.span, Span(4, 10))
            self.assertEqual(d.introduced_in.kind, IntroducedInKind.WORLD)
        two = self.referent(self.s, "Tablet", Span(28, 38), number=Number.PLURAL, cardinality=2)
        rng = self.referent(self.s, "Tablet", Span(28, 38), number=Number.PLURAL, cardinality=(2, 3))
        with self.db.read() as r:
            self.assertEqual(self.store.get_referent(r, two).cardinality, 2)
            self.assertEqual(self.store.get_referent(r, rng).cardinality, (2, 3))

    def test_referent_introduced_inside_an_attitude_context_roundtrips(self):
        inst = self.add_instance(self.give())
        apple = self.referent(self.s, "Apple", Span(1, 3), introduced_in=IntroducedIn(IntroducedInKind.CONTENT_OF, inst))
        with self.db.read() as r:
            got = self.store.get_referent(r, apple)
            self.assertEqual(got.introduced_in, IntroducedIn(IntroducedInKind.CONTENT_OF, inst))

    def test_resolved_individual_roundtrip(self):
        ref = self.referent(self.s, "Doctor", Span(4, 10), scope=ReferentScope.RESOLVED_INDIVIDUAL, individual_ids=("wikidata:Q123",))
        with self.db.read() as r:
            self.assertEqual(self.store.get_referent(r, ref).individual_ids, ("wikidata:Q123",))

    def test_referent_needs_resolvable_class_and_source(self):
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
                self.store.add_referent(t, Referent(SemKind.ENTITY, (Ref(IdSpace.CONCEPT, 99999),), source=self.s.ref))
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
                self.store.add_referent(t, Referent(SemKind.ENTITY, (self.c["Doctor"],)))  # no source

    def test_frame_instance_roundtrip(self):
        inst = self.give()
        ref = self.add_instance(inst)
        with self.db.read() as r:
            got = self.store.get_frame_instance(r, ref)
            self.assertEqual(got.frame, inst.frame)
            self.assertEqual({b.role for b in got.bindings}, {"AGENT", "SOURCE", "RECIPIENT", "THEME"})
            ag = got.binding("AGENT")
            self.assertEqual((ag.basis, ag.span, ag.filler.ref), (Basis.EXPLICIT, Span(4, 10), self.doctor))
            self.assertEqual(got.binding("SOURCE").rule, "SG-INT-012")  # the giver fills two roles
            self.assertEqual(got.binding("SOURCE").filler.ref, got.binding("AGENT").filler.ref)

    def test_holes_roundtrip_and_literals(self):
        ev = (RoleBinding("TIME", ValueState.UNKNOWN),)
        inst = self.give(extra=ev)
        ref = self.add_instance(inst)
        with self.db.read() as r:
            t = self.store.get_frame_instance(r, ref).binding("TIME")
            self.assertEqual((t.value_state, t.filler, t.basis), (ValueState.UNKNOWN, None, None))
        fid = self.rep.frame_refs["OPEN"]
        o = FrameInstance(fid, 1, (RoleBinding("UNDERGOER", ValueState.UNSPECIFIED),), source=self.s.ref)
        self.assertIsNotNone(self.add_instance(o))

    def test_invalid_instances_are_rejected_before_storage(self):
        bad_role = self.give(extra=(RoleBinding("EXAMINER", ValueState.UNSPECIFIED),))
        with self.assertRaises(InvariantViolation) as cm:
            self.add_instance(bad_role)
        self.assertEqual(cm.exception.code, "VC-S06")
        fid = self.rep.frame_refs["TRANSFER"]  # abstract
        abstract = FrameInstance(fid, 1, tuple(b for b in self.give().bindings), source=self.s.ref)
        with self.assertRaises(InvariantViolation) as cm:
            self.add_instance(abstract)
        self.assertEqual(cm.exception.code, "VC-S05")
        missing = FrameInstance(self.rep.frame_refs["GIVE"], 1, self.give().bindings[:2], source=self.s.ref)
        with self.assertRaises(InvariantViolation) as cm:
            self.add_instance(missing)
        self.assertEqual(cm.exception.code, "VC-S07")
        ghost = Ref(IdSpace.REFERENT, 99999)
        with self.assertRaises(InvariantViolation) as cm:
            self.add_instance(self.give(recipient=ghost))
        self.assertEqual(cm.exception.code, "SG-FND-001")
        with self.db.read() as r:
            self.assertEqual(r.scalar("SELECT COUNT(*) FROM frame_instance"), 0)  # nothing partial was stored

    def test_instance_pins_frame_version_and_library_must_match(self):
        other = FrameLibrary(self.fnd.ontology, self.fnd.relations)
        for n in self.lib.names():
            f = self.lib.get(n)
            other.add(dataclasses.replace(f, doc="edited") if n == "GIVE" else f)
        other.finalize()
        with self.assertRaises(InvariantViolation) as cm:
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
                self.store.add_frame_instance(t, self.give(), other)
        self.assertEqual(cm.exception.code, "I-12")

    def test_database_checks_are_a_second_line_of_defence(self):
        ref = self.add_instance(self.give())
        raw = self.db.raw_unsafe_connection()
        with self.assertRaises(sqlite3.IntegrityError):  # a hole carrying a filler
            raw.execute("INSERT INTO binding(instance_id,role_index,role_name,value_state,filler_kind,filler_space,filler_id)"
                        " VALUES(?,?,?,?,?,?,?)", (ref.n, 4, "TIME", "UNKNOWN", "REFERENT", "REFERENT", self.doctor.n))
        with self.assertRaises(sqlite3.IntegrityError):  # a SPECIFIED binding without a basis
            raw.execute("INSERT INTO binding(instance_id,role_index,role_name,value_state,filler_kind,filler_space,filler_id)"
                        " VALUES(?,?,?,?,?,?,?)", (ref.n, 4, "TIME", "SPECIFIED", "REFERENT", "REFERENT", self.doctor.n))

    def test_randomized_instances_roundtrip_exactly(self):
        """Property check (seeded, no external libs): random valid instances of every concrete frame survive
        store -> load unchanged, and dropping any REQUIRED role is always rejected."""
        import random
        rng = random.Random(20261019)
        pool = [self.doctor, self.patient, self.med] + [self.referent(self.s, "Doctor", Span(4, 10)) for _ in range(3)]
        holes = (ValueState.UNSPECIFIED, ValueState.UNKNOWN, ValueState.NOT_APPLICABLE, ValueState.WITHHELD)
        n_checked = 0
        for name in self.lib.names():
            rf = self.lib.resolved(name)
            if rf.frame.abstract:
                continue
            fid, ver = self.rep.frame_refs[name], 1
            for _ in range(8):
                used = {}
                bindings = []
                for r in rf.roles:
                    if not r.required and rng.random() < 0.5:
                        continue
                    if rng.random() < 0.3:
                        bindings.append(RoleBinding(r.name, rng.choice(holes)))
                        continue
                    ref = rng.choice(pool)
                    used[r.name] = ref
                    basis = rng.choice([Basis.EXPLICIT, Basis.GRAMMATICAL, Basis.BACKGROUND])
                    kw = {"span": Span(0, 3)} if basis is Basis.EXPLICIT else {"rule": "SG-INT-012"}
                    bindings.append(RoleBinding(r.name, ValueState.SPECIFIED, basis, Filler.referent(ref), **kw))
                inst = FrameInstance(fid, ver, tuple(bindings), source=self.s.ref)
                if self.lib.validate_bindings(name, bindings):  # e.g. random draw put one referent in two disjoint roles
                    continue
                ref = self.add_instance(inst)
                with self.db.read() as r:
                    got = self.store.get_frame_instance(r, ref)
                key = lambda b: (b.role, b.ord)
                self.assertEqual(sorted(got.bindings, key=key), sorted(bindings, key=key), name)
                n_checked += 1
            req = [r.name for r in rf.roles if r.required]
            for dropped in req:
                partial = tuple(RoleBinding(x, ValueState.UNSPECIFIED) for x in req if x != dropped)
                with self.assertRaises(InvariantViolation) as cm:
                    self.add_instance(FrameInstance(fid, ver, partial, source=self.s.ref))
                self.assertEqual(cm.exception.code, "VC-S07")
        self.assertGreater(n_checked, 150)

    # ---------------------------------------------------------------- assertions
    def assertion(self, **kw):
        inst = self.add_instance(self.give())
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            return self.store.add_assertion(t, Assertion.new(ContentType.INSTANCE, inst, Origin.SOURCE_TEXT, source=self.s.ref, **kw))

    def test_assertion_roundtrip_and_creation_statuses(self):
        a = self.assertion()
        with self.db.read() as r:
            got = self.store.get_assertion(r, a)
            self.assertEqual((got.epistemic_status, got.lifecycle, got.origin), (EpistemicStatus.SOURCE_ASSERTED, Lifecycle.DISCOVERED, Origin.SOURCE_TEXT))
        inst = self.add_instance(self.give())
        for status in (EpistemicStatus.VERIFIED, EpistemicStatus.DISPUTED, EpistemicStatus.UNKNOWN):
            with self.assertRaises(InvariantViolation):
                with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
                    self.store.add_assertion(t, Assertion(ContentType.INSTANCE, inst, Origin.SOURCE_TEXT, status, source=self.s.ref))
        with self.assertRaises(InvariantViolation):
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:  # born already promoted
                self.store.add_assertion(t, Assertion.new(ContentType.INSTANCE, inst, Origin.SOURCE_TEXT, source=self.s.ref,
                                                          lifecycle=Lifecycle.CORROBORATED, evidence=Ref(IdSpace.EVIDENCE, 1)))

    def test_attributed_commitment_roundtrip(self):
        inst = self.add_instance(self.give())
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            ref = self.store.add_assertion(t, Assertion.new(ContentType.INSTANCE, inst, Origin.SOURCE_TEXT, source=self.s.ref,
                                                            commitment=CommitmentKind.ATTRIBUTED, attributed_to=self.doctor))
        with self.db.read() as r:
            got = self.store.get_assertion(r, ref)
            self.assertEqual((got.commitment, got.attributed_to), (CommitmentKind.ATTRIBUTED, self.doctor))

    def test_status_changes_only_through_the_evaluation_process(self):
        a = self.assertion()
        with self.assertRaises(PolicyDenied):  # right component, wrong writer role
            with self.db.write(W.CANDIDATE_STORE) as t:
                self.store.set_assertion_status(t, a, EpistemicStatus.VERIFIED)
        for actor in (Component.INTERPRETER, Component.LEARNING_ENGINE, Component.PROMOTION_CONTROLLER):
            with self.assertRaises(InvariantViolation):  # right role, wrong component
                with self.db.write(W.EVALUATION) as t:
                    self.store.set_assertion_status(t, a, EpistemicStatus.VERIFIED, actor)
        with self.db.write(W.EVALUATION) as t:
            self.store.set_assertion_status(t, a, EpistemicStatus.DISPUTED)
        with self.db.write(W.EVALUATION) as t:
            self.store.set_assertion_status(t, a, EpistemicStatus.VERIFIED)
        with self.db.read() as r:
            self.assertEqual(self.store.get_assertion(r, a).epistemic_status, EpistemicStatus.VERIFIED)
        self.assertEqual(self.audit_events().count("STATUS_CHANGED"), 2)

    def test_inference_is_never_relabelled_source_stated(self):
        inst = self.add_instance(self.give())
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            inf = self.store.add_assertion(t, Assertion.new(ContentType.INSTANCE, inst, Origin.BACKGROUND_INFERENCE, source=self.s.ref))
        with self.assertRaises(InvariantViolation) as cm:
            with self.db.write(W.EVALUATION) as t:
                self.store.set_assertion_status(t, inf, EpistemicStatus.SOURCE_ASSERTED)
        self.assertEqual(cm.exception.code, "SG-EVD-003")

    def test_lifecycle_stages_are_owned_and_promotion_is_exclusive(self):
        a = self.assertion()
        with self.db.write(W.CANDIDATE_STORE) as t:
            self.store.set_assertion_stage(t, a, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        with self.assertRaises(InvariantViolation):  # no evidence yet: cannot be formally validated
            with self.db.write(W.CANDIDATE_STORE) as t:
                self.store.set_assertion_stage(t, a, Lifecycle.VALIDATED_FORMALLY, Component.VALIDATOR)
        with self.db.write(W.REGISTRY, W.CANDIDATE_STORE) as t:
            ev = self.reg.allocate(t, IdSpace.EVIDENCE, record_kind="Evidence")
            self.store.attach_evidence(t, a, ev)
        with self.assertRaises(InvariantViolation):  # an engine cannot validate
            with self.db.write(W.CANDIDATE_STORE) as t:
                self.store.set_assertion_stage(t, a, Lifecycle.VALIDATED_FORMALLY, Component.LEARNING_ENGINE)
        with self.db.write(W.CANDIDATE_STORE) as t:
            self.store.set_assertion_stage(t, a, Lifecycle.VALIDATED_FORMALLY, Component.VALIDATOR)
        for actor in (Component.VALIDATOR, Component.LEARNING_ENGINE, Component.AUTOMATED_PANEL):
            with self.assertRaises(InvariantViolation):
                with self.db.write(W.CANDIDATE_STORE, W.PROMOTION) as t:
                    self.store.set_assertion_stage(t, a, Lifecycle.PROMOTED, actor)
        with self.assertRaises(PolicyDenied):  # correct component, but not the promotion writer
            with self.db.write(W.CANDIDATE_STORE) as t:
                self.store.set_assertion_stage(t, a, Lifecycle.PROMOTED, Component.PROMOTION_CONTROLLER)
        with self.db.write(W.PROMOTION) as t:
            self.store.set_assertion_stage(t, a, Lifecycle.PROMOTED, Component.PROMOTION_CONTROLLER)
        with self.assertRaises(InvariantViolation):  # promoted records only deprecate
            with self.db.write(W.CANDIDATE_STORE) as t:
                self.store.set_assertion_stage(t, a, Lifecycle.STRUCTURED, Component.CANDIDATE_STORE)
        self.assertIn("PROMOTED", self.audit_events())
        with self.db.read() as r:
            ok, bad = verify_chain(r.query("SELECT * FROM audit_log ORDER BY seq"))
            self.assertTrue(ok)

    def test_database_level_assertion_invariants(self):
        inst = self.add_instance(self.give())
        raw = self.db.raw_unsafe_connection()
        base = ("INSERT INTO assertion(content_type,content_space,content_id,origin,epistemic_status,commitment,eval_context,"
                "source_id,lifecycle,grammar_version,ontology_release) VALUES('INSTANCE','INSTANCE',?,?,?,'AUTHOR','WORLD',?,'DISCOVERED','1.0','0.1')")
        with self.assertRaises(sqlite3.IntegrityError):  # I-08: no source and not an authorized origin
            raw.execute(base, (inst.n, "SOURCE_TEXT", "SOURCE_ASSERTED", None))
        with self.assertRaises(sqlite3.IntegrityError):  # an inference can never be SOURCE_ASSERTED
            raw.execute(base, (inst.n, "BACKGROUND_INFERENCE", "SOURCE_ASSERTED", self.s.ref.n))
        with self.assertRaises(sqlite3.IntegrityError):  # source-derived content is never INFERRED
            raw.execute(base, (inst.n, "SOURCE_TEXT", "INFERRED", self.s.ref.n))


if __name__ == "__main__":
    unittest.main()
