# DOMAIN LAYER: stdlib imports only.
import random
from ..entities.encounter_entity import EncounterEntity
from ..entities.monster_definition import MonsterDefinition


def sort_entities(
    entities: list[EncounterEntity],
    monster_defs: dict[str, MonsterDefinition],
    rng: random.Random | None = None,
) -> list[EncounterEntity]:
    """Return entities sorted high-to-low by initiative with five-step tie-breaking.

    Tie-breaking steps (applied in order when initiative values are equal):
        1. Higher dex_modifier wins (from MonsterDefinition; players use 0).
        2. Player entries rank above monster entries.
        3. Higher cr_decimal wins (monsters only).
        4. Players still tied: PRNG random order.
        5. Monsters still tied: PRNG random order.
    """
    _rng = rng or random.Random()

    def sort_key(entity: EncounterEntity) -> tuple:
        dex_mod = 0
        cr_decimal = 0.0
        if entity.entity_type == "monster" and entity.monster_id:
            defn = monster_defs.get(entity.monster_id)
            if defn:
                dex_mod = defn.ability_scores.dex_modifier
                cr_decimal = defn.challenge_rating.decimal
        is_player = 0 if entity.entity_type == "player" else 1  # players first on tie
        return (
            -entity.initiative,  # descending
            -dex_mod,  # step 1: higher dex wins
            is_player,  # step 2: players before monsters
            -cr_decimal,  # step 3: higher CR wins
            _rng.random(),  # steps 4+5: PRNG for remaining ties
        )

    return sorted(entities, key=sort_key)
