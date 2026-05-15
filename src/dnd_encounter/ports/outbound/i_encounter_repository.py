# ports/outbound/i_encounter_repository.py
from typing import Protocol
from ...domain.entities.encounter import Encounter


class IEncounterRepository(Protocol):
    def load(self) -> Encounter | None: ...
    def save(self, encounter: Encounter) -> None: ...
