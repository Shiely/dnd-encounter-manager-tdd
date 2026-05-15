# tests/unit/domain/test_condition_rules.py
# DOMAIN LAYER TEST - No external imports allowed

from dnd_encounter.domain.rules.condition_rules import toggle_condition
from dnd_encounter.domain.value_objects.condition import Condition


def test_toggle_adds_when_not_present():
    conditions = []
    result = toggle_condition(conditions, Condition.FRIGHTENED)
    assert Condition.FRIGHTENED in result
    assert len(result) == 1


def test_toggle_removes_when_present():
    conditions = [Condition.FRIGHTENED, Condition.POISONED]
    result = toggle_condition(conditions, Condition.FRIGHTENED)
    assert Condition.FRIGHTENED not in result
    assert len(result) == 1


def test_toggle_is_idempotent():
    conditions = []
    result = toggle_condition(conditions, Condition.FRIGHTENED)
    result = toggle_condition(result, Condition.FRIGHTENED)  # add twice
    result = toggle_condition(result, Condition.FRIGHTENED)  # remove
    assert len(result) == 0


def test_toggle_does_not_mutate_input():
    original = [Condition.POISONED]
    toggle_condition(original, Condition.FRIGHTENED)
    assert original == [Condition.POISONED]  # input unchanged
