# ports/outbound/i_event_publisher.py
from typing import Protocol, Any

class IEventPublisher(Protocol):
    def publish(self, event_type: str, payload: dict[str, Any]) -> None: ...
