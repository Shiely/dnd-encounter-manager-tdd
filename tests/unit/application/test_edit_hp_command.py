# tests/unit/application/test_edit_hp_command.py
# Uses stubs from conftest

import pytest
from src.dnd_encounter.application.commands.edit_hp_command import EditHpCommand
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.domain.entities.encounter_entity import EncounterEntity


def test_execute_sets_hp(stub_encounter_repo, stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = EditHpCommand(encounter, "e1", 7, stub_publisher)
    cmd.execute()

    assert entity.current_hp == 7


def test_execute_hp_zero_auto_removes(stub_encounter_repo, stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = EditHpCommand(encounter, "e1", 0, stub_publisher)
    cmd.execute()

    assert entity.current_hp == 0
    assert entity.is_active is False
    assert any(e[0] == "entity_auto_removed" for e in stub_publisher.events)


def test_execute_publishes_hp_changed(stub_encounter_repo, stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = EditHpCommand(encounter, "e1", 5, stub_publisher)
    cmd.execute()

    assert any(e[0] == "hp_changed" for e in stub_publisher.events)


def test_undo_restores_hp(stub_encounter_repo, stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = EditHpCommand(encounter, "e1", 3, stub_publisher)
    cmd.execute()
    cmd.undo()

    assert entity.current_hp == 10


def test_undo_restores_active_after_auto_remove(stub_encounter_repo, stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = EditHpCommand(encounter, "e1", 0, stub_publisher)
    cmd.execute()
    cmd.undo()

    assert entity.current_hp == 10
    assert entity.is_active is True
