"""ID registry (spec Part 2 §2.4, Part 7 §7.10).

* The registry is the ONLY allocator of ids; allocation happens inside the
  caller's write transaction (REGISTRY role required).
* Ids are meaning-free, immutable and never reused. Retirement writes a
  tombstone; old references stay resolvable.
* Allocation is idempotent per key, so retries, restarts and concurrent
  controllers never allocate a second id for the same proposal (E-20, E-63).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.ids import IdSpace, Ref
from ..core.values import Component
from ..errors import InvariantViolation, StorageError
from .database import ReadTxn, WriteTxn
from .schema import WriterRole


@dataclass(frozen=True)
class RegistryEntry:
    ref: Ref
    record_kind: str
    sem_kind: str | None
    status: str
    version: int
    primary_domain: int | None
    tombstone: bool
    replaced_by: Ref | None
    tombstone_reason: str | None


def _row_to_entry(r) -> RegistryEntry:
    return RegistryEntry(
        ref=Ref(IdSpace(r["space"]), int(r["id"])),
        record_kind=r["record_kind"],
        sem_kind=r["sem_kind"],
        status=r["status"],
        version=int(r["version"]),
        primary_domain=r["primary_domain"],
        tombstone=bool(r["tombstone"]),
        replaced_by=Ref.parse(r["replaced_by"]) if r["replaced_by"] else None,
        tombstone_reason=r["tombstone_reason"],
    )


class IdRegistry:
    def allocate(
        self,
        txn: WriteTxn,
        space: IdSpace,
        *,
        record_kind: str,
        sem_kind: str | None = None,
        status: str = "DISCOVERED",
        version: int = 1,
        primary_domain: int | None = None,
        idempotency_key: str | None = None,
    ) -> Ref:
        txn.require_role(WriterRole.REGISTRY)
        if idempotency_key:
            row = txn.one("SELECT space,id FROM idempotency_key WHERE key=?", (idempotency_key,))
            if row is not None:
                if row["space"] != space.value:
                    raise InvariantViolation(
                        f"idempotency key {idempotency_key!r} already used in space {row['space']}", "SG-IDN-007"
                    )
                return Ref(space, int(row["id"]))
        row = txn.one("SELECT next_id FROM id_sequence WHERE space=?", (space.value,))
        if row is None:
            n = 1
            txn.execute("INSERT INTO id_sequence(space,next_id) VALUES(?,?)", (space.value, 2))
        else:
            n = int(row["next_id"])
            txn.execute("UPDATE id_sequence SET next_id=? WHERE space=?", (n + 1, space.value))
        txn.execute(
            "INSERT INTO registry_entry(space,id,record_kind,sem_kind,status,version,primary_domain) VALUES(?,?,?,?,?,?,?)",
            (space.value, n, record_kind, sem_kind, status, version, primary_domain),
        )
        if idempotency_key:
            txn.execute(
                "INSERT INTO idempotency_key(key,space,id,created_at) VALUES(?,?,?,?)",
                (idempotency_key, space.value, n, float(txn.clock.now())),
            )
        return Ref(space, n)

    def get(self, txn: ReadTxn, ref: Ref) -> RegistryEntry | None:
        row = txn.one("SELECT * FROM registry_entry WHERE space=? AND id=?", (ref.space.value, ref.n))
        return _row_to_entry(row) if row else None

    def resolve_status(self, txn: ReadTxn, ref: Ref) -> str:
        """'ACTIVE' | 'TOMBSTONE' | 'UNKNOWN' — SG-FND-001 requires every id to resolve."""
        e = self.get(txn, ref)
        if e is None:
            return "UNKNOWN"
        return "TOMBSTONE" if e.tombstone else "ACTIVE"

    def require_resolvable(self, txn: ReadTxn, ref: Ref) -> RegistryEntry:
        e = self.get(txn, ref)
        if e is None:
            raise StorageError(f"unknown reference {ref}")
        return e

    def set_status(self, txn: WriteTxn, ref: Ref, status: str, version: int | None = None) -> None:
        txn.require_role(WriterRole.REGISTRY)
        e = self.require_resolvable(txn, ref)
        if e.tombstone:
            raise InvariantViolation(f"{ref} is tombstoned", "I-03")
        txn.execute(
            "UPDATE registry_entry SET status=?, version=? WHERE space=? AND id=?",
            (status, version if version is not None else e.version, ref.space.value, ref.n),
        )

    def tombstone(self, txn: WriteTxn, ref: Ref, replaced_by: Ref | None = None, reason: str = "") -> None:
        txn.require_role(WriterRole.REGISTRY)
        e = self.require_resolvable(txn, ref)
        if e.tombstone:
            raise InvariantViolation(f"{ref} already tombstoned", "I-03")
        txn.execute(
            "UPDATE registry_entry SET tombstone=1, replaced_by=?, tombstone_reason=? WHERE space=? AND id=?",
            (str(replaced_by) if replaced_by else None, reason[:300], ref.space.value, ref.n),
        )
        txn.audit(Component.REGISTRY, "ID_TOMBSTONED", str(ref), reason)

    def count(self, txn: ReadTxn, space: IdSpace) -> int:
        return int(txn.scalar("SELECT COUNT(*) FROM registry_entry WHERE space=?", (space.value,), 0))
