# tests/unit/ui/conftest.py
# Fixtures for GUI tests
#
# IMPORTANT: Force headless/offscreen Qt platform so GUI tests never pop up
# real windows during normal development or CI runs.
# This must be set *before* any PySide6/Qt imports happen.
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from unittest.mock import Mock


@pytest.fixture
def stub_service():
    """Simple stub EncounterService for GUI tests."""
    service = Mock()

    # Create simple mock entities
    e1 = Mock(
        instance_id="e1",
        display_name="Aragorn",
        entity_type="player",
        initiative=18,
        current_hp=45,
        max_hp=45,
        conditions=[],
        is_active=True,
    )
    e2 = Mock(
        instance_id="e2",
        display_name="Goblin #1",
        entity_type="monster",
        initiative=15,
        current_hp=7,
        max_hp=7,
        conditions=["Poisoned"],
        is_active=True,
    )
    e3 = Mock(
        instance_id="e3",
        display_name="Orc #2",
        entity_type="monster",
        initiative=12,
        current_hp=0,
        max_hp=15,
        conditions=["Dead"],
        is_active=False,
    )

    # Mock encounter with entities list
    encounter = Mock()
    encounter.entities = [e1, e2, e3]
    encounter.round_number = 1
    encounter.current_turn_index = 0

    service.encounter = encounter

    # Mock methods
    service.get_state = Mock(
        return_value=Mock(
            encounter_id="test",
            round_number=1,
            entities=[e1, e2, e3],
            undo_available=False,
        )
    )
    service.advance_turn = Mock()
    service.add_monster = Mock()
    service.edit_hp = Mock()
    service.remove_entity = Mock()
    service.rename_entity = Mock()
    service.change_initiative = Mock()

    return service


# --- Real service fixture for automated flow / integration tests ---

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.adapters.outbound.in_memory_undo_stack import InMemoryUndoStack
from dnd_encounter.adapters.outbound.dice_roller import DiceRoller
from dnd_encounter.adapters.outbound.event_publisher import EventPublisher
from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.bootstrap import seed_default_monsters


class _DummyEncounterRepo:
    """No-op repository so we don't need real file I/O during flow tests."""
    def save(self, encounter):
        pass

    def load(self):
        return None


@pytest.fixture
def real_service():
    """
    A fully functional EncounterService using in-memory components.
    Useful for automated GUI flow tests that exercise real logic
    (adding, condition toggling, sorting, undo, etc.).
    """
    monster_repo = JsonMonsterRepository()
    seed_default_monsters(monster_repo)   # give us goblins, orcs, etc.

    encounter = Encounter(encounter_id="test-flow")
    undo_stack = InMemoryUndoStack(maxlen=5)
    dice_roller = DiceRoller()
    publisher = EventPublisher()
    dummy_repo = _DummyEncounterRepo()

    service = EncounterService(
        encounter=encounter,
        monster_repo=monster_repo,
        encounter_repo=dummy_repo,
        undo_stack=undo_stack,
        dice_roller=dice_roller,
        publisher=publisher,
    )
    return service


# --- New architecture UI fixtures (used by test_new_main_window.py) ---

from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO


def _make_sample_state() -> EncounterStateDTO:
    """Internal helper to build a deterministic sample state for tests."""
    entities = [
        EntityRowDTO(
            instance_id="p1",
            display_name="Aragorn",
            entity_type="player",
            initiative=18,
            current_hp=None,
            max_hp=None,
            conditions=[],
            is_current_turn=True,
            is_active=True,
        ),
        EntityRowDTO(
            instance_id="m1",
            display_name="Goblin",
            entity_type="monster",
            initiative=15,
            current_hp=7,
            max_hp=7,
            conditions=["Poisoned"],
            is_current_turn=False,
            is_active=True,
        ),
    ]
    return EncounterStateDTO(
        encounter_id="test-enc",
        round_number=1,
        entities=entities,
        undo_available=False,
    )


@pytest.fixture
def sample_state() -> EncounterStateDTO:
    """A realistic EncounterStateDTO for testing the new MainWindow and widgets."""
    return _make_sample_state()


@pytest.fixture
def new_stub_service():
    """Mock EncounterService returning proper DTOs for the new UI tests."""
    from unittest.mock import Mock

    service = Mock()
    service.get_state = Mock(return_value=_make_sample_state())
    service.advance_turn = Mock()
    service.add_monster = Mock()
    service.add_player = Mock()
    service.remove_entity = Mock()
    service.edit_hp = Mock()
    service.toggle_condition = Mock()
    service.rename_entity = Mock()
    service.change_initiative = Mock()
    return service
