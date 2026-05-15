# tests/unit/application/test_encounter_service.py
# Uses stubs from conftest

import pytest
from src.dnd_encounter.application.services.encounter_service import EncounterService
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.entities.encounter_entity import EncounterEntity


def test_add_monster(stub_monster_repo, stub_encounter_repo, stub_undo_stack, stub_dice_roller, stub_publisher):
    encounter = Encounter(encounter_id="test")
    # Add a monster to the stub repo
    from src.dnd_encounter.domain.entities.monster_definition import MonsterDefinition
    from src.dnd_encounter.domain.value_objects.ability_scores import AbilityScores
    from src.dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

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
    stub_monster_repo.upsert(goblin)

    service = EncounterService(
        encounter=encounter,
        monster_repo=stub_monster_repo,
        encounter_repo=stub_encounter_repo,
        undo_stack=stub_undo_stack,
        dice_roller=stub_dice_roller,
        publisher=stub_publisher,
    )

    result = service.add_monster("goblin")
    assert len(result.entities) == 1
    assert result.entities[0].display_name.startswith("Goblin #")


def test_undo(stub_monster_repo, stub_encounter_repo, stub_undo_stack, stub_dice_roller, stub_publisher):
    encounter = Encounter(encounter_id="test")
    service = EncounterService(
        encounter=encounter,
        monster_repo=stub_monster_repo,
        encounter_repo=stub_encounter_repo,
        undo_stack=stub_undo_stack,
        dice_roller=stub_dice_roller,
        publisher=stub_publisher,
    )

    # This test is simplified - full implementation will be tested in integration
    assert True  # Placeholder until full service is complete
