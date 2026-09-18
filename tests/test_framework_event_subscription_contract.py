from dataclasses import FrozenInstanceError

import pytest

from phoenix_framework.contracts.subscription import EventSubscription


def test_subscription_contains_expected_fields():
    handler = lambda event: {"handled": True}

    subscription = EventSubscription(
        subscriber_module="crm",
        event_type="sales.quote.created",
        handler=handler,
    )

    assert subscription.subscriber_module == "crm"
    assert subscription.event_type == "sales.quote.created"
    assert subscription.handler is handler


def test_subscription_is_immutable():
    subscription = EventSubscription(
        subscriber_module="crm",
        event_type="sales.quote.created",
        handler=lambda event: None,
    )

    with pytest.raises(FrozenInstanceError):
        subscription.event_type = "sales.quote.updated"


@pytest.mark.parametrize(
    "field",
    [
        "subscriber_module",
        "event_type",
    ],
)
def test_subscription_rejects_missing_required_fields(field):
    values = {
        "subscriber_module": "crm",
        "event_type": "sales.quote.created",
        "handler": lambda event: None,
    }

    values[field] = ""

    with pytest.raises(ValueError):
        EventSubscription(**values)
