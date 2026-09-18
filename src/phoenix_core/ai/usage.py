from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AIUsagePolicy:
    """Core-owned AI consumption limits."""

    max_requests: Optional[int] = None
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    max_estimated_cost: Optional[float] = None
    currency: Optional[str] = None

    def __post_init__(self):
        limits = (
            self.max_requests,
            self.max_input_tokens,
            self.max_output_tokens,
        )

        for value in limits:
            if value is not None and value < 0:
                raise ValueError("Usage limits cannot be negative")

        if self.max_total_tokens is not None and self.max_total_tokens < 0:
            raise ValueError("Usage limits cannot be negative")

        if self.max_estimated_cost is not None and self.max_estimated_cost < 0:
            raise ValueError("Estimated cost limit cannot be negative")

        if self.max_estimated_cost is not None and not self.currency:
            raise ValueError(
                "Currency is required when an estimated cost limit is configured"
            )
