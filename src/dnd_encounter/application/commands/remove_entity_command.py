# application/commands/remove_entity_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher


@dataclass
class RemoveEntityCommand(BaseCommand):
    encounter: Encounter
    instance_id: str
    publisher: IEventPublisher
    _was_active: bool = True

    def execute(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        self._was_active = entity.is_active
        entity.is_active = False
        self.publisher.publish("entity_removed", {"instance_id": self.instance_id})

    def undo(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        entity.is_active = self._was_active
        self.publisher.publish("entity_restored", {"instance_id": self.instance_id})
