import pytest

from phoenix_core.ai.contracts import AIUsage
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker


def test_usage_is_recorded_per_organisation():
    tracker = AIUsageTracker()

    tracker.record(
        "org-1",
        AIUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.25,
            currency="USD",
        ),
    )

    usage = tracker.get("org-1")

    assert usage.requests == 1
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.total_tokens == 150
    assert usage.estimated_cost == 0.25
    assert usage.currency == "USD"


def test_organisations_have_separate_usage():
    tracker = AIUsageTracker()

    tracker.record("org-1", AIUsage(total_tokens=100))
    tracker.record("org-2", AIUsage(total_tokens=200))

    assert tracker.get("org-1").total_tokens == 100
    assert tracker.get("org-2").total_tokens == 200


def test_request_quota_is_enforced():
    tracker = AIUsageTracker()
    tracker.record("org-1", AIUsage())

    quota = AIQuotaService(tracker)

    with pytest.raises(PermissionError, match="request quota"):
        quota.check_request(
            "org-1",
            AIUsagePolicy(max_requests=1),
        )


def test_token_quota_is_enforced():
    tracker = AIUsageTracker()

    tracker.record(
        "org-1",
        AIUsage(
            total_tokens=100,
        ),
    )

    quota = AIQuotaService(tracker)

    with pytest.raises(PermissionError, match="total token quota"):
        quota.check_request(
            "org-1",
            AIUsagePolicy(max_total_tokens=100),
        )


def test_cost_quota_is_enforced():
    tracker = AIUsageTracker()

    tracker.record(
        "org-1",
        AIUsage(
            estimated_cost=5.0,
            currency="USD",
        ),
    )

    quota = AIQuotaService(tracker)

    with pytest.raises(PermissionError, match="cost quota"):
        quota.check_request(
            "org-1",
            AIUsagePolicy(
                max_estimated_cost=5.0,
                currency="USD",
            ),
        )


def test_unlimited_policy_allows_request():
    tracker = AIUsageTracker()
    quota = AIQuotaService(tracker)

    quota.check_request(
        "org-1",
        AIUsagePolicy(),
    )
