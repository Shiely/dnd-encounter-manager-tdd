# tests/conftest.py
import collections
import pytest
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.application.commands.base_command import BaseCommand


class StubMonsterRepository:
    def __init__(self) -> None:
        self._store: dict[str, MonsterDefinition] = {}

    def get(self, monster_id: str) -> MonsterDefinition | None:
        return self._store.get(monster_id)

    def list_all(self) -> list[MonsterDefinition]:
        return list(self._store.values())

    def upsert(self, monster: MonsterDefinition) -> None:
        self._store[monster.id] = monster

    def count(self) -> int:
        return len(self._store)


class StubEncounterRepository:
    def __init__(self) -> None:
        self._saved: Encounter | None = None

    def load(self) -> Encounter | None:
        return self._saved

    def save(self, encounter: Encounter) -> None:
        self._saved = encounter


class StubUndoStack:
    def __init__(self) -> None:
        self._stack: collections.deque[BaseCommand] = collections.deque(maxlen=5)

    def push(self, command: BaseCommand) -> None:
        self._stack.append(command)

    def pop(self) -> BaseCommand | None:
        return self._stack.pop() if self._stack else None

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def depth(self) -> int:
        return len(self._stack)


class StubDiceRoller:
    def __init__(self, fixed_value: int = 10) -> None:
        self._value = fixed_value

    def roll_d20(self) -> int:
        return self._value


class StubEventPublisher:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def publish(self, event_type: str, payload: dict) -> None:
        self.events.append((event_type, payload))


@pytest.fixture
def stub_monster_repo() -> StubMonsterRepository:
    return StubMonsterRepository()


@pytest.fixture
def stub_encounter_repo() -> StubEncounterRepository:
    return StubEncounterRepository()


@pytest.fixture
def stub_undo_stack() -> StubUndoStack:
    return StubUndoStack()


@pytest.fixture
def stub_dice_roller() -> StubDiceRoller:
    return StubDiceRoller()


@pytest.fixture
def stub_publisher() -> StubEventPublisher:
