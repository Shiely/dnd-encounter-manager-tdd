# application/dto/encounter_dto.py
from dataclasses import dataclass, field


@dataclass
class EntityRowDTO:
    instance_id: str
    display_name: str
    entity_type: str  # "monster" | "player"
    initiative: int
    current_hp: int | None  # None for player entities
    max_hp: int | None  # None for player entities
    conditions: list[str]  # condition names as strings
    is_current_turn: bool
    is_active: bool
    monster_id: str | None = None   # populated for monsters so StatBlock can fetch rich definition


@dataclass
class EncounterStateDTO:
    encounter_id: str
    round_number: int
    entities: list[EntityRowDTO] = field(default_factory=list)
    undo_available: bool = False
    error: str | None = None  # non-None signals a rejected operation


@dataclass
class MonsterSummaryDTO:
    monster_id: str
    name: str
    cr: str
    hp: int
    ac: int
    source: str
