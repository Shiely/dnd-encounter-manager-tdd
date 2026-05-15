# ports/outbound/i_dice_roller.py
from typing import Protocol


class IDiceRoller(Protocol):
    def roll_d20(self) -> int: ...
