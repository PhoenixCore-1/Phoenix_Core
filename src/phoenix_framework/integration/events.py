"""Phoenix Generic Framework event bus."""

from typing import Dict, List

from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.subscription import EventSubscription
from phoenix_framework.integration.registry import IntegrationRegistry


class EventBus:
    """
    Runtime event publication and subscription infrastructure.

    The event bus owns routing only. It does not own module business logic,
    persistence, tenant authority, security authority, or event source data.

    Publisher ownership is validated through the existing
    IntegrationRegistry. The EventBus does not maintain a second module
    authority.
    """

    def __init__(
        self,
        integration_registry: IntegrationRegistry | None = None,
    ) -> None:
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._integration_registry = integration_registry

    def subscribe(self, subscription: EventSubscription) -> None:
        subscriptions = self._subscriptions.setdefault(
            subscription.event_type,
            [],
        )

        for existing in subscriptions:
            if existing.subscriber_module == subscription.subscriber_module:
                raise ValueError(
                    "Subscriber already registered for event type: "
                    f"{subscription.event_type}"
                )

        subscriptions.append(subscription)

    def unsubscribe(
        self,
        subscriber_module: str,
        event_type: str,
    ) -> None:
        event_type = (event_type or "").strip()
        subscriber_module = (subscriber_module or "").strip().lower()

        subscriptions = self._subscriptions.get(event_type)

        if not subscriptions:
            return

        self._subscriptions[event_type] = [
            subscription
            for subscription in subscriptions
            if subscription.subscriber_module.lower()
            != subscriber_module
        ]

        if not self._subscriptions[event_type]:
            del self._subscriptions[event_type]

    def publish(self, event: ModuleEvent) -> List[object]:
        """
        Publish an event to all registered subscribers.

        When an IntegrationRegistry is configured, the publisher must have
        registered integration metadata declaring the event type.

        Subscriber failures are isolated and returned as results rather
        than preventing remaining subscribers from being invoked.
        """

        self._validate_publisher(event)

        results: List[object] = []

        for subscription in self._subscriptions.get(
            event.event_type,
            [],
        ):
            try:
                results.append(subscription.handler(event))
            except Exception as exc:
                results.append(exc)

        return results

    def deliver(
        self,
        event: ModuleEvent,
        subscriber_module: str,
    ) -> object:
        """
        Deliver an event to one specific subscriber.

        This operation is intended for durable delivery processing. Unlike
        publish(), subscriber failures are allowed to propagate so the
        owning Core Job can apply its retry/failure lifecycle.
        """

        self._validate_publisher(event)

        subscriber = (subscriber_module or "").strip().lower()

        if not subscriber:
            raise ValueError(
                "Subscriber module is required for targeted delivery."
            )

        for subscription in self._subscriptions.get(
            event.event_type,
            [],
        ):
            if subscription.subscriber_module.strip().lower() == subscriber:
                return subscription.handler(event)

        raise ValueError(
            "Subscriber is not registered for event type: "
            f"{event.event_type}"
        )

    def _validate_publisher(self, event: ModuleEvent) -> None:
        """
        Validate that the declared publisher owns the event type.

        EventBus does not create or duplicate module authority. It relies on
        the existing IntegrationRegistry integration metadata.
        """

        if self._integration_registry is None:
            return

        publisher = event.publisher_module.strip().lower()

        if not self._integration_registry.has_module_contract(publisher):
            raise ValueError(
                "Event publisher integration contract not registered: "
                f"{publisher}"
            )

        integration_contract = (
            self._integration_registry.get_module_contract(publisher)
        )

        if not integration_contract.provides_event(event.event_type):
            raise ValueError(
                "Event publisher is not authorized to publish event type: "
                f"{event.event_type}"
            )

    def subscribers(
        self,
        event_type: str,
    ) -> List[EventSubscription]:
        return list(
            self._subscriptions.get(
                event_type,
                [],
            )
        )

    def has_subscribers(self, event_type: str) -> bool:
        return bool(
            self._subscriptions.get(
                event_type,
                [],
            )
        )

    def clear(self) -> None:
        self._subscriptions.clear()
