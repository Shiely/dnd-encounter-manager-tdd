"""
TDD tests for the new MonsterStatBlockRenderer.

These tests drive the design and extraction of the rendering logic
out of StatBlockPanel. They focus on:

- Clean public interface: render(monster: MonsterDefinition) -> str
- Information preservation (core requirement)
- No leakage of 5eTools tags or mangled attack text
- Classic 5e formatting for actions, spellcasting, reactions, etc.

All tests must pass before and after refactoring.
"""

import pytest

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating

# This import will drive the creation of the new class
from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import (
    MonsterStatBlockRenderer,
)


def test_monster_stat_block_renderer_has_render_method():
    """Basic interface test (TDD - this should fail until the class exists)."""
    renderer = MonsterStatBlockRenderer()
    assert hasattr(renderer, "render")
    assert callable(getattr(renderer, "render"))


def test_monster_stat_block_renderer_renders_basic_monster():
    """The renderer must produce some output for a minimal monster."""
    monster = MonsterDefinition(
        id="goblin-test",
        name="Goblin",
        size="Small",
        type_="humanoid",
        alignment="neutral evil",
        armor_class=15,
        hit_points=7,
        hit_dice="2d6",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=8, dex=14, con=10, int_=10, wis=8, cha=8),
        challenge_rating=ChallengeRating("1/4"),
        xp=50,
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert isinstance(html, str)
    assert len(html) > 50
    # The renderer focuses on stats/abilities/actions, not the monster name
    # (the name is shown in the panel title bar separately).
    assert "CR" in html or "1/4" in html
    assert "STR" in html and "DEX" in html  # ability scores are rendered


def test_monster_stat_block_renderer_renders_actions_in_classic_5e_style():
    """Actions should use 'Name. Description.' format."""
    monster = MonsterDefinition(
        id="test-monster",
        name="Test Monster",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=12,
        hit_points=20,
        hit_dice="3d8+6",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=12, con=14, int_=10, wis=10, cha=10),
        challenge_rating=ChallengeRating("1"),
        xp=200,
        actions=[
            {"name": "Multiattack", "description": "The monster makes two attacks."},
            {
                "name": "Scimitar",
                "description": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
            },
        ],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert "<b>Multiattack.</b> The monster makes two attacks." in html
    assert "<b>Scimitar.</b> Melee Weapon Attack: +4 to hit" in html


def test_monster_stat_block_renderer_no_raw_5etools_tags():
    """The renderer must never leak raw 5eTools tags into the output."""
    monster = MonsterDefinition(
        id="tag-test",
        name="Tag Test",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=12,
        hit_points=30,
        hit_dice="4d8+8",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=12, con=14, int_=10, wis=10, cha=10),
        challenge_rating=ChallengeRating("2"),
        xp=450,
        actions=[
            {
                "name": "Bad Attack",
                "description": "{@atk ms,rs} +5 to hit. 10 (2d6 + 3) damage.",
            }
        ],
        reactions=[
            {"name": "Ward {@recharge 4}", "description": "Something happens."}
        ],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert "{@" not in html
    assert "ms,rs" not in html
    assert "{@recharge" not in html


def test_monster_stat_block_renderer_produces_nice_spellcasting_labels():
    """Spellcasting should use friendly 5e labels like 'At will' and '1/day each'."""
    monster = MonsterDefinition(
        id="caster-test",
        name="Caster Test",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=12,
        hit_points=40,
        hit_dice="5d8+10",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=8, dex=12, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("3"),
        xp=700,
        spellcasting=[
            {
                "header": "The caster casts spells...",
                "spells": {
                    "at_will": ["light", "mage hand"],
                    "daily_2": ["fireball"],
                    "daily_1": ["banishment"],
                },
            }
        ],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert "At will:" in html or "At will" in html
    assert "1/day each:" in html or "1/day each" in html
    assert "2/day each:" in html or "2/day each" in html


def test_monster_stat_block_renderer_shows_rolled_hp_and_formula():
    """
    When an instance has rolled HP (from hit dice), the renderer should display
    the actual rolled current/max HP **and** the original dice formula it was
    rolled from.

    This is critical for transparency (player/DM can see both the current
    rolled value and what formula produced it).
    """
    monster_def = MonsterDefinition(
        id="abjurer-rolled-hp-test",
        name="Abjurer",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=104,           # average from definition
        hit_dice="16d8+32",       # the formula that was rolled
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
    )

    renderer = MonsterStatBlockRenderer()

    # Simulate a monster that rolled poorly (87 instead of the average 104)
    html = renderer.render(monster_def, current_hp=87, max_hp=87)

    # Must show the rolled value
    assert "HP</b> 87" in html or "HP 87" in html

    # Must also show what it was rolled from (the formula)
    assert "16d8+32" in html
    assert "rolled from" in html.lower()

    # When current != max (damaged monster), both should be visible
    html_damaged = renderer.render(monster_def, current_hp=62, max_hp=87)
    assert "62 / 87" in html_damaged or "HP</b> 62" in html_damaged
    assert "16d8+32" in html_damaged
    assert "rolled from" in html_damaged.lower()


def test_monster_stat_block_renderer_renders_size_type_and_alignment():
    """Size (and the full creature type line) must be rendered in the stat block."""
    monster = MonsterDefinition(
        id="size-test",
        name="Ancient Red Dragon",
        size="Gargantuan",
        type_="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        speed={"walk": 40, "fly": 80},
        ability_scores=AbilityScores(str_=30, dex=10, con=29, int_=18, wis=15, cha=23),
        challenge_rating=ChallengeRating("24"),
        xp=62000,
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    # Should contain the full type line
    assert "Gargantuan" in html
    assert "dragon" in html.lower()
    assert "chaotic evil" in html.lower() or "Chaotic Evil" in html

    # A common combined form should be present (our current format uses commas)
    assert "gargantuan, dragon" in html.lower()


# =============================================================================
# REGRESSION TESTS FOR DEFENSIVE RENDERING
# =============================================================================

def test_monster_stat_block_renderer_gracefully_handles_bad_defense_data():
    """
    Regression test: The renderer must not crash when defense lists contain
    non-string items (e.g. dicts from incompletely normalized 5eTools MPMM data).

    This was the exact failure mode reported with the Abjurer Wizard.
    """
    monster = MonsterDefinition(
        id="dirty-defense-test",
        name="Dirty Defense Monster",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=15,
        hit_points=60,
        hit_dice="8d8+16",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=10, wis=12, cha=10),
        challenge_rating=ChallengeRating("3"),
        xp=700,
        # Simulate bad data: a list containing a dict (realistic from some MPMM entries)
        damage_resistances=["fire", {"resist": "cold", "note": "from spells"}],
        damage_immunities=["poison"],
        condition_immunities=[{"immune": "charmed"}],
        actions=[
            {"name": "Attack", "description": "Simple attack."}
        ],
    )

    renderer = MonsterStatBlockRenderer()

    # Must not raise
    html = renderer.render(monster)

    # The renderer must still produce valid output with other sections intact
    # (even if the bad defense data is stringified or partially included)
    assert isinstance(html, str)
    assert len(html) > 100
    assert "CR 3" in html
    assert "Actions" in html
    assert "Attack." in html

    # Most importantly: it must not have crashed
    # (this was the regression: dict in defense list would previously raise)


def test_monster_stat_block_renderer_gracefully_handles_bad_spell_list_data():
    """
    Regression test: Spell lists containing non-string items must not crash rendering.
    """
    monster = MonsterDefinition(
        id="dirty-spells-test",
        name="Dirty Spells Monster",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=12,
        hit_points=40,
        hit_dice="5d8+10",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=8, dex=12, con=14, int_=16, wis=10, cha=8),
        challenge_rating=ChallengeRating("2"),
        xp=450,
        spellcasting=[
            {
                "header": "Casts spells.",
                "spells": {
                    "at_will": ["mage hand", {"spell": "light"}],  # bad item
                    "daily_1": ["fireball"],
                }
            }
        ],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert isinstance(html, str)
    assert "Spellcasting" in html
    assert "Actions" not in html or "Spellcasting" in html  # basic sanity
    # The render must succeed even with dirty spell data


def test_monster_stat_block_renderer_defensive_rendering_skips_bad_sections_but_keeps_good_ones():
    """
    When one section has bad data, the renderer should skip only that section
    (via _safe_append) while still rendering all other good sections.
    """
    monster = MonsterDefinition(
        id="multi-bad-section-test",
        name="Multi Bad Section Monster",
        size="Small",
        type_="fey",
        alignment="chaotic good",
        armor_class=13,
        hit_points=30,
        hit_dice="4d6+8",
        speed={"walk": 25},
        ability_scores=AbilityScores(str_=8, dex=16, con=12, int_=10, wis=14, cha=18),
        challenge_rating=ChallengeRating("1"),
        xp=200,
        # Bad defenses
        damage_resistances=[{"resist": "fire"}],
        # Good actions
        actions=[{"name": "Charm", "description": "The fey charms a creature."}],
        # Bad legendary
        legendary_actions=[{"name": "Bad Leg", "description": {"bad": "data"}}],
        # Good reactions
        reactions=[{"name": "Evasion", "description": "The fey dodges."}],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert isinstance(html, str)
    assert len(html) > 50

    # Good sections must still be present
    assert "CR 1" in html
    assert "small, fey" in html.lower()
    assert "AC" in html and "13" in html
    assert "Actions" in html
    assert "Charm." in html
    assert "Reactions" in html
    assert "Evasion." in html

    # The bad sections may or may not produce output, but the renderer didn't crash
    # and good content is there.


def test_monster_stat_block_renderer_handles_minimal_monster_definition():
    """Renderer should handle a MonsterDefinition with almost no optional fields."""
    monster = MonsterDefinition(
        id="minimal",
        name="Minimal Monster",
        size="Tiny",
        type_="beast",
        alignment="unaligned",
        armor_class=10,
        hit_points=5,
        hit_dice="1d4+1",
        speed={"walk": 20},
        ability_scores=AbilityScores(str_=6, dex=14, con=10, int_=2, wis=12, cha=6),
        challenge_rating=ChallengeRating("0"),
        xp=10,
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert isinstance(html, str)
    assert "CR 0" in html
    assert "tiny, beast" in html.lower()
    assert "AC" in html and "10" in html
    assert "HP" in html and "5" in html
    assert "Speed" in html


def test_monster_stat_block_renderer_gracefully_handles_bad_traits_and_bonus_actions():
    """Additional coverage: bad data in traits and bonus_actions must be skipped without crashing the whole block."""
    monster = MonsterDefinition(
        id="bad-traits-bonus",
        name="Messy Monster",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=14,
        hit_points=45,
        hit_dice="6d8+12",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=12, dex=14, con=14, int_=10, wis=12, cha=10),
        challenge_rating=ChallengeRating("2"),
        xp=450,
        traits=[{"name": "Bad Trait", "description": {"nested": True}}],
        bonus_actions=[{"name": "Bad Bonus", "description": 12345}],  # non-string description
        actions=[{"name": "Good Attack", "description": "Hits hard."}],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert isinstance(html, str)
    assert "CR 2" in html
    assert "Actions" in html
    assert "Good Attack." in html
    # Bad sections are allowed to be missing or partially stringified; main point is no crash


def test_monster_stat_block_renderer_renders_skills_and_senses_when_present():
    """Covers the skills and senses+language rendering branches."""
    monster = MonsterDefinition(
        id="skilled-senses",
        name="Skilled Monster",
        size="Large",
        type_="monstrosity",
        alignment="neutral",
        armor_class=15,
        hit_points=90,
        hit_dice="12d10+24",
        speed={"walk": 40, "swim": 30},
        ability_scores=AbilityScores(str_=18, dex=12, con=16, int_=6, wis=12, cha=8),
        challenge_rating=ChallengeRating("5"),
        xp=1800,
        skills={"perception": 5, "stealth": 3},
        senses={"darkvision": 60, "passive_perception": 15},
        languages=["Common", "Deep Speech"],
    )

    renderer = MonsterStatBlockRenderer()
    html = renderer.render(monster)

    assert "Skills" in html
    assert "Perception" in html or "PERCEPTION" in html
    assert "Senses:" in html
    assert "darkvision" in html.lower()
    assert "Languages" in html
    assert "Deep Speech" in html
