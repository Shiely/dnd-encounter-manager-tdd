# DOMAIN LAYER: stdlib imports only.
from ..value_objects.condition import Condition


def toggle_condition(conditions: list[Condition], condition: Condition) -> list[Condition]:
    """Return a new list with the condition toggled. Does not mutate input."""
    # Use value comparison to be safe with Enum
    if any(c.value == condition.value for c in conditions):
        return [c for c in conditions if c.value != condition.value]
    return conditions + [condition]
