"""Sealed code manifest — the no-human replacement for the spec's "out-of-band
human release" of Level-1 rules, the validator and the autonomy policy
(SG-FND-005, SG-SEC-009).

At install the SHA-256 of each sealed module's source is stored in
``sealed_manifest``. On every start (and periodically) ``verify_seal`` compares
the live source to the manifest. A mismatch means the code that enforces the
safety invariants changed after install, so the system must refuse to promote
anything (SAFE MODE). Changing sealed code is a *package release* followed by an
explicit ``reseal`` — never something a runtime process can do.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from ..core.values import Component
from ..errors import SealViolation
from ..storage.database import Database
from ..storage.schema import WriterRole
from ..util import sha256_hex

# Extended by later implementation parts (validator, rulebook, security, ...).
SEALED_MODULES: list[str] = [
    # foundations (Part 1)
    "usg", "usg.cli",
    "usg.errors",
    "usg.util",
    "usg.config",
    "usg.core.ids",
    "usg.core.kinds",
    "usg.core.values",
    "usg.core.roles",
    "usg.storage.audit",
    "usg.autonomy.policy",
    "usg.autonomy.ledger",
    "usg.autonomy.seal",
    # data model, storage boundary and Foundation Package (Part 2)
    "usg.core.records",
    "usg.ontology",
    "usg.model.relations",
    "usg.model.frames",
    "usg.storage.schema",
    "usg.storage.database",
    "usg.storage.registry",
    "usg.storage.records_store",
    "usg.foundation.concepts",
    "usg.foundation.relations",
    "usg.foundation.functions",
    "usg.foundation.frames",
    "usg.foundation.builder",
    "usg.foundation.install",
    # expression grammar (Part 3)
    "usg.grammar.node",
    "usg.grammar.serialize",
    "usg.grammar.scope",
    "usg.grammar.timeval",
    "usg.grammar.canon",
    "usg.grammar.opaque",
    "usg.grammar.typecheck",
    "usg.grammar.annot",
    "usg.validation.certificate", "usg.validation.checks", "usg.validation.rules", "usg.validation.validator",
    "usg.validation.evidence", "usg.autonomy.panel", "usg.security.text", "usg.runtime",
    "usg.concepts.lexicon", "usg.concepts.identity", "usg.interpretation.parser", "usg.models.gateway",
    "usg.learning.dsl", "usg.learning.engine", "usg.cognition.controller", "usg.cognition.worker",
    "usg.cognition.memory", "usg.cognition.reasoner", "usg.encoding.usbf", "usg.encoding.exchange",
    "usg.validation.evaluation", "usg.cognition.entailments",
    "usg.encoding.optimizer", "usg.storage.partitions", "usg.services",
    "usg.encoding.compact",
    "usg.benchmark.corpus", "usg.benchmark.runner",
    "usg.concepts.definitions", "usg.validation.contextual", "usg.validation.calibration",
    "usg.interpretation.resources", "usg.interpretation.dependencies", "usg.learning.semantic",
    "usg.cognition.resources", "usg.encoding.templates", "usg.encoding.linked_data",
    "usg.storage.views", "usg.conformance", "usg.acceptance", "usg.release",
]


def module_hash(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec is None or not spec.origin or spec.origin in ("built-in", "frozen"):
        raise SealViolation(f"cannot locate source of sealed module {name!r}")
    with open(spec.origin, "rb") as f:
        return sha256_hex(f.read())


def compute_manifest(modules: list[str] | None = None) -> dict[str, str]:
    return {m: module_hash(m) for m in (modules or SEALED_MODULES)}


@dataclass(frozen=True)
class SealReport:
    ok: bool
    mismatches: tuple[str, ...]
    missing: tuple[str, ...]  # sealed module not in manifest (needs reseal after upgrade)


def install_seal(db: Database, modules: list[str] | None = None, *, reseal: bool = False) -> dict[str, str]:
    """Record the manifest. Idempotent if unchanged; refuses to overwrite a
    different manifest unless ``reseal=True`` (a release-time action)."""
    manifest = compute_manifest(modules)
    now = db.clock.now()
    with db.write(WriterRole.RELEASE) as txn:
        existing = {r["name"]: r["sha256"] for r in txn.query("SELECT name,sha256 FROM sealed_manifest")}
        if existing and not reseal:
            if existing != manifest:
                raise SealViolation("sealed manifest differs from live code; refusing to overwrite without reseal")
            return manifest
        if reseal:
            txn.execute("DELETE FROM sealed_manifest")
        for name, digest in manifest.items():
            txn.execute("INSERT INTO sealed_manifest(name,kind,sha256,sealed_at) VALUES(?,?,?,?)",
                        (name, "MODULE", digest, now))
        txn.audit(Component.RELEASE, "SEAL_INSTALLED", "manifest", f"{len(manifest)} modules; reseal={reseal}")
    return manifest


def verify_seal(db: Database, modules: list[str] | None = None) -> SealReport:
    live = compute_manifest(modules)
    with db.read() as r:
        stored = {row["name"]: row["sha256"] for row in r.query("SELECT name,sha256 FROM sealed_manifest")}
    mismatches = tuple(sorted(n for n, h in live.items() if n in stored and stored[n] != h))
    missing = tuple(sorted(n for n in live if n not in stored))
    return SealReport(ok=not mismatches and not missing and bool(stored), mismatches=mismatches, missing=missing)


def assert_sealed(db: Database, modules: list[str] | None = None) -> None:
    rep = verify_seal(db, modules)
    if not rep.ok:
        raise SealViolation(
            f"seal check failed: mismatches={list(rep.mismatches)} missing={list(rep.missing)} (SAFE MODE)"
        )
