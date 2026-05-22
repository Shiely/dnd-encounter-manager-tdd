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

    # New rich fields (all optional for backward compatibility)
    saving_throws: dict[str, int] = field(default_factory=dict)
    skills: dict[str, int] = field(default_factory=dict)

    damage_resistances: list[str] = field(default_factory=list)
    damage_immunities: list[str] = field(default_factory=list)
    damage_vulnerabilities: list[str] = field(default_factory=list)
    condition_immunities: list[str] = field(default_factory=list)

    senses: dict[str, Any] = field(default_factory=dict)
    languages: list[str] = field(default_factory=list)

    traits: list[dict[str, str]] = field(default_factory=list)
    actions: list[dict[str, str]] = field(default_factory=list)
    bonus_actions: list[dict[str, str]] = field(default_factory=list)
    reactions: list[dict[str, str]] = field(default_factory=list)
    legendary_actions: list[dict[str, str]] = field(default_factory=list)

    spellcasting: list[dict[str, Any]] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)

    # Image support
    has_token: bool = False
    has_fluff_image: bool = False
    image_path: str | None = None   # relative path, e.g. "bestiary/tokens/Ancient_Red_Dragon.png"

    def __post_init__(self):
        if isinstance(self.ability_scores, dict):
            self.ability_scores = AbilityScores(**self.ability_scores)
        if isinstance(self.challenge_rating, (str, dict)):
            val = self.challenge_rating.get("value") if isinstance(self.challenge_rating, dict) else self.challenge_rating
            self.challenge_rating = ChallengeRating(str(val))
