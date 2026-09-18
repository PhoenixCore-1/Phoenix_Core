from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker


class AIQuotaService:
    """Core authority for enforcing AI consumption limits."""

    def __init__(self, usage_tracker: AIUsageTracker):
        self.usage_tracker = usage_tracker

    def check_request(
        self,
        organisation_id: str,
        policy: AIUsagePolicy,
    ) -> None:
        usage = self.usage_tracker.get(organisation_id)

        if (
            policy.max_requests is not None
            and usage.requests >= policy.max_requests
        ):
            raise PermissionError("AI request quota exceeded")

        if (
            policy.max_input_tokens is not None
            and usage.input_tokens >= policy.max_input_tokens
        ):
            raise PermissionError("AI input token quota exceeded")

        if (
            policy.max_output_tokens is not None
            and usage.output_tokens >= policy.max_output_tokens
        ):
            raise PermissionError("AI output token quota exceeded")

        if (
            policy.max_total_tokens is not None
            and usage.total_tokens >= policy.max_total_tokens
        ):
            raise PermissionError("AI total token quota exceeded")

        if (
            policy.max_estimated_cost is not None
            and usage.estimated_cost >= policy.max_estimated_cost
        ):
            raise PermissionError("AI cost quota exceeded")
