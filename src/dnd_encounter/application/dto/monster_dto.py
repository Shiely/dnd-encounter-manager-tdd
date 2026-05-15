# application/dto/monster_dto.py
from dataclasses import dataclass

@dataclass
class MonsterSummaryDTO:
    monster_id: str
    name: str
    cr: str
    hp: int
    ac: int
    source: str
