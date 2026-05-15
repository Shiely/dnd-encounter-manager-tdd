# application/commands/edit_hp_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.rules.hp_rules import apply_hp_edit, is_auto_remove
from src.dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher


@dataclass
class EditHpCommand(BaseCommand):
    encounter: Encounter
    instance_id: str
    new_hp: int
    publisher: IEventPublisher
    _old_hp: int = 0
    _was_active: bool = True

    def execute(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        assert entity.current_hp is not None, "HP edit called on player entity"
        self._old_hp = entity.current_hp
        self._was_active = entity.is_active

        entity.current_hp = apply_hp_edit(entity.current_hp, self.new_hp)

        if is_auto_remove(entity.current_hp) and entity.entity_type == "monster":
            entity.is_active = False
            self.publisher.publish("entity_auto_removed", {"instance_id": self.instance_id})

        self.publisher.publish(
            "hp_changed",
            {
                "instance_id": self.instance_id,
                "old_hp": self._old_hp,
                "new_hp": entity.current_hp,
            },
        )

    def undo(self) -> None:
        entity = next(e for e in self.encounter.entities if e.instance_id == self.instance_id)
        assert entity.current_hp is not None
        entity.current_hp = self._old_hp
        entity.is_active = self._was_active
        self.publisher.publish(
            "hp_changed",
            {
                "instance_id": self.instance_id,
                "old_hp": entity.current_hp,
                "new_hp": self._old_hp,
            },
        )
