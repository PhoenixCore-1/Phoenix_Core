from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class AIProviderConfig:
    """
    Non-secret server-side configuration for an AI provider.

    Provider credentials are resolved separately through Phoenix Core's
    secure secret mechanism and must never be stored in this configuration
    object, AI requests, module contracts, logs, or client responses.
    """

    provider_name: str
    base_url: str
    default_model: Optional[str] = None
    timeout_seconds: float = 60.0
    extra_headers: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if not self.provider_name:
            raise ValueError("Provider name cannot be empty")

        if not self.base_url:
            raise ValueError("Provider base URL cannot be empty")

        if self.timeout_seconds <= 0:
            raise ValueError("Provider timeout must be greater than zero")
