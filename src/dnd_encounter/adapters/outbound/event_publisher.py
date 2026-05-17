# adapters/outbound/event_publisher.py
# Qt signal-based event publisher for reactive GUI updates

from PySide6.QtCore import QObject, Signal


class EventPublisher(QObject):
    """Publishes domain events. Emits Qt signals so GUI components can react."""

    event_fired = Signal(str, dict)  # event_type, payload

    def __init__(self):
        super().__init__()
        self._subscribers = []

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def publish(self, event_type: str, payload: dict):
        print(f"[EVENT] {event_type}: {payload}")
        # Notify traditional subscribers
        for subscriber in self._subscribers:
            subscriber(event_type, payload)
        # Emit Qt signal for GUI components
        self.event_fired.emit(event_type, payload)

    def publish_simple(self, event):
        for subscriber in self._subscribers:
            subscriber(event)
