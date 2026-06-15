# application/services/encounter_service.py
# Orchestrates domain logic and coordinates commands

from __future__ import annotations

from dnd_encounter.domain.entities.encounter import Encounter
from dnd_encounter.domain.entities.encounter_entity import EncounterEntity
from dnd_encounter.ports.outbound.i_encounter_repository import IEncounterRepository
from dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository
from dnd_encounter.ports.outbound.i_undo_stack import IUndoStack
from dnd_encounter.ports.outbound.i_dice_roller import IDiceRoller
from dnd_encounter.ports.outbound.i_event_publisher import IEventPublisher

from dnd_encounter.application.commands.add_entity_command import AddEntityCommand
from dnd_encounter.application.commands.edit_hp_command import EditHpCommand
from dnd_encounter.application.commands.remove_entity_command import RemoveEntityCommand
from dnd_encounter.application.commands.toggle_condition_command import ToggleConditionCommand
from dnd_encounter.application.commands.change_initiative_command import ChangeInitiativeCommand
from dnd_encounter.application.commands.rename_entity_command import RenameEntityCommand


class EncounterService:
    def __init__(
        self,
        encounter: Encounter,
        monster_repo: IMonsterRepository,
        encounter_repo: IEncounterRepository,
        undo_stack: IUndoStack,
        dice_roller: IDiceRoller,
        publisher: IEventPublisher,
    ):
        self.encounter = encounter
        self.monster_repo = monster_repo
        self.encounter_repo = encounter_repo
        self.undo_stack = undo_stack
        self.dice_roller = dice_roller
        self.publisher = publisher

    def get_state(self):
        from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO

        current = self.encounter.current_entity()
        entities = []
        for entity in self.encounter.entities:
            if not entity.is_active:
                continue  # Removed entities are hidden from the UI (soft-delete for undo support)
            # Phase 4: populate core stats additively for monsters (from bestiary via repo already on service).
            # Non-monsters and missing defs get None (backward safe). This makes ac/speed/cr available
            # on the DTO for StatBlockPanel (and any other consumer) without changing call sites.
            # Phase 5: xp added in same seam (additive).
            ac = None
            speed = None
            cr = None
            xp = None
            mid = getattr(entity, "monster_id", None)
            if mid and self.monster_repo:
                try:
                    mdef = self.monster_repo.get(mid)
                    if mdef:
                        ac = getattr(mdef, "armor_class", None)
                        spd = getattr(mdef, "speed", None) or {}
                        # Format speed lightly for DTO (matches panel expectation; renderer has full too)
                        if isinstance(spd, dict):
                            walk = spd.get("walk")
                            speed = f"{walk} ft." if walk else str(spd)
                        else:
                            speed = str(spd) if spd else None
                        cr_obj = getattr(mdef, "challenge_rating", None)
                        cr = getattr(cr_obj, "value", None) if cr_obj else None
                        xp = getattr(mdef, "xp", None)
                except Exception:
                    pass  # never break get_state on data issues

            entities.append(
                EntityRowDTO(
                    instance_id=entity.instance_id,
                    display_name=entity.display_name,
                    entity_type=entity.entity_type,
                    initiative=entity.initiative,
                    current_hp=entity.current_hp,
                    max_hp=entity.max_hp,
                    conditions=[c.value for c in entity.conditions],
                    is_current_turn=(entity is current),
                    is_active=entity.is_active,
                    monster_id=mid,
                    ac=ac,
                    speed=speed,
                    cr=cr,
                    xp=xp,
                )
            )

        return EncounterStateDTO(
            encounter_id=self.encounter.encounter_id,
            round_number=self.encounter.round_number,
            entities=entities,
            undo_available=not self.undo_stack.is_empty(),
        )

    def add_monster(self, monster_id: str, count: int = 1):
        """Add one or more of the same monster. count > 1 performs count independent AddEntityCommand
        executions so each gets its own initiative (d20 + dex) and HP (roll_expression or static) rolls.
        Backward compatible: count=1 (default) produces identical observable behavior to pre-Phase-1
        (same # of entities, same undo stack depth per add, same display names for singles, same DTOs).
        """
        for _ in range(max(1, int(count))):
            cmd = AddEntityCommand(
                encounter=self.encounter,
                monster_repo=self.monster_repo,
                monster_id=monster_id,
                dice_roller=self.dice_roller,
                publisher=self.publisher,
            )
            cmd.execute()
            self.undo_stack.push(cmd)
        self.encounter.sort_by_initiative()  # <-- ensure correct order (after all batch appends)
        self.encounter_repo.save(self.encounter)
        return self.encounter

    def add_player(self, name: str, initiative: int, max_hp: int):
        """Add a player character to the encounter."""
        from dnd_encounter.domain.entities.encounter_entity import EncounterEntity

        player = EncounterEntity(
            instance_id=f"player_{name.lower().replace(' ', '_')}",
            display_name=name,
            entity_type="player",
            initiative=initiative,
            current_hp=max_hp,
            max_hp=max_hp,
            monster_id=None,
        )
        self.encounter.entities.append(player)
        self.encounter.sort_by_initiative()  # <-- ensure correct order
        self.encounter_repo.save(self.encounter)

    def edit_hp(self, instance_id: str, new_hp: int):
        cmd = EditHpCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_hp=new_hp,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def remove_entity(self, instance_id: str):
        cmd = RemoveEntityCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def toggle_condition(self, instance_id: str, condition):
        # Convert string from UI to proper Condition enum
        if isinstance(condition, str):
            from dnd_encounter.domain.value_objects.condition import Condition
            condition = next((c for c in Condition if c.value == condition), None)
            if condition is None:
                print(f"[Service] Unknown condition string: {condition}")
                return

        cmd = ToggleConditionCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            condition=condition,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def change_initiative(self, instance_id: str, new_initiative: int):
        cmd = ChangeInitiativeCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_initiative=new_initiative,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def rename_entity(self, instance_id: str, new_name: str):
        cmd = RenameEntityCommand(
            encounter=self.encounter,
            instance_id=instance_id,
            new_name=new_name,
            publisher=self.publisher,
        )
        cmd.execute()
        self.undo_stack.push(cmd)
        self.encounter_repo.save(self.encounter)

    def advance_turn(self):
        if self.encounter.entities:
            self.encounter.current_turn_index = (self.encounter.current_turn_index + 1) % len(self.encounter.entities)
            if self.encounter.current_turn_index == 0:
                self.encounter.round_number += 1
            self.encounter_repo.save(self.encounter)

    def undo(self) -> bool:
        """Undo the last command if possible. Returns True if something was undone."""
        if self.undo_stack.is_empty():
            return False

        cmd = self.undo_stack.pop()
        if cmd:
            cmd.undo()
            self.encounter_repo.save(self.encounter)
            return True
        return False

    def can_undo(self) -> bool:
        return not self.undo_stack.is_empty()

    def reset(self) -> None:
        """Reset / clear the encounter for a fresh start (new top TODO item (2)).

        Atomically:
        - Clears encounter.entities = []
        - Resets current_turn_index = 0 and round_number = 1
        - Drains the undo stack (no stale undos from prior encounter; does not call undo())
        - Persists via encounter_repo
        - Subsequent get_state() yields clean EncounterStateDTO (empty entities, round=1, undo_available=false, no error)

        Additive only: no change to any pre-existing method signatures, returns, or observable behavior
        for add/advance/undo/HP/conditions paths. Reset itself is decisive (not undoable).
        """
        self.encounter.entities = []
        self.encounter.current_turn_index = 0
        self.encounter.round_number = 1

        # Drain undo stack without invoking command undo() (we want clean slate, not reversal)
        while not self.undo_stack.is_empty():
            self.undo_stack.pop()

        self.encounter_repo.save(self.encounter)
        # get_state() will now reflect the clean state on next call (no explicit publish needed)
