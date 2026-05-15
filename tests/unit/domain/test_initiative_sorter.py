# tests/unit/domain/test_initiative_sorter.py
# DOMAIN LAYER TEST

import random
from src.dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from src.dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from src.dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from src.dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating
from src.dnd_encounter.domain.rules.initiative_sorter import sort_entities


def test_basic_sort_descending():
    entities = [
        EncounterEntity("e1", "Goblin #1", "monster", 12, monster_id="goblin"),
        EncounterEntity("e2", "Player", "player", 18),
    ]
    defs = {}
    result = sort_entities(entities, defs)
    assert [e.initiative for e in result] == [18, 12]


def test_tie_step1_higher_dex_wins():
    # Same initiative, higher dex wins
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
        ability_scores=AbilityScores(8, 14, 10, 10, 8, 8),  # dex=14 → +2
        challenge_rating=ChallengeRating("1/4"),
        xp=50,
    )
    orc = MonsterDefinition(
        id="orc",
        name="Orc",
        size="Medium",
        type_="humanoid",
        alignment="chaotic evil",
        armor_class=13,
        hit_points=15,
        hit_dice="2d8+2",
        speed={"walk": 30},
        ability_scores=AbilityScores(16, 12, 14, 7, 11, 10),  # dex=12 → +1
        challenge_rating=ChallengeRating("1/2"),
        xp=100,
    )
    entities = [
        EncounterEntity("e1", "Goblin #1", "monster", 10, monster_id="goblin"),
        EncounterEntity("e2", "Orc #1", "monster", 10, monster_id="orc"),
    ]
    defs = {"goblin": goblin, "orc": orc}
    result = sort_entities(entities, defs)
    assert result[0].display_name == "Goblin #1"  # higher dex wins


def test_tie_step2_player_beats_monster():
    entities = [
        EncounterEntity("e1", "Goblin #1", "monster", 15, monster_id="goblin"),
        EncounterEntity("e2", "Player", "player", 15),
    ]
    defs = {}
    result = sort_entities(entities, defs)
    assert result[0].display_name == "Player"


def test_tie_step3_higher_cr_wins():
    # Same initiative, same dex, higher CR wins between monsters
    low_cr = MonsterDefinition(
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
    high_cr = MonsterDefinition(
        id="ogre",
        name="Ogre",
        size="Large",
        type_="giant",
        alignment="chaotic evil",
        armor_class=11,
        hit_points=59,
        hit_dice="7d10+21",
        speed={"walk": 40},
        ability_scores=AbilityScores(19, 8, 16, 5, 7, 7),
        challenge_rating=ChallengeRating("2"),
        xp=450,
    )
    entities = [
        EncounterEntity("e1", "Goblin #1", "monster", 12, monster_id="goblin"),
        EncounterEntity("e2", "Ogre #1", "monster", 12, monster_id="ogre"),
    ]
    defs = {"goblin": low_cr, "ogre": high_cr}
    result = sort_entities(entities, defs)
    assert result[0].display_name == "Ogre #1"


def test_tie_prng():
    entities = [
        EncounterEntity("e1", "Goblin #1", "monster", 10, monster_id="goblin"),
        EncounterEntity("e2", "Goblin #2", "monster", 10, monster_id="goblin"),
    ]
    defs = {}
    rng = random.Random(42)  # deterministic
    result = sort_entities(entities, defs, rng=rng)
    assert len(result) == 2


def test_empty_list():
    result = sort_entities([], {})
    assert result == []


def test_single_entity():
    e = EncounterEntity("e1", "Solo", "player", 20)
    result = sort_entities([e], {})
    assert result == [e]
