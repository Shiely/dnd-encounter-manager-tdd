#!/usr/bin/env python
"""
Convenience launcher for the new UI (adapters/inbound/desktop_ui).

This is the recommended way to run the new MainWindow during development
and manual testing.

Usage:
    uv run python run_ui.py

Optional: You can also run it with offscreen mode for quick checks:
    QT_QPA_PLATFORM=offscreen uv run python run_ui.py
"""

from PySide6.QtWidgets import QApplication
import sys

from dnd_encounter.adapters.inbound.desktop_ui.main_window import MainWindow
from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository
from dnd_encounter.adapters.outbound.in_memory_undo_stack import InMemoryUndoStack
from dnd_encounter.adapters.outbound.dice_roller import DiceRoller
from dnd_encounter.adapters.outbound.event_publisher import EventPublisher
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.bootstrap import seed_default_monsters


def main() -> None:
    app = QApplication(sys.argv)

    # Real repositories (data persists in user data dir)
    monster_repo = JsonMonsterRepository()
    encounter_repo = JsonEncounterRepository()

    # Undo stack (5 levels, matching the architecture spec)
    undo_stack = InMemoryUndoStack(maxlen=5)

    dice_roller = DiceRoller()
    publisher = EventPublisher()

    # Ensure we have some monsters available
    seed_default_monsters(monster_repo)

    # Fresh encounter for this run
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
    main()
