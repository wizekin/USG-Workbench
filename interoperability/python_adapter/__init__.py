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
_V09_EXPORTS = {"KernelV09Document", "document_to_kernel_v09", "kernel_v09_document_to_contract"}
_V10_EXPORTS = {"KernelV10Document", "document_to_kernel_v10", "kernel_v10_document_to_contract"}
_V11_EXPORTS = {"KernelV11Document", "document_to_kernel_v11", "kernel_v11_document_to_contract"}
_V12_EXPORTS = {"KernelV12Document", "document_to_kernel_v12", "kernel_v12_document_to_contract"}
_V121_EXPORTS = {"KernelV121Document", "document_to_kernel_v121", "kernel_v121_document_to_contract"}
_V13_EXPORTS = {"KernelV13Document", "document_to_kernel_v13", "kernel_v13_document_to_contract"}
_V14_EXPORTS = {"KernelV14Document", "document_to_kernel_v14", "kernel_v14_document_to_contract"}
_V15_EXPORTS = {"KernelV15Document", "document_to_kernel_v15", "kernel_v15_document_to_contract"}
__all__ += sorted(_V06_EXPORTS | _V07_EXPORTS | _V08_EXPORTS | _V09_EXPORTS | _V10_EXPORTS | _V11_EXPORTS | _V12_EXPORTS | _V121_EXPORTS | _V13_EXPORTS | _V14_EXPORTS | _V15_EXPORTS)

def __getattr__(name):
    from importlib import import_module
    if name in _V15_EXPORTS:
        module = import_module(".document_v15", __name__)
        return getattr(module, name)
    if name in _V14_EXPORTS:
        module = import_module(".document_v14", __name__)
        return getattr(module, name)
    if name in _V121_EXPORTS:
        module = import_module(".document_v121", __name__)
        return getattr(module, name)
    if name in _V13_EXPORTS:
        module = import_module(".document_v13", __name__)
        return getattr(module, name)
    if name in _V12_EXPORTS:
        module = import_module(".document_v12", __name__)
        return getattr(module, name)
    if name in _V11_EXPORTS:
        module = import_module(".document_v11", __name__)
        return getattr(module, name)
    if name in _V10_EXPORTS:
        module = import_module(".document_v10", __name__)
        return getattr(module, name)
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
