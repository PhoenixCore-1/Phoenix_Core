"""Phoenix Generic Framework command contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ModuleCommand:
    """
    Contract representing a request for a module to perform an action.

    Commands are directed to an owning module and may change state.
    """

    request_id: str
    source_module: str
    target_module: str
    name: str
    context: Any
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("Command request ID is required.")

        if not self.source_module.strip():
            raise ValueError("Command source module is required.")

        if not self.target_module.strip():
            raise ValueError("Command target module is required.")

        if not self.name.strip():
            raise ValueError("Command name is required.")

        if self.source_module.strip().lower() == self.target_module.strip().lower():
            raise ValueError("Command source and target modules must differ.")
