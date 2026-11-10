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

from .kernel_v05 import (
    KernelV05Graph, contract_graph_roots_to_kernel_v05,
    contract_graph_roots_to_kernel_v05_partial, kernel_v05_graph_to_contract,
)
from .document_v05 import KernelV05Document, document_to_kernel_v05, kernel_v05_document_to_contract
__all__ += [
    "KernelV05Graph", "contract_graph_roots_to_kernel_v05",
    "contract_graph_roots_to_kernel_v05_partial", "kernel_v05_graph_to_contract",
    "KernelV05Document", "document_to_kernel_v05", "kernel_v05_document_to_contract",
]

_V06_EXPORTS = {"KernelV06Document", "document_to_kernel_v06", "kernel_v06_document_to_contract"}
_V07_EXPORTS = {"KernelV07Document", "document_to_kernel_v07", "kernel_v07_document_to_contract"}
_V08_EXPORTS = {"KernelV08Document", "document_to_kernel_v08", "kernel_v08_document_to_contract"}
__all__ += sorted(_V06_EXPORTS | _V07_EXPORTS | _V08_EXPORTS | _V09_EXPORTS)

def __getattr__(name):
    from importlib import import_module
    if name in _V09_EXPORTS:
        module = import_module(".document_v09", __name__)
        return getattr(module, name)
    if name in _V08_EXPORTS:
        module = import_module(".document_v08", __name__)
        return getattr(module, name)
    if name in _V07_EXPORTS:
        module = import_module(".document_v07", __name__)
        return getattr(module, name)
    if name in _V06_EXPORTS:
        module = import_module(".document_v06", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
