from dataclasses import dataclass
from typing import Optional

from phoenix_core.ai.contracts import AIUsage


@dataclass
class AIUsageRecord:
    organisation_id: str
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    currency: Optional[str] = None


class AIUsageTracker:
    """Core-owned in-memory usage authority.

    Persistence/metering integration can be added without changing
    the AI provider contract.
    """

    def __init__(self):
        self._records: dict[str, AIUsageRecord] = {}

    def get(self, organisation_id: str) -> AIUsageRecord:
        record = self._records.get(organisation_id)

        if record is None:
            record = AIUsageRecord(
                organisation_id=organisation_id,
            )
            self._records[organisation_id] = record

        return record

    def record(
        self,
        organisation_id: str,
        usage: Optional[AIUsage],
    ) -> AIUsageRecord:
        record = self.get(organisation_id)

        record.requests += 1

        if usage is not None:
            record.input_tokens += usage.input_tokens or 0
            record.output_tokens += usage.output_tokens or 0
            record.total_tokens += usage.total_tokens or 0
            record.estimated_cost += usage.estimated_cost or 0.0

            if usage.currency:
                record.currency = usage.currency

        return record
