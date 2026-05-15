# DOMAIN LAYER: stdlib imports only.
from __future__ import annotations
from dataclasses import dataclass, field
from ..value_objects.condition import Condition

@dataclass
class EncounterEntity:
    instance_id: str
    display_name: str
    entity_type: str  # "monster" | "player"
    initiative: int
    is_active: bool = True
    monster_id: str | None = None
    initiative_roll: int | None = None
    current_hp: int | None = None
    max_hp: int | None = None
    conditions: list[Condition] = field(default_factory=list)
