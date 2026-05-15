# DOMAIN LAYER: stdlib imports only.
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class AbilityScores:
    str_: int
    dex: int
    con: int
    int_: int
    wis: int
    cha: int

    @property
    def dex_modifier(self) -> int:
        return math.floor((self.dex - 10) / 2)
