# tests/unit/application/test_encounter_service.py
# Clean tests using real implementations

import pytest
import tempfile
from pathlib import Path

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.adapters.outbound.json_encounter_repository import JsonEncounterRepository
from dnd_encounter.adapters.outbound.json_monster_repository import JsonMonsterRepository
from dnd_encounter.adapters.outbound.in_memory_undo_stack import InMemoryUndoStack
from dnd_encounter.adapters.outbound.dice_roller import DiceRoller
from dnd_encounter.adapters.outbound.event_publisher import EventPublisher


def test_add_monster():
    encounter = Encounter(encounter_id="test")
    from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
    from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
    from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

    goblin = MonsterDefinition(
        id="goblin",
        name="Goblin",
        size="Small",
        type_="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        speed={"walk": 30},
        ability_scores=AbilityScores(8, 14, 10, 10, 8, 8),
        challenge_rating=ChallengeRating("1/4"),
        xp=50,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        monster_repo = JsonMonsterRepository(path=Path(tmpdir) / "monsters.json")
        monster_repo.upsert(goblin)
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=monster_repo,
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        result = service.add_monster("goblin")
        assert len(result.entities) == 1
        assert result.entities[0].display_name.startswith("Goblin #")


def test_add_player():
    encounter = Encounter(encounter_id="test")
    with tempfile.TemporaryDirectory() as tmpdir:
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=None,  # type: ignore[arg-type]
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        service.add_player("Aragorn", 18, 45)
        assert len(encounter.entities) == 1
        assert encounter.entities[0].display_name == "Aragorn"


def test_add_player_multiple():
    encounter = Encounter(encounter_id="test")
    with tempfile.TemporaryDirectory() as tmpdir:
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=None,  # type: ignore[arg-type]
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        service.add_player("Aragorn", 18, 45)
        service.add_player("Legolas", 20, 40)

        assert len(encounter.entities) == 2
        # Sorted by initiative descending (highest first)
        assert encounter.entities[0].display_name == "Legolas"
        assert encounter.entities[1].display_name == "Aragorn"


def test_get_state_populates_current_turn_and_active():
    """Verify that get_state() correctly populates is_current_turn and is_active in EntityRowDTO."""
    encounter = Encounter(encounter_id="test")
    from dnd_encounter.domain.entities.encounter_entity import EncounterEntity

    e1 = EncounterEntity(
        instance_id="e1",
        display_name="Player1",
        entity_type="player",
        initiative=10,
        current_hp=20,
        max_hp=20,
        is_active=True,
    )
    e2 = EncounterEntity(
        instance_id="e2",
        display_name="Monster1",
        entity_type="monster",
        initiative=15,
        current_hp=10,
        max_hp=10,
        is_active=True,
    )
    e3 = EncounterEntity(
        instance_id="e3",
        display_name="DeadMonster",
        entity_type="monster",
        initiative=5,
        current_hp=0,
        max_hp=10,
        is_active=False,
    )
    encounter.entities = [e1, e2, e3]
    encounter.current_turn_index = 1  # points to e2 among active [e1, e2]

    with tempfile.TemporaryDirectory() as tmpdir:
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = DiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=None,  # type: ignore[arg-type]
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        state = service.get_state()

        # Only active entities should be returned (inactive ones are filtered for the UI)
        assert len(state.entities) == 2
        assert state.encounter_id == "test"
        assert state.round_number == 1
        assert state.undo_available is False

        # e0 (Player1): not current turn, active
        assert state.entities[0].is_current_turn is False
        assert state.entities[0].is_active is True

        # e1 (Monster1): current turn among active entities, active
        assert state.entities[1].is_current_turn is True
        assert state.entities[1].is_active is True

        # Note: e2 (DeadMonster) is inactive and correctly filtered out of the state sent to UI


# --- Phase 1 TDD red tests (added before touching non-test production code) ---

class VaryingDiceRoller:
    """Deterministic roller so batch test can prove independent rolls (different init + HP) without probability."""
    def __init__(self):
        self._d20 = 5
        self._hp_base = 7

    def roll_d20(self) -> int:
        v = self._d20
        self._d20 += 3  # produce distinct across calls
        return v

    def roll_expression(self, expression: str) -> int:
        v = self._hp_base
        self._hp_base += 2
        return v


def test_add_monster_count_n_produces_n_distinct_entities_with_independent_rolls():
    """Red test (pre-prod): add_monster(monster_id, count=N) must execute N independent AddEntityCommands.
    Each must roll its own initiative (d20 + dex) and HP (roll_expression or fallback), yielding distinct values
    and correct sequential display names. count=1 path remains unchanged (tested elsewhere).
    """
    encounter = Encounter(encounter_id="test")
    from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
    from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
    from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

    goblin = MonsterDefinition(
        id="goblin",
        name="Goblin",
        size="Small",
        type_="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        speed={"walk": 30},
        ability_scores=AbilityScores(8, 14, 10, 10, 8, 8),  # dex 14 -> +2 mod
        challenge_rating=ChallengeRating("1/4"),
        xp=50,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        monster_repo = JsonMonsterRepository(path=Path(tmpdir) / "monsters.json")
        monster_repo.upsert(goblin)
        encounter_repo = JsonEncounterRepository(path=Path(tmpdir) / "encounter.json")
        undo_stack = InMemoryUndoStack()
        dice_roller = VaryingDiceRoller()
        publisher = EventPublisher()

        service = EncounterService(
            encounter=encounter,
            monster_repo=monster_repo,
            encounter_repo=encounter_repo,
            undo_stack=undo_stack,
            dice_roller=dice_roller,
            publisher=publisher,
        )

        # This call will be red until service extended (signature + loop behavior)
        # Use positional for count to also cover
        result = service.add_monster("goblin", 3)

        # Must produce exactly 3
        assert len(result.entities) == 3
        names = [e.display_name for e in result.entities]
        # Names are assigned at creation time (#1 then #2 then #3); sort_by_initiative (highest init first) reorders the list
        # but does not change the display_name values. Use set or sorted for order-independent check.
        assert set(names) == {"Goblin #1", "Goblin #2", "Goblin #3"}
        assert sorted(names) == ["Goblin #1", "Goblin #2", "Goblin #3"]

        # Independent rolls => different initiative and current_hp (core requirement)
        inits = [e.initiative for e in result.entities]
        hps = [e.current_hp for e in result.entities]
        assert len(set(inits)) == 3, f"Expected 3 distinct initiatives from independent rolls, got {inits}"
        assert len(set(hps)) == 3, f"Expected 3 distinct HPs from independent rolls, got {hps}"

        # Also verify undo stack has 3 independent cmds (granular undo, same as pre-phase multi-single-add)
        assert undo_stack.depth() == 3  # or len of internal if exposed; using existing depth helper in stub

        # Pre-existing count=1 behavior must still work (call site compat)
        # (separate call re-uses same setup but we already mutated; simple re-assert shape covered by other test)
