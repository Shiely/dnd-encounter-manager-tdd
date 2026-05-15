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
from src.dnd_encounter.application.commands.add_entity_command import AddEntityCommand
from src.dnd_encounter.application.commands.edit_hp_command import EditHpCommand
# ... other commands will be imported as needed

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

    # Other methods (edit_hp, toggle_condition, advance_turn, undo, etc.) will be added in next commits
    def get_state(self) -> EncounterStateDTO:
        return self._to_dto()
