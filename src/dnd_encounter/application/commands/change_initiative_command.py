# application/commands/change_initiative_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher

@dataclass
class ChangeInitiativeCommand(BaseCommand):
    encounter: Encounter
    instance_id: str
    new_initiative: int
    publisher: IEventPublisher
    _old_initiative: int = 0

    def execute(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        self._old_initiative = entity.initiative
        entity.initiative = self.new_initiative
        self.publisher.publish("initiative_changed", {
            "instance_id": self.instance_id,
            "old_initiative": self._old_initiative,
            "new_initiative": self.new_initiative
        })

    def undo(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        entity.initiative = self._old_initiative
        self.publisher.publish("initiative_changed", {
            "instance_id": self.instance_id,
            "old_initiative": self.new_initiative,
            "new_initiative": self._old_initiative
        })
