# tests/integration/test_json_encounter_repository.py
import tempfile
from pathlib import Path

from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository
from dnd_encounter.domain.entities.encounter import Encounter


def test_save_and_load(tmp_path):
    repo = JsonEncounterRepository(path=tmp_path / "encounter.json")

    encounter = Encounter(encounter_id="test-123")
    repo.save(encounter)

    loaded = repo.load()
    assert loaded is not None
    assert loaded.encounter_id == "test-123"


def test_load_missing_file(tmp_path):
    repo = JsonEncounterRepository(path=tmp_path / "nonexistent.json")
    assert repo.load() is None
