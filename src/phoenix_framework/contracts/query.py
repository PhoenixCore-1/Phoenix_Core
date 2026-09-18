"""Phoenix Generic Framework query contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ModuleQuery:
    """
    Contract representing a read-only information request.

    Queries are directed to an owning module and must not represent
    state-changing operations.
    """

    request_id: str
    source_module: str
    target_module: str
    name: str
    context: Any
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("Query request ID is required.")

        if not self.source_module.strip():
            raise ValueError("Query source module is required.")

        if not self.target_module.strip():
            raise ValueError("Query target module is required.")

        if not self.name.strip():
            raise ValueError("Query name is required.")

        if self.source_module.strip().lower() == self.target_module.strip().lower():
            raise ValueError("Query source and target modules must differ.")
