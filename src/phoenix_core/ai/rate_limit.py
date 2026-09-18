from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class AIRateLimitPolicy:
    max_requests: int
    window_seconds: int = 60

    def __post_init__(self):
        if self.max_requests < 1:
            raise ValueError("Rate limit must allow at least one request")

        if self.window_seconds < 1:
            raise ValueError("Rate limit window must be positive")


class AIRateLimitService:
    """Core-owned AI request rate limiting."""

    def __init__(self):
        self._requests: dict[str, list[datetime]] = {}

    def check_request(
        self,
        organisation_id: str,
        policy: AIRateLimitPolicy,
    ) -> None:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=policy.window_seconds)

        timestamps = self._requests.setdefault(organisation_id, [])

        timestamps[:] = [
            timestamp
            for timestamp in timestamps
            if timestamp > cutoff
        ]

        if len(timestamps) >= policy.max_requests:
            raise PermissionError("AI rate limit exceeded")

        timestamps.append(now)
