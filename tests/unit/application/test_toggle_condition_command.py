# tests/unit/application/test_toggle_condition_command.py

from dnd_encounter.application.commands.toggle_condition_command import ToggleConditionCommand
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from dnd_encounter.domain.value_objects.condition import Condition


def test_execute_toggles_condition_on(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, conditions=[], monster_id="goblin")
    encounter.entities.append(entity)

    cmd = ToggleConditionCommand(encounter, "e1", Condition.FRIGHTENED, stub_publisher)
    cmd.execute()

    assert Condition.FRIGHTENED in entity.conditions


def test_execute_toggles_condition_off(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, conditions=[Condition.FRIGHTENED], monster_id="goblin")
    encounter.entities.append(entity)

    cmd = ToggleConditionCommand(encounter, "e1", Condition.FRIGHTENED, stub_publisher)
    cmd.execute()

    assert Condition.FRIGHTENED not in entity.conditions


def test_undo_restores_previous_state(stub_publisher):
    encounter = Encounter(encounter_id="test")
    entity = EncounterEntity("e1", "Goblin #1", "monster", 10, current_hp=10, max_hp=10, conditions=[], monster_id="goblin")
    encounter.entities.append(entity)

    cmd = ToggleConditionCommand(encounter, "e1", Condition.FRIGHTENED, stub_publisher)
    cmd.execute()
    cmd.undo()

    assert Condition.FRIGHTENED not in entity.conditions
