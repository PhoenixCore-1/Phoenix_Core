"""In-process realtime publisher implementations for Phoenix communications."""

from phoenix_core.communications.contracts import RealtimeEvent


class InMemoryRealtimePublisher:
    """Simple publisher used by tests and local development.

    This implementation deliberately has no transport dependency. It records
    published events so callers can verify the realtime contract.
    """

    def __init__(self):
        self.events: list[RealtimeEvent] = []

    def publish(self, event: RealtimeEvent) -> None:
        self.events.append(event)

    def clear(self) -> None:
        self.events.clear()
