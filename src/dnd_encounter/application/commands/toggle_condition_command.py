# application/commands/toggle_condition_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.value_objects.condition import Condition
from src.dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher

@dataclass
class ToggleConditionCommand(BaseCommand):
    encounter: Encounter
    instance_id: str
    condition: Condition
    publisher: IEventPublisher
    _old_conditions: list[Condition] = None

    def execute(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        self._old_conditions = list(entity.conditions)

        if self.condition in entity.conditions:
            entity.conditions.remove(self.condition)
        else:
            entity.conditions.append(self.condition)

        self.publisher.publish("condition_toggled", {
            "instance_id": self.instance_id,
            "condition": self.condition.value,
            "active": self.condition in entity.conditions
        })

    def undo(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        entity.conditions = self._old_conditions
        self.publisher.publish("condition_restored", {"instance_id": self.instance_id})
