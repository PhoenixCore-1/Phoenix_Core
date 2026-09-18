import pytest

from phoenix_core.ai.rate_limit import (
    AIRateLimitPolicy,
    AIRateLimitService,
)


def test_rate_limit_allows_requests_within_limit():
    service = AIRateLimitService()
    policy = AIRateLimitPolicy(
        max_requests=2,
        window_seconds=60,
    )

    service.check_request("org-1", policy)
    service.check_request("org-1", policy)


def test_rate_limit_blocks_excess_requests():
    service = AIRateLimitService()
    policy = AIRateLimitPolicy(
        max_requests=2,
        window_seconds=60,
    )

    service.check_request("org-1", policy)
    service.check_request("org-1", policy)

    with pytest.raises(PermissionError, match="rate limit"):
        service.check_request("org-1", policy)


def test_rate_limits_are_isolated_between_organisations():
    service = AIRateLimitService()
    policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    service.check_request("org-1", policy)
    service.check_request("org-2", policy)


def test_invalid_rate_limit_is_rejected():
    with pytest.raises(ValueError):
        AIRateLimitPolicy(max_requests=0)

    with pytest.raises(ValueError):
        AIRateLimitPolicy(max_requests=1, window_seconds=0)
