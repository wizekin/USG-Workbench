"""Typed relation validation and conservative source reconciliation for Phase 7."""
from .relations import (
    RELATION_REGISTRY_VERSION,
    RelationValidationError,
    load_relation_registry,
    validate_relations,
    reconcile_relations,
)
__all__ = ["RELATION_REGISTRY_VERSION", "RelationValidationError", "load_relation_registry",
           "validate_relations", "reconcile_relations"]
