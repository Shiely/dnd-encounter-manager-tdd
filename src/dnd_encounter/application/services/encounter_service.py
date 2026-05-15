# application/services/encounter_service.py
from __future__ import annotations
from dataclasses import dataclass
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from src.dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository
from src.dnd_encounter.ports.outbound.i_encounter_repository import IEncounterRepository
from src.dnd_encounter.ports.outbound.i_undo_stack import IUndoStack
from src.dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller
from src.dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher
from src.dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO, MonsterSummaryDTO
from src.dnd_encounter.application.commands import (
    AddEntityCommand,
    EditHpCommand,
    ToggleConditionCommand,
    RemoveEntityCommand,
    RenameEntityCommand,
    ChangeInitiativeCommand,
)

@dataclass
class EncounterService:
    encounter: Encounter
    monster_repo: IMonsterRepository
    encounter_repo: IEncounterRepository
    undo_stack: IUndoStack
    dice_roller: IDiceRoller
    publisher: IEventPublisher

    def _to_dto(self) -> EncounterStateDTO:
        entities = []
        for i, e in enumerate(self.encounter.entities):
            if not e.is_active:
                continue
            entities.append(EntityRowDTO(
                instance_id=e.instance_id,
                display_name=e.display_name,
                entity_type=e.entity_type,
                initiative=e.initiative,
                current_hp=e.current_hp,
                max_hp=e.max_hp,
                conditions=[c.value for c in e.conditions],
                is_current_turn=(i == self.encounter.current_turn_index),
                is_active=e.is_active,
            ))
        return EncounterStateDTO(
            encounter_id=self.encounter.encounter_id,
            round_number=self.encounter.round_number,
            entities=entities,
            undo_available=not self.undo_stack.is_empty(),
        )

    def add_monster(self, monster_id: str) -> EncounterStateDTO:
        cmd = AddEntityCommand(
            encounter=self.encounter,
            monster_id=monster_id,
            monster_repo=self.monster_repo,
            dice_roller=self.dice_roller,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def edit_hp(self, instance_id: str, new_hp: int) -> EncounterStateDTO:
        cmd = EditHpCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_hp=new_hp,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def toggle_condition(self, instance_id: str, condition_name: str) -> EncounterStateDTO:
        from src.dnd_encounter.domain.value_objects.condition import Condition
        condition = Condition(condition_name)
        cmd = ToggleConditionCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            condition=condition,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def remove_entity(self, instance_id: str) -> EncounterStateDTO:
        cmd = RemoveEntityCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def advance_turn(self) -> EncounterStateDTO:
        if self.encounter.entities:
            self.encounter.current_turn_index = (self.encounter.current_turn_index + 1) % len(self.encounter.entities)
            if self.encounter.current_turn_index == 0:
                self.encounter.round_number += 1
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def undo(self) -> EncounterStateDTO:
        if self.undo_stack.is_empty():
            return self._to_dto()
        cmd = self.undo_stack.pop()
        if cmd:
            cmd.undo()
        self.encounter_repo.save(self.encounter)
        return self._to_dto()

    def get_state(self) -> EncounterStateDTO:
        return self._to_dto()

    def get_monster_definition(self, monster_id: str) -> MonsterSummaryDTO | None:
        definition = self.monster_repo.get(monster_id)
        if not definition:
            return None
        return MonsterSummaryDTO(
            monster_id=definition.id,
            name=definition.name,
            cr=str(definition.challenge_rating.value),
            hp=definition.hit_points,
            ac=definition.armor_class,
            source=definition.source,
        )
