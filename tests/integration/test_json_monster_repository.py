# tests/integration/test_json_monster_repository.py
import tempfile
from pathlib import Path

from src.dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from src.dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from src.dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from src.dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating


def test_upsert_and_get(tmp_path):
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")

    goblin = MonsterDefinition(
        id="goblin",
        name="Goblin",
        size="Small",
        type_="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        speed={"walk": 30},
        ability_scores=AbilityScores(8, 14, 10, 10, 8, 8),
        challenge_rating=ChallengeRating("1/4"),
        xp=50,
    )

    repo.upsert(goblin)
    loaded = repo.get("goblin")

    assert loaded is not None
    assert loaded.name == "Goblin"


def test_list_all(tmp_path):
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")
    assert len(repo.list_all()) == 0
