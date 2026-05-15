# src/dnd_encounter/bootstrap.py
# Wires everything together and launches the app

from PySide6.QtWidgets import QApplication
import sys
from typing import Any

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository
from dnd_encounter.ui.main_window import MainWindow


def seed_default_monsters(monster_repo: JsonMonsterRepository) -> None:
    """Seed the monster repository with default monsters if empty."""
    if monster_repo.count() > 0:
        return

    from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
    from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
    from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

    defaults = [
        MonsterDefinition(
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
        ),
        MonsterDefinition(
            id="orc",
            name="Orc",
            size="Medium",
            type_="humanoid",
            alignment="chaotic evil",
            armor_class=13,
            hit_points=15,
            hit_dice="2d8+6",
            speed={"walk": 30},
            ability_scores=AbilityScores(16, 12, 16, 7, 11, 10),
            challenge_rating=ChallengeRating("1/2"),
            xp=100,
        ),
        MonsterDefinition(
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
        ),
        MonsterDefinition(
            id="troll",
            name="Troll",
            size="Large",
            type_="giant",
            alignment="chaotic evil",
            armor_class=15,
            hit_points=84,
            hit_dice="8d10+40",
            speed={"walk": 30},
            ability_scores=AbilityScores(18, 13, 20, 7, 9, 7),
            challenge_rating=ChallengeRating("5"),
            xp=1800,
        ),
    ]

    for monster in defaults:
        monster_repo.upsert(monster)


class SimpleUndoStack:
    def __init__(self) -> None:
        self._stack: list[Any] = []

    def push(self, cmd: Any) -> None:  # noqa: ANN401
        self._stack.append(cmd)

    def pop(self) -> Any | None:  # noqa: ANN401
        return self._stack.pop() if self._stack else None

    def is_empty(self) -> bool:
        return len(self._stack) == 0


def bootstrap() -> None:
    app = QApplication(sys.argv)

    monster_repo = JsonMonsterRepository()
    encounter_repo = JsonEncounterRepository()
    undo_stack = SimpleUndoStack()

    # Seed default monsters
    seed_default_monsters(monster_repo)

    class SimpleDiceRoller:
        def roll_d20(self) -> int:
            import random

            return random.randint(1, 20)

    dice_roller = SimpleDiceRoller()

    class SimplePublisher:
        def publish(self, event_type: str, payload: dict) -> None:
            print(f"[EVENT] {event_type}: {payload}")

    publisher = SimplePublisher()

    from dnd_encounter.domain.entities.encounter import Encounter

    encounter = Encounter(encounter_id="default")

    service = EncounterService(
        encounter=encounter,
        monster_repo=monster_repo,
        encounter_repo=encounter_repo,
        undo_stack=undo_stack,
        dice_roller=dice_roller,
        publisher=publisher,
    )

    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    bootstrap()
