# ports/outbound/i_dice_roller.py
from typing import Protocol


class IDiceRoller(Protocol):
    def roll_d20(self) -> int: ...

    def roll_expression(self, expression: str) -> int:
        """Roll a dice expression like '16d8+32' or '2d6+3'."""
        ...
