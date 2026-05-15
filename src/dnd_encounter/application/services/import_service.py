# application/services/import_service.py
from __future__ import annotations
from dataclasses import dataclass
from src.dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository

@dataclass
class ImportService:
    monster_repo: IMonsterRepository
    schema_path: str

    def import_monsters(self, json_path: str) -> dict[str, int]:
        import json
        from jsonschema import validate, ValidationError

        with open(json_path) as f:
            data = json.load(f)

        with open(self.schema_path) as f:
            schema = json.load(f)

        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Invalid import file: {e.message}")

        added = 0
        updated = 0

        for monster_data in data.get("monsters", []):
            # Simplified - in real version we'd use pydantic
            monster = type('obj', (object,), monster_data)()  # placeholder
            # Proper deserialization would happen here
            self.monster_repo.upsert(monster)  # type: ignore
            added += 1

        return {"added": added, "updated": updated}
