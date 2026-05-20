# tests/unit/ui/conftest.py
# Fixtures for GUI tests

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
    service.get_state = Mock(return_value=Mock(
        encounter_id="test",
        round_number=1,
        entities=[e1, e2, e3],
        undo_available=False,
    ))
    service.advance_turn = Mock()
    service.add_monster = Mock()
    service.edit_hp = Mock()
    service.remove_entity = Mock()
    service.rename_entity = Mock()
    service.change_initiative = Mock()

    return service
