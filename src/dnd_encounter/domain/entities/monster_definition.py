# domain/entities/monster_definition.py
# Monster definition value object

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..value_objects.ability_scores import AbilityScores
from ..value_objects.challenge_rating import ChallengeRating


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
    speed: dict[str, Any]
    ability_scores: AbilityScores
    challenge_rating: ChallengeRating
    xp: int
    source: str = "custom"

    def __post_init__(self):
        if isinstance(self.ability_scores, dict):
            self.ability_scores = AbilityScores(**self.ability_scores)
        if isinstance(self.challenge_rating, str):
            self.challenge_rating = ChallengeRating(self.challenge_rating)
