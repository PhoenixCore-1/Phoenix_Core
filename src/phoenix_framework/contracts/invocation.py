"""Phoenix module-to-module invocation contracts."""

from dataclasses import dataclass
from typing import Any, Mapping

from phoenix_framework.context import FrameworkContext


@dataclass(frozen=True)
class ModuleInvocationRequest:
    """
    Request to invoke a published operation on another Phoenix module.

    Security and tenant authority remain with Phoenix Core through the
    FrameworkContext carried with the request.
    """

    request_id: str
    source_module: str
    target_module: str
    contract: str
    operation: str
    context: FrameworkContext
    payload: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("Invocation request_id cannot be empty")

        if not self.source_module.strip():
            raise ValueError("Invocation source_module cannot be empty")

        if not self.target_module.strip():
            raise ValueError("Invocation target_module cannot be empty")

        if not self.contract.strip():
            raise ValueError("Invocation contract cannot be empty")

        if not self.operation.strip():
            raise ValueError("Invocation operation cannot be empty")

        if self.source_module == self.target_module:
            raise ValueError(
                "Module invocation source and target cannot be identical"
            )


@dataclass(frozen=True)
class ModuleInvocationResponse:
    """Response returned from a module invocation."""

    request_id: str
    success: bool
    data: Any = None
    error: str | None = None
