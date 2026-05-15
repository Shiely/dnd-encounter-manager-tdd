# adapters/outbound/dice_roller.py
# Dice rolling adapter

import random


class DiceRoller:
    """Adapter for rolling dice in D&D encounters."""

    def roll_d20(self) -> int:
        """Roll a d20."""
        return random.randint(1, 20)

    def roll(self, num_dice: int, dice_sides: int, modifier: int = 0) -> int:
        """Roll dice and return the result."""
        rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
        return sum(rolls) + modifier

    def roll_multiple(self, num_dice: int, dice_sides: int, times: int) -> list[int]:
        """Roll multiple sets of dice."""
        return [self.roll(num_dice, dice_sides) for _ in range(times)]
