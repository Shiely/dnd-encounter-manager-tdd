# adapters/outbound/json_encounter_repository.py
import json
from pathlib import Path
from platformdirs import user_data_dir
from src.dnd_encounter.domain.entities.encounter import Encounter
from src.dnd_encounter.ports.outbound.i_encounter_repository import IEncounterRepository

APP_NAME = "DndEncounterManager"
APP_AUTHOR = "dnd-encounter-manager"

ENCOUNTER_SAVE_PATH = Path(user_data_dir(APP_NAME, APP_AUTHOR)) / "encounter_save.json"

class JsonEncounterRepository(IEncounterRepository):
    def __init__(self, path: Path | None = None):
        self.path = path or ENCOUNTER_SAVE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Encounter | None:
        if not self.path.exists():
            return None
        with open(self.path) as f:
            data = json.load(f)
        # Simplified - in real version we'd use proper deserialization
        return Encounter(**data)  # type: ignore

    def save(self, encounter: Encounter) -> None:
        with open(self.path, "w") as f:
            json.dump(encounter.__dict__, f, indent=2, default=str)
