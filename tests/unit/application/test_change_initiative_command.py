# tests/unit/application/test_change_initiative_command.py

from dnd_encounter.application.commands.change_initiative_command import ChangeInitiativeCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity


def test_execute_changes_initiative(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = ChangeInitiativeCommand(encounter, "e1", 18, stub_publisher)
    cmd.execute()

    assert entity.initiative == 18


def test_undo_restores_old_initiative(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, monster_id="goblin")
    encounter.entities.append(entity)

    cmd = ChangeInitiativeCommand(encounter, "e1", 18, stub_publisher)
    cmd.execute()
    cmd.undo()

    assert entity.initiative == 10
