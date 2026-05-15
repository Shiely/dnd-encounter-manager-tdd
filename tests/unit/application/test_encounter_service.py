# tests/unit/application/test_encounter_service.py
# Clean tests using real implementations

import pytest
import tempfile
from pathlib import Path

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository
from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.adapters.outbound.in_memory_undo_stack import InMemoryUndoStack
from dnd_encounter.adapters.outbound.dice_roller import DiceRoller
from dnd_encounter.adapters.outbound.event_publisher import EventPublisher


def test_add_monster():
    encounter = Encounter(encounter_id="test")
    from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
    from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
    from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

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

    with tempfile.TemporaryDirectory() as tmpdir:
        monster_repo = JsonMonsterRepository(path=Path(tmpdir) / "monsters.json")
        monster_repo.upsert(goblin)
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=monster_repo,
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        result = service.add_monster("goblin")
        assert len(result.entities) == 1
        assert result.entities[0].display_name.startswith("Goblin #")


def test_add_player():
    encounter = Encounter(encounter_id="test")
    with tempfile.TemporaryDirectory() as tmpdir:
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=None,  # type: ignore[arg-type]
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        service.add_player("Aragorn", 18, 45)
        assert len(encounter.entities) == 1
        assert encounter.entities[0].display_name == "Aragorn"


def test_add_player_multiple():
    encounter = Encounter(encounter_id="test")
    with tempfile.TemporaryDirectory() as tmpdir:
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=None,  # type: ignore[arg-type]
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        service.add_player("Aragorn", 18, 45)
        service.add_player("Legolas", 20, 40)

        assert len(encounter.entities) == 2
        assert encounter.entities[0].display_name == "Aragorn"
        assert encounter.entities[1].display_name == "Legolas"
