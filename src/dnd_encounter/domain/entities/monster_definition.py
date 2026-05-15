# DOMAIN LAYER: stdlib imports only.
from __future__ import annotations
from dataclasses import dataclass, field
from .ability_scores import AbilityScores
from .challenge_rating import ChallengeRating


@dataclass
class MonsterDefinition:
    id: str
    name: str
    size: str
    type_: str
    alignment: str
    armor_class: int
    hit_points: int
    hit_dice: str
    speed: dict
    ability_scores: AbilityScores
    challenge_rating: ChallengeRating
    xp: int
    source: str = "custom"
