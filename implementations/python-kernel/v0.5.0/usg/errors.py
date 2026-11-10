"""Exception hierarchy. Every error that represents a violated rule carries the
rule/invariant code so reports and tests can assert on it."""

from __future__ import annotations


class USGError(Exception):
    """Base class for all USG errors."""

    code: str = "USG-ERR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class InvariantViolation(USGError):
    """A data-model invariant (I-01..I-14) or construction rule was violated."""

    code = "INVARIANT"


class PolicyDenied(USGError):
    """An action is forbidden by the autonomy policy or by role permissions."""

    code = "POLICY-DENIED"


class BudgetExceeded(USGError):
    """A resource or big-model budget does not allow the operation."""

    code = "BUDGET"


class StorageError(USGError):
    """A storage-layer failure (unknown id, role violation, schema problem)."""

    code = "STORAGE"


class SealViolation(USGError):
    """Sealed (frozen) code or data no longer matches its install-time hash."""

    code = "SEAL-VIOLATION"
