# application/commands/add_entity_command.py
from __future__ import annotations
from dataclasses import dataclass
from .base_command import BaseCommand
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from src.dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from src.dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository
from src.dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller
from src.dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher

import uuid


@dataclass
class AddEntityCommand(BaseCommand):
    encounter: Encounter
    monster_id: str
    monster_repo: IMonsterRepository
    dice_roller: IDiceRoller
    publisher: IEventPublisher
    _snapshot: EncounterEntity | None = None

    def execute(self) -> None:
        definition: MonsterDefinition | None = self.monster_repo.get(self.monster_id)
        if definition is None:
            raise ValueError(f"Monster {self.monster_id} not found")

        instance_id: str = str(uuid.uuid4())
        display_name: str = f"{definition.name} #{len([e for e in self.encounter.entities if e.monster_id == self.monster_id]) + 1}"

        entity: EncounterEntity = EncounterEntity(
            instance_id=instance_id,
            display_name=display_name,
            entity_type="monster",
            initiative=0,
            monster_id=self.monster_id,
            current_hp=definition.hit_points,
            max_hp=definition.hit_points,
        )

        roll: int = self.dice_roller.roll_d20()
        entity.initiative_roll = roll
        entity.initiative = roll + definition.ability_scores.dex_modifier

        self.encounter.entities.append(entity)
        self._snapshot = entity

        self.publisher.publish("entity_added", {"instance_id": instance_id})

    def undo(self) -> None:
        if self._snapshot is not None:
            self._snapshot.is_active = False
            self.publisher.publish("entity_removed", {"instance_id": self._snapshot.instance_id})
