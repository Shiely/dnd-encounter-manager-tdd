# adapters/outbound/dice_roller.py
import random
import re

from dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller


class DiceRoller(IDiceRoller):
    def roll_d20(self) -> int:
        return random.randint(1, 20)

    def roll_expression(self, expression: str) -> int:
        """
        Roll a dice expression such as:
            "16d8+32"
            "2d6-1"
            "1d8"
            "8"
        Returns the total.
        """
        if not expression or not isinstance(expression, str):
            return 0

        expression = expression.strip().lower().replace(" ", "")

        # Handle plain number
        if expression.isdigit() or (expression.startswith("-") and expression[1:].isdigit()):
            return int(expression)

        total = 0
        # Match patterns like 2d6, +3, -4, etc.
        # We split into dice rolls and modifiers
        parts = re.findall(r'([+-]?\d+d\d+|[+-]?\d+)', expression)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            sign = 1
            if part.startswith("+"):
                part = part[1:]
            elif part.startswith("-"):
                sign = -1
                part = part[1:]

            if "d" in part:
                # Dice roll: e.g. "16d8"
                num, sides = part.split("d", 1)
                num = int(num) if num else 1
                sides = int(sides)
                roll = sum(random.randint(1, sides) for _ in range(num))
                total += sign * roll
            else:
                # Modifier
                total += sign * int(part)

        return total
