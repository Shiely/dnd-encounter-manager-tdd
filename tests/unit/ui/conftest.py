# tests/unit/ui/conftest.py
# Fixtures for GUI tests

import pytest
from unittest.mock import Mock


@pytest.fixture
def stub_service():
    """Stub EncounterService for UI testing with realistic state including is_current_turn and is_active."""
    service = Mock()

    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

    # Realistic state with current turn and active/inactive entities
    entities = [
        EntityRowDTO(
            instance_id="e1",
            display_name="Aragorn",
            entity_type="player",
            initiative=18,
            current_hp=45,
            max_hp=45,
            conditions=[],
            is_current_turn=False,
            is_active=True,
        ),
        EntityRowDTO(
            instance_id="e2",
            display_name="Goblin #1",
            entity_type="monster",
            initiative=15,
            current_hp=7,
            max_hp=7,
            conditions=["Poisoned"],
            is_current_turn=True,  # current turn
            is_active=True,
        ),
        EntityRowDTO(
            instance_id="e3",
            display_name="Orc #2",
            entity_type="monster",
            initiative=12,
            current_hp=0,
            max_hp=15,
            conditions=["Dead"],
            is_current_turn=False,
            is_active=False,  # inactive / dead
        ),
    ]

    state = EncounterStateDTO(
        encounter_id="test",
        round_number=3,
        entities=entities,
        undo_available=True,
    )

    def mock_advance_turn():
        state.round_number += 1
        return state

    service.get_state.return_value = state
    service.add_monster.return_value = state
    service.edit_hp.return_value = state
    service.advance_turn = mock_advance_turn

    return service
