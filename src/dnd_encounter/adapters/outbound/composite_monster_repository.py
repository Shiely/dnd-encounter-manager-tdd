# adapters/outbound/composite_monster_repository.py
"""
Composite repository that layers multiple IMonsterRepository sources.
Typical usage:
    srd = SrdMonsterRepository()
    user = JsonMonsterRepository()
    repo = CompositeMonsterRepository([srd, user])   # srd is base, user overrides
"""

from __future__ import annotations
from typing import Sequence

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository


class CompositeMonsterRepository(IMonsterRepository):
    """
    Combines multiple repositories.
    Earlier repositories in the list have lower priority.
    Later ones override earlier ones on conflicts (by monster id).
    upsert() always goes to the last repository in the list (assumed to be the writable one).
    """

    def __init__(self, repositories: Sequence[IMonsterRepository]):
        if not repositories:
            raise ValueError("CompositeMonsterRepository requires at least one repository")
        self.repositories: list[IMonsterRepository] = list(repositories)

    def get(self, monster_id: str) -> MonsterDefinition | None:
        # Check from last to first so user overrides win
        for repo in reversed(self.repositories):
            monster = repo.get(monster_id)
            if monster is not None:
                return monster
        return None

    def list_all(self) -> list[MonsterDefinition]:
        # Later repositories override earlier ones (user repo wins over SRD on id conflict)
        by_id: dict[str, MonsterDefinition] = {}

        for repo in self.repositories:
            for m in repo.list_all():
                by_id[m.id] = m   # later entries overwrite earlier ones

        # Return sorted by name for nice dialogs
        return sorted(by_id.values(), key=lambda m: getattr(m, 'name', ''))

    def upsert(self, monster: MonsterDefinition) -> None:
        # Always write to the highest-priority (last) repo, assumed writable
        self.repositories[-1].upsert(monster)

    def count(self) -> int:
        # Efficient count without materializing the full list
        seen: set[str] = set()
        for repo in self.repositories:
            for m in repo.list_all():
                seen.add(m.id)
        return len(seen)