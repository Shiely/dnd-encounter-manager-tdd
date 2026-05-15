# tests/unit/ui/conftest.py
# Fixtures for GUI tests

import pytest
from unittest.mock import Mock


@pytest.fixture
def stub_service():
    """Stub EncounterService for UI testing."""
    service = Mock()

    # Mock get_state() to return a basic EncounterStateDTO
    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

    state = EncounterStateDTO(
        encounter_id="test",
        round_number=1,
        entities=[
            EntityRowDTO(
                instance_id="e1",
                display_name="Goblin #1",
                entity_type="monster",
                initiative=12,
                current_hp=10,
                max_hp=10,
                conditions=[],
                is_current_turn=False,
                is_active=True,
            )
        ],
        undo_available=False,
    )

    service.get_state.return_value = state
    service.add_monster.return_value = state
    service.edit_hp.return_value = state

    return service
