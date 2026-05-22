# tests/integration/test_json_monster_repository.py
import tempfile
from pathlib import Path

from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating


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


def test_upsert_custom_monster_with_rich_fields(tmp_path):
    """Test that custom monsters created via the new form can be persisted with all optional fields."""
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")

    custom = MonsterDefinition(
        id="custom-dragon",
        name="Test Dragon",
        size="Huge",
        type_="dragon",
        alignment="chaotic evil",
        armor_class=18,
        hit_points=150,
        hit_dice="15d12+60",
        speed={"walk": 40, "fly": 80},
        ability_scores=AbilityScores(22, 10, 20, 14, 12, 16),
        challenge_rating=ChallengeRating("8"),
        xp=3900,
        source="Custom",
        saving_throws={"dex": 4, "con": 9, "wis": 5, "cha": 7},
        skills={"perception": 9, "stealth": 4},
        damage_resistances=["fire"],
        damage_immunities=["poison"],
        traits=[{"name": "Legendary Resistance", "description": "Can reroll a save 3/day"}],
        actions=[{"name": "Bite", "description": "Deals piercing + fire damage"}],
        legendary_actions=[{"name": "Tail Attack", "description": "Make a tail attack"}],
    )

    repo.upsert(custom)
    loaded = repo.get("custom-dragon")

    assert loaded is not None
    assert loaded.name == "Test Dragon"
    assert loaded.hit_points == 150
    assert len(loaded.traits) == 1
    assert len(loaded.legendary_actions) == 1
    assert "fire" in loaded.damage_resistances


def test_upsert_updates_existing_monster(tmp_path):
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")

    goblin = MonsterDefinition(id="goblin", name="Goblin", hit_points=7, armor_class=15, size="Small", type_="humanoid", alignment="neutral evil", hit_dice="2d6", speed={}, ability_scores=AbilityScores(8,14,10,10,8,8), challenge_rating=ChallengeRating("1/4"), xp=50)
    repo.upsert(goblin)

    # Update it
    goblin.hit_points = 10
    repo.upsert(goblin)

    loaded = repo.get("goblin")
    assert loaded.hit_points == 10
    assert repo.count() == 1


def test_get_nonexistent_returns_none(tmp_path):
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")
    assert repo.get("nonexistent") is None


def test_count(tmp_path):
    repo = JsonMonsterRepository(path=tmp_path / "monsters.json")
    assert repo.count() == 0

    m1 = MonsterDefinition(id="m1", name="M1", hit_points=10, armor_class=10, size="M", type_="test", alignment="u", hit_dice="1d8", speed={}, ability_scores=AbilityScores(10,10,10,10,10,10), challenge_rating=ChallengeRating("1"), xp=10)
    repo.upsert(m1)
    assert repo.count() == 1
