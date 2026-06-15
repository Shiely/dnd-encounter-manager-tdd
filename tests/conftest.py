# tests/conftest.py
import collections
import pytest
from unittest.mock import Mock

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

    def roll_expression(self, expression: str) -> int:
        # For tests, return a predictable value based on the fixed_value
        return self._value * 2 + 5   # e.g. 25 if fixed_value=10


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
    return StubEventPublisher()


@pytest.fixture
def stub_service():
    """Stub service for UI testing."""
    service = Mock()
    service.get_state = Mock(return_value=Mock(entities=[], round_number=1))
    service.add_monster = Mock()
    service.add_player = Mock()
    service.edit_hp = Mock()
    service.remove_entity = Mock()
    service.advance_turn = Mock()
    service.reset = Mock()
    return service
