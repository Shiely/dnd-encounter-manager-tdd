# application/services/encounter_service.py
# Orchestrates domain logic and coordinates commands

from __future__ import annotations

from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from dnd_encounter.ports.outbound.i_encounter_repository import IEncounterRepository
from dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository
from dnd_encounter.ports.outbound.i_undo_stack import IUndoStack
from dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller
from dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher

from dnd_encounter.application.commands.add_entity_command import AddEntityCommand
from dnd_encounter.application.commands.edit_hp_command import EditHpCommand
from dnd_encounter.application.commands.remove_entity_command import RemoveEntityCommand
from dnd_encounter.application.commands.toggle_condition_command import ToggleConditionCommand
from dnd_encounter.application.commands.change_initiative_command import ChangeInitiativeCommand
from dnd_encounter.application.commands.rename_entity_command import RenameEntityCommand


class EncounterService:
    def __init__(
        self,
        encounter: Encounter,
        monster_repo: IMonsterRepository,
        encounter_repo: IEncounterRepository,
        undo_stack: IUndoStack,
        dice_roller: IDiceRoller,
        publisher: IEventPublisher,
    ):
        self.encounter = encounter
        self.monster_repo = monster_repo
        self.encounter_repo = encounter_repo
        self.undo_stack = undo_stack
        self.dice_roller = dice_roller
        self.publisher = publisher

    def get_state(self):
        from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

        entities = []
        for entity in self.encounter.entities:
            entities.append(
                EntityRowDTO(
                    instance_id=entity.instance_id,
                    display_name=entity.display_name,
                    entity_type=entity.entity_type,
                    initiative=entity.initiative,
                    current_hp=entity.current_hp,
                    max_hp=entity.max_hp,
                    conditions=[c.value for c in entity.conditions],
                    monster_id=entity.monster_id,
                )
            )

        return EncounterStateDTO(
            encounter_id=self.encounter.encounter_id,
            round_number=self.encounter.round_number,
            entities=entities,
            undo_available=not self.undo_stack.is_empty(),
        )

    def add_monster(self, monster_id: str):
        cmd = AddEntityCommand(
            encounter=self.encounter,
            monster_repo=self.monster_repo,
            monster_id=monster_id,
            dice_roller=self.dice_roller,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def add_player(self, name: str, initiative: int, max_hp: int):
        """Add a player character to the encounter."""
        from dnd_encounter.domain.entities.encounter_entity import EncounterEntity

        player = EncounterEntity(
            instance_id=f"player_{name.lower().replace(' ', '_')}",
            display_name=name,
            entity_type="player",
            initiative=initiative,
            current_hp=max_hp,
            max_hp=max_hp,
            monster_id=None,
        )
        self.encounter.entities.append(player)
        self.encounter_repo.save(self.encounter)

    def edit_hp(self, instance_id: str, new_hp: int):
        cmd = EditHpCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_hp=new_hp,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def remove_entity(self, instance_id: str):
        cmd = RemoveEntityCommand(
            encounter=self.encounter,
            instance_id=instance_id,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def toggle_condition(self, instance_id: str, condition):
        cmd = ToggleConditionCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            condition=condition,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def change_initiative(self, instance_id: str, new_initiative: int):
        cmd = ChangeInitiativeCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_initiative=new_initiative,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def rename_entity(self, instance_id: str, new_name: str):
        cmd = RenameEntityCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_name=new_name,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def advance_turn(self):
        if self.encounter.entities:
            self.encounter.current_turn_index = (self.encounter.current_turn_index + 1) % len(self.encounter.entities)
            if self.encounter.current_turn_index == 0:
                self.encounter.round_number += 1
            self.encounter_repo.save(self.encounter)
