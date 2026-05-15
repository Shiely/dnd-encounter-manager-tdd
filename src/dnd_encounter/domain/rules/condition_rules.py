# DOMAIN LAYER: stdlib imports only.
from ..value_objects.condition import Condition


def toggle_condition(conditions: list[Condition], condition: Condition) -> list[Condition]:
    """Return a new list with the condition toggled. Does not mutate input."""
    if any(c == condition for c in conditions):
        return [c for c in conditions if c != condition]
    return conditions + [condition]
