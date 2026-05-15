# application/commands/rename_entity_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher


@dataclass
class RenameEntityCommand(BaseCommand):
    encounter: Encounter
    instance_id: str
    new_name: str
    publisher: IEventPublisher
    _old_name: str = ""

    def execute(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        self._old_name = entity.display_name
        entity.display_name = self.new_name
        self.publisher.publish("entity_renamed", {"instance_id": self.instance_id, "old_name": self._old_name, "new_name": self.new_name})

    def undo(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        entity.display_name = self._old_name
        self.publisher.publish("entity_renamed", {"instance_id": self.instance_id, "old_name": self.new_name, "new_name": self._old_name})
