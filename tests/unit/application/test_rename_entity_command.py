# tests/unit/application/test_rename_entity_command.py

from dnd_encounter.application.commands.rename_entity_command import RenameEntityCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity


def test_execute_renames_entity(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = RenameEntityCommand(encounter, "e1", "Goblin #2", stub_publisher)
    cmd.execute()

    assert entity.display_name == "Goblin #2"


def test_undo_restores_old_name(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = RenameEntityCommand(encounter, "e1", "Goblin #2", stub_publisher)
    cmd.execute()
    cmd.undo()

    assert entity.display_name == "Goblin #1"
