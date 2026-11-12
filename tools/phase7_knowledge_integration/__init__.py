"""Read-only knowledge adapters for existing reasoning and interpretation services."""
from .read_adapter import (
    KNOWLEDGE_READ_ADAPTER_VERSION,
    KnowledgeReadAdapter,
    KnowledgeIntegrationError,
)
__all__ = ["KNOWLEDGE_READ_ADAPTER_VERSION", "KnowledgeReadAdapter", "KnowledgeIntegrationError"]
