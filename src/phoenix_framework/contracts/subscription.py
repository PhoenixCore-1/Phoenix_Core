"""Phoenix Generic Framework event subscription contract."""

from dataclasses import dataclass
from typing import Any, Callable


EventHandler = Callable[[Any], object]


@dataclass(frozen=True)
class EventSubscription:
    """
    Runtime registration of a module event subscriber.

    Subscribers consume published events. They do not become owners of
    the event or the publishing module's domain data.
    """

    subscriber_module: str
    event_type: str
    handler: EventHandler

    def __post_init__(self) -> None:
        if not self.subscriber_module.strip():
            raise ValueError("Subscriber module is required.")

        if not self.event_type.strip():
            raise ValueError("Event type is required.")
