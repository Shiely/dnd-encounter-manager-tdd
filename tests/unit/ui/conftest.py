# tests/unit/ui/conftest.py
# Fixtures for GUI tests

import pytest
from unittest.mock import Mock


@pytest.fixture
def stub_service():
    """Stub EncounterService for UI testing."""
    service = Mock()

    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

    # Initial state
    state = EncounterStateDTO(
        encounter_id="test",
        round_number=1,
        entities=[],
        undo_available=False,
    )

    def mock_advance_turn():
        state.round_number += 1
        return state

    service.get_state.return_value = state
    service.add_monster.return_value = state
    service.edit_hp.return_value = state
    service.advance_turn = mock_advance_turn

    return service
