# domain/entities/encounter.py
# DOMAIN LAYER: stdlib imports only.
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .encounter_entity import EncounterEntity

@dataclass
class Encounter:
    encounter_id: str
    entities: list[EncounterEntity] = field(default_factory=list)
    current_turn_index: int = 0
    round_number: int = 1
    saved_at: datetime | None = None

    def active_entities(self) -> list[EncounterEntity]:
        return [e for e in self.entities if e.is_active]

    def current_entity(self) -> EncounterEntity | None:
        active = self.active_entities()
        if not active:
            return None
        return active[self.current_turn_index % len(active)]
