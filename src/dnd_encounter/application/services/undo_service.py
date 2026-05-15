# application/services/undo_service.py
from __future__ import annotations
from dataclasses import dataclass
from dnd_encounter.ports.outbound.i_undo_stack import IUndoStack
from dnd_encounter.ports.outbound.i_encounter_repository import IEncounterRepository
from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO


@dataclass
class UndoService:
    undo_stack: IUndoStack
    encounter_repo: IEncounterRepository

    def undo(self) -> EncounterStateDTO:
        if self.undo_stack.is_empty():
            return EncounterStateDTO(encounter_id="", round_number=1, error="Nothing to undo")
        cmd = self.undo_stack.pop()
        if cmd:
            cmd.undo()
        self.encounter_repo.save(None)  # placeholder
        # In real version we'd return proper DTO
        return EncounterStateDTO(encounter_id="", round_number=1)
