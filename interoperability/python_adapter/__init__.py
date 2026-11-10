"""USG-SEM/1.0 Python interoperability adapter."""
from .document import ImportedDocument, document_to_python, validate_contract_document
from .reverse import python_to_contract_document
from .usg_sem_1 import (
    ContractMappingError,
    contract_graph_roots_to_semir,
    contract_graph_roots_to_semir_partial,
    contract_graph_to_semir,
    mapping_report_for_python,
)

__all__ = [
    "ImportedDocument", "document_to_python", "validate_contract_document",
    "python_to_contract_document",
    "ContractMappingError", "contract_graph_roots_to_semir",
    "contract_graph_roots_to_semir_partial", "contract_graph_to_semir",
    "mapping_report_for_python",
]
