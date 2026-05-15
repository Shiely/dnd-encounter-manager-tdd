# DOMAIN LAYER: stdlib imports only.
import re
from dataclasses import dataclass

_PATTERN = re.compile(r"^\d+d\d+([+-]\d+)?$|^\d+$")


@dataclass(frozen=True)
class DiceExpression:
    value: str

    def __post_init__(self) -> None:
        if not _PATTERN.match(self.value):
            raise ValueError(f"Invalid dice expression: {self.value!r}")
