# src/dnd_encounter/bootstrap.py
# Wires everything together and launches the app

from PySide6.QtWidgets import QApplication
import sys

from dnd_encounter.application.services.encounter_service import EncounterService

from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository


from dnd_encounter.ui.main_window import MainWindow


class SimpleUndoStack:
    def __init__(self):
        self._stack = []

    def push(self, cmd):
        self._stack.append(cmd)

    def pop(self):
        return self._stack.pop() if self._stack else None

    def is_empty(self):
        return len(self._stack) == 0


def bootstrap():
    app = QApplication(sys.argv)

    # Repositories
    monster_repo = JsonMonsterRepository()
    encounter_repo = JsonEncounterRepository()

    # Simple undo stack (in-memory for now)
    undo_stack = SimpleUndoStack()

    # Dice roller (simple)
    class SimpleDiceRoller:
        def roll_d20(self):
            import random
            return random.randint(1, 20)

    dice_roller = SimpleDiceRoller()

    # Event publisher (simple)
    class SimplePublisher:
        def publish(self, event_type, payload):
            print(f"[EVENT] {event_type}: {payload}")

    publisher = SimplePublisher()

    # Create a default encounter
    from dnd_encounter.domain.entities.encounter import Encounter
    encounter = Encounter(encounter_id="default")

    # Service
    service = EncounterService(
        encounter=encounter,
        monster_repo=monster_repo,
        encounter_repo=encounter_repo,
        undo_stack=undo_stack,
        dice_roller=dice_roller,
        publisher=publisher,
    )

    # Main window
    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    bootstrap()
