# adapters/outbound/json_monster_repository.py
from __future__ import annotations
import json
from pathlib import Path
from platformdirs import user_data_dir
from src.dnd_encounter.domain.entities.monster_definition import MonsterDefinition

from src.dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository

APP_NAME = "DndEncounterManager"
APP_AUTHOR = "dnd-encounter-manager"

MONSTERS_DB_PATH = Path(user_data_dir(APP_NAME, APP_AUTHOR)) / "monsters_db.json"


class JsonMonsterRepository(IMonsterRepository):
    def __init__(self, path: Path | None = None):
        self.path = path or MONSTERS_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return json.load(f)

    def _write(self, data: list[dict]) -> None:
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, monster_id: str) -> MonsterDefinition | None:
        for item in self._load():
            if item["id"] == monster_id:
                # Simplified deserialization
                return MonsterDefinition(**item)  # type: ignore
        return None

    def list_all(self) -> list[MonsterDefinition]:
        return [MonsterDefinition(**item) for item in self._load()]  # type: ignore

    def upsert(self, monster: MonsterDefinition) -> None:
        data = self._load()
        for i, item in enumerate(data):
            if item["id"] == monster.id:
                data[i] = monster.__dict__
                self._write(data)
                return
        data.append(monster.__dict__)
        self._write(data)

    def count(self) -> int:
        return len(self._load())
