# tests/unit/application/test_remove_entity_command.py

from dnd_encounter.application.commands.remove_entity_command import RemoveEntityCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity


def test_execute_removes_entity(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, is_active=True, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = RemoveEntityCommand(encounter, "e1", stub_publisher)
    cmd.execute()

    assert entity.is_active is False


def test_undo_restores_entity(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, is_active=True, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = RemoveEntityCommand(encounter, "e1", stub_publisher)
    cmd.execute()
    cmd.undo()

    assert entity.is_active is True
