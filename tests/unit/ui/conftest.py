# tests/unit/ui/conftest.py
# Fixtures for GUI tests

import pytest
from unittest.mock import Mock, patch

from dnd_encounter.domain.entities.encounter import Encounter


@pytest.fixture
def stub_service():
    """Stub EncounterService for UI testing with realistic state including is_current_turn and is_active."""
    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

    # Create a real Encounter with test entities
    encounter = Encounter(encounter_id="test")

    from dnd_encounter.domain.entities.encounter_entity import EncounterEntity

    e1 = EncounterEntity(
        instance_id="e1",
        display_name="Aragorn",
        entity_type="player",
        initiative=18,
        current_hp=45,
        max_hp=45,
        is_active=True,
    )
    e2 = EncounterEntity(
        instance_id="e2",
        display_name="Goblin #1",
        entity_type="monster",
        initiative=15,
        current_hp=7,
        max_hp=7,
        is_active=True,
    )
    e3 = EncounterEntity(
        instance_id="e3",
        display_name="Orc #2",
        entity_type="monster",
        initiative=12,
        current_hp=0,
        max_hp=15,
        is_active=False,
    )
    encounter.entities = [e1, e2, e3]

    # Create service mock
    service = Mock()
    service.encounter = encounter

    # Mock get_state() to return a DTO built from the live encounter
    def mock_get_state():
        entities = []
        for entity in encounter.entities:
            entities.append(
                EntityRowDTO(
                    instance_id=entity.instance_id,
                    display_name=entity.display_name,
                    entity_type=entity.entity_type,
                    initiative=entity.initiative,
                    current_hp=entity.current_hp,
                    max_hp=entity.max_hp,
                    conditions=[c.value for c in entity.conditions],
                    is_current_turn=False,
                    is_active=entity.is_active,
                )
            )
        return EncounterStateDTO(
            encounter_id=encounter.encounter_id,
            round_number=encounter.round_number,
            entities=entities,
            undo_available=False,
        )

    service.get_state = mock_get_state
    service.add_monster = Mock(return_value=encounter)
    service.edit_hp = Mock()
    service.advance_turn = Mock()
    service.remove_entity = Mock()
    service.rename_entity = Mock()
    service.change_initiative = Mock()

    return service


@pytest.fixture(autouse=True)
def mock_qinputdialog():
    """Automatically mock QInputDialog so GUI tests don't hang on modal dialogs."""
    with (
        patch("PySide6.QtWidgets.QInputDialog.getText", return_value=("New Name", True)),
        patch("PySide6.QtWidgets.QInputDialog.getInt", return_value=(15, True)),
    ):
        yield
