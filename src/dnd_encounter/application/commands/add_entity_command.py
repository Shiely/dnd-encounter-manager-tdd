# application/commands/add_entity_command.py
# Command to add a monster to an encounter

from __future__ import annotations

from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository
from dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller
from dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher


class AddEntityCommand:
    def __init__(
        self,
        encounter: Encounter,
        monster_repo: IMonsterRepository,
        monster_id: str,
        dice_roller: IDiceRoller,
        publisher: IEventPublisher | None = None,
    ):
        self.encounter = encounter
        self.monster_repo = monster_repo
        self.monster_id = monster_id
        self.dice_roller = dice_roller
        self.publisher = publisher

    def execute(self) -> None:
        definition = self.monster_repo.get(self.monster_id)
        if not definition:
            raise ValueError(f"Monster {self.monster_id} not found")

        roll = self.dice_roller.roll_d20()
        initiative = roll + definition.ability_scores.dex_modifier

        entity = EncounterEntity(
            instance_id=f"{self.monster_id}_{len(self.encounter.entities)}",
            display_name=f"{definition.name} #{len([e for e in self.encounter.entities if e.monster_id == self.monster_id]) + 1}",
            entity_type="monster",
            initiative=initiative,
            current_hp=definition.hit_points,
            max_hp=definition.hit_points,
            monster_id=self.monster_id,
        )

        self.encounter.entities.append(entity)

        if self.publisher:
            self.publisher.publish("entity_added", {"entity": entity})

    def undo(self) -> None:
        if self.encounter.entities:
            self.encounter.entities.pop()
