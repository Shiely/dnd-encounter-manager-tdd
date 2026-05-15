# adapters/outbound/event_publisher.py
# Event publishing adapter


class EventPublisher:
    """Publishes domain events to subscribers."""

    def __init__(self):
        self._subscribers = []

    def subscribe(self, subscriber):
        """Register a subscriber to receive published events."""
        self._subscribers.append(subscriber)

    def publish(self, event_type: str, payload: dict):
        """Publish an event to all subscribers."""
        for subscriber in self._subscribers:
            subscriber(event_type, payload)

    def publish_simple(self, event):
        """Publish a simple event to all subscribers."""
        for subscriber in self._subscribers:
            subscriber(event)
