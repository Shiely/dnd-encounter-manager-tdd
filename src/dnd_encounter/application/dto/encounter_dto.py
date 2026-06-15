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
    # Phase 4 additive enrichment (deliverable 1): core combat stats from bestiary for glance in StatBlockPanel.
    # Optional + defaulted for 100% backward compat with all existing call sites, sample_state, stubs, manual constructions.
    ac: int | None = None
    speed: str | None = None  # formatted e.g. "30 ft." or full for simplicity in DTO
    cr: str | None = None
    # Phase 5 additive (P4-style for compat): xp value awarded for defeating this monster (from MonsterDefinition.xp via existing monster_repo seam in service).
    # Optional + default None so 100% backward compat with all pre-Phase5 call sites, sample_state, stubs, manual EntityRowDTO(...,) constructions, P4 tests.
    xp: int | None = None


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
