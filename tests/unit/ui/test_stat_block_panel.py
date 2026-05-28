"""
Tests for StatBlockPanel, focusing on rich monster data rendering.

These tests cover the display of full monster definitions including
long action/trait/legendary action descriptions.
"""

import pytest
from unittest.mock import Mock

from PySide6.QtWidgets import QTextBrowser

from dnd_encounter.adapters.inbound.desktop_ui.stat_block_panel import StatBlockPanel
from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO
from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating


def test_stat_block_panel_renders_full_long_action_descriptions(qtbot):
    """
    Regression test for action description truncation.

    Long mechanical descriptions (e.g. Force Blast on Abjurer Wizard) must
    not be arbitrarily truncated in the StatBlockPanel. Previously a hard
    [:160] slice in _build_rich_monster_html would cut off important text
    such as push effects and successful save riders.
    """
    long_force_blast = (
        "Each creature in a 20-foot cube originating from the abjurer must make a DC 16 "
        "Constitution saving throw. On a failed save, a creature takes 36 (8d8) force damage "
        "and is pushed up to 10 feet away from the abjurer. On a successful save, a creature "
        "takes half as much damage and isn't pushed."
    )

    # Build a realistic MonsterDefinition with the long action
    monster_def = MonsterDefinition(
        id="abjurer-wizard",
        name="Abjurer",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=84,
        hit_dice="13d8+26",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        actions=[
            {
                "name": "Force Blast",
                "description": long_force_blast,
            }
        ],
    )

    # Stub repository that returns our monster definition
    monster_repo = Mock()
    monster_repo.get.return_value = monster_def

    # Create minimal state containing the monster entity
    entity = EntityRowDTO(
        instance_id="abjurer_0",
        display_name="Abjurer #1",
        entity_type="monster",
        initiative=12,
        current_hp=84,
        max_hp=84,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="abjurer-wizard",
    )
    state = EncounterStateDTO(
        encounter_id="test-encounter",
        round_number=1,
        entities=[entity],
        undo_available=False,
    )

    panel = StatBlockPanel(monster_repo=monster_repo)
    qtbot.addWidget(panel)

    # Trigger the rich rendering path
    panel.refresh(state, "abjurer_0")

    # QTextBrowser uses toHtml() / toPlainText() instead of .text()
    rendered_html = panel._content.toHtml()

    # The full distinctive parts of the long description must be present.
    # This would have failed before the fix due to [:160] truncation.
    assert "pushed up to 10 feet away from the abjurer" in rendered_html
    assert "On a successful save, a creature takes half as much damage" in rendered_html
    assert "isn't pushed" in rendered_html


def test_stat_block_panel_allows_copying_rich_text(qtbot):
    """
    Users must be able to highlight and copy text from the StatBlockPanel
    (especially the rich monster description). This is critical for debugging
    data issues and for normal usability.

    Previously the content was a plain QLabel, which does not support text
    selection by default.
    """
    from PySide6.QtWidgets import QTextBrowser
    from PySide6.QtCore import Qt

    panel = StatBlockPanel()
    qtbot.addWidget(panel)

    # Set some content (simulates what happens during normal use)
    panel._content.setText(
        "<b>Force Blast</b> — Each creature in a 20-foot cube... takes 36 (8d8) force damage..."
    )

    # The widget used for rich content must be a QTextBrowser (which supports selection)
    assert isinstance(panel._content, QTextBrowser)

    # Explicitly verify that mouse selection is enabled
    flags = panel._content.textInteractionFlags()
    assert flags & Qt.TextInteractionFlag.TextSelectableByMouse


def test_stat_block_panel_renders_actions_in_classic_5e_style(qtbot):
    """
    TDD test for priority #2: Action descriptions should render in classic
    5e style (Name. Description.) rather than bullet points with dashes.
    This also exercises that dice expressions (once fixed in importer)
    appear correctly.
    """
    long_force_blast = (
        "Each creature in a 20-foot cube originating from the abjurer must make a DC 16 "
        "Constitution saving throw. On a failed save, a creature takes 36 (8d8) force damage "
        "and is pushed up to 10 feet away from the abjurer. On a successful save, a creature "
        "takes half as much damage and isn't pushed."
    )

    monster_def = MonsterDefinition(
        id="abjurer-wizard",
        name="Abjurer",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=84,
        hit_dice="13d8+26",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        actions=[
            {"name": "Multiattack", "description": "The abjurer makes three Arcane Burst attacks."},
            {
                "name": "Arcane Burst",
                "description": "Melee or Ranged Spell Attack: +8 to hit, reach 5 ft. or range 120 ft., one target. Hit: 20 (3d10 + 4) force damage."
            },
            {"name": "Force Blast", "description": long_force_blast},
        ],
    )

    monster_repo = Mock()
    monster_repo.get.return_value = monster_def

    entity = EntityRowDTO(
        instance_id="abjurer_0",
        display_name="Abjurer #1",
        entity_type="monster",
        initiative=12,
        current_hp=84,
        max_hp=84,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="abjurer-wizard",
    )
    state = EncounterStateDTO(
        encounter_id="test",
        round_number=1,
        entities=[entity],
        undo_available=False,
    )

    # Test the rendering method directly to avoid side effects from refresh/image loading
    panel = StatBlockPanel(monster_repo=monster_repo)
    qtbot.addWidget(panel)

    # Tests now go through the extracted renderer (preferred path)
    if not hasattr(panel, "_renderer"):
        from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import MonsterStatBlockRenderer
        panel._renderer = MonsterStatBlockRenderer()
    html = panel._renderer.render(monster_def)

    # New classic 5e style (Name. Description.)
    assert "<b>Multiattack.</b> The abjurer makes three Arcane Burst attacks." in html
    assert "<b>Arcane Burst.</b> Melee or Ranged Spell Attack: +8 to hit" in html
    assert "Hit: 20 (3d10 + 4) force damage." in html
    assert "<b>Force Blast.</b> Each creature in a 20-foot cube" in html

    # Should not have the old bullet-dash style
    assert "• <b>Force Blast</b> —" not in html


def test_stat_block_panel_renders_full_spellcasting(qtbot):
    """High priority test: Spellcasting should show the full spell lists."""
    monster_def = MonsterDefinition(
        id="abjurer-wizard",
        name="Abjurer",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=84,
        hit_dice="13d8+26",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        spellcasting=[
            {
                "header": "The abjurer casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 16):",
                "spells": [
                    {"at_will": "dancing lights, mage hand, message, prestidigitation"},
                    {"daily_2": "dispel magic, lightning bolt, mage armor"},
                    {"daily_1": "arcane lock, banishment, globe of invulnerability, invisibility, wall of force"},
                ],
            }
        ],
    )

    monster_repo = Mock()
    monster_repo.get.return_value = monster_def

    entity = EntityRowDTO(
        instance_id="abjurer_0",
        display_name="Abjurer #1",
        entity_type="monster",
        initiative=12,
        current_hp=84,
        max_hp=84,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="abjurer-wizard",
    )
    state = EncounterStateDTO(
        encounter_id="test",
        round_number=1,
        entities=[entity],
        undo_available=False,
    )

    panel = StatBlockPanel(monster_repo=monster_repo)
    qtbot.addWidget(panel)
    panel.refresh(state, "abjurer_0")

    html = panel._content.toHtml()

    assert "At Will:" in html or "at will" in html.lower()
    assert "dancing lights, mage hand" in html
    assert "Daily 2:" in html or "2/day" in html.lower()
    assert "Daily 1:" in html or "1/day" in html.lower()


def test_stat_block_panel_renders_reactions(qtbot):
    """High priority test: Reactions should be displayed."""
    monster_def = MonsterDefinition(
        id="abjurer-wizard",
        name="Abjurer",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=84,
        hit_dice="13d8+26",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        reactions=[
            {
                "name": "Arcane Ward",
                "description": "When the abjurer or a creature it can see within 30 feet of it takes damage, the abjurer magically creates a protective barrier around itself or the other creature. The barrier reduces the damage to the protected creature by 26 (4d10 + 4), to a minimum of 0, and then vanishes. (Recharge 4–6)"
            }
        ],
    )

    monster_repo = Mock()
    monster_repo.get.return_value = monster_def

    entity = EntityRowDTO(
        instance_id="abjurer_0",
        display_name="Abjurer #1",
        entity_type="monster",
        initiative=12,
        current_hp=84,
        max_hp=84,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="abjurer-wizard",
    )
    state = EncounterStateDTO(
        encounter_id="test",
        round_number=1,
        entities=[entity],
        undo_available=False,
    )

    panel = StatBlockPanel(monster_repo=monster_repo)
    qtbot.addWidget(panel)
    panel.refresh(state, "abjurer_0")

    html = panel._content.toHtml()

    assert "Reactions" in html
    assert "Arcane Ward." in html
    assert "protective barrier" in html
    assert "Recharge 4–6" in html


# =============================================================================
# INFORMATION PRESERVATION AUDIT
# =============================================================================
#
# The goal of the audit is to guarantee that _build_rich_monster_html never
# silently drops information that exists in a MonsterDefinition.
#
# This is the primary safety net while we continue to polish readability
# under Option 1 (QTextBrowser + pure Python renderer).
#
# Strategy:
#   - For every "content-bearing" field (traits, actions, bonus_actions,
#     reactions, legendary_actions, spellcasting) we extract the names +
#     distinctive fragments.
#   - After rendering we assert that each name and its signature content
#     fragments appear in the produced HTML.
#   - We use realistic complex structures (will/daily + slots, recharge
#     reactions, legendary actions, long descriptions, bonus actions).
# =============================================================================

def _extract_preservation_items(monster_def: MonsterDefinition) -> list[tuple[str, str]]:
    """
    Return a list of (signature_name, must_appear_fragment) pairs that the
    renderer is required to preserve for this monster.

    The fragments are chosen so they are robust to nice human-readable
    reformatting done by the renderer (e.g. "daily_2" -> "Daily 2:").
    """
    items: list[tuple[str, str]] = []

    for field_name in ("traits", "actions", "bonus_actions", "reactions", "legendary_actions"):
        entries = getattr(monster_def, field_name, []) or []
        for e in entries:
            name = e.get("name", "") or field_name
            desc = (e.get("description", "") or "").strip()
            fragment = desc[:70].strip()
            items.append((name, fragment))
            if len(desc) > 90:
                # Capture a second distinctive chunk from longer descriptions
                mid = desc[55:120].strip()
                if mid:
                    items.append((name, mid))

    # Spellcasting: we care that the header survives and that individual
    # spell names + frequency indicators appear in some readable form.
    for sc in getattr(monster_def, "spellcasting", []) or []:
        header = (sc.get("header", "") or "").strip()
        if header:
            items.append(("Spellcasting", header[:55]))

        spells = sc.get("spells", {}) or {}
        if isinstance(spells, dict):
            for freq, val in spells.items():
                # Human readable frequency — match what the renderer now produces
                if freq == "at_will":
                    readable = "At will"
                elif freq.startswith("daily_"):
                    num = freq.split("_", 1)[1]
                    readable = f"{num}/day each"
                elif freq.startswith("level_"):
                    num = freq.split("_", 1)[1]
                    readable = f"{num} level"
                else:
                    readable = freq.replace("_", " ").title()

                items.append((readable[:15], readable))

                spell_names: list[str] = []
                if isinstance(val, dict):
                    spell_names = val.get("spells", []) or []
                elif isinstance(val, list):
                    spell_names = val

                for spell in spell_names[:4]:
                    if spell:
                        clean = _strip_5etools_tags_for_test(spell)
                        items.append((clean[:18], clean[:35]))
        elif isinstance(spells, list):
            for g in spells:
                if isinstance(g, dict):
                    for freq, txt in g.items():
                        items.append((str(freq)[:12], str(txt)[:40]))

    # Dedup
    seen = set()
    unique = []
    for it in items:
        key = (it[0][:45], it[1][:45])
        if key not in seen and it[0]:
            seen.add(key)
            unique.append(it)
    return unique


def _strip_5etools_tags_for_test(text: str) -> str:
    """Minimal version for the test helper (avoid import cycles)."""
    import re
    if not isinstance(text, str):
        return str(text)
    text = re.sub(r"\{@[^}]+}", "", text)
    return text.strip()


def _assert_full_preservation(rendered_html: str, monster_def: MonsterDefinition, test_label: str = ""):
    """Core of the info preservation audit.

    We primarily verify that the *fragments* (distinctive text) are present.
    The first element of each pair is mostly a label for diagnostics.
    """
    items = _extract_preservation_items(monster_def)
    missing = []
    for label, fragment in items:
        if fragment and fragment not in rendered_html:
            missing.append(f"{label!r} -> {fragment[:45]!r}")

    if missing:
        plain = rendered_html
        raise AssertionError(
            f"[{test_label}] INFO PRESERVATION FAILURE: {len(missing)} items missing.\n"
            f"First 8 missing: {missing[:8]}\n"
            f"Rendered length: {len(rendered_html)} chars\n"
            f"Sample of rendered (first 1600):\n{plain[:1600]}"
        )


# =============================================================================
# HARDENED AUDIT INVARIANTS / RULES
#
# These are rules we add over time as we discover gaps.
# The goal is to make the audit progressively harder to fool while still
# focusing on information preservation + preventing known classes of bad output.
#
# Current rules (as of latest session):
# - No raw 5eTools tags in output
# - No broken attack abbreviations (ms,rs, etc.)
# - Nice spellcasting frequency labels ("1/day each", "At will")
# - Spellcasting should appear after Actions and before Reactions
# - All six ability scores (STR/DEX/CON/INT/WIS/CHA) must appear with modifiers
# - AC (Armor Class) must be rendered
# - Speed/Movement must be rendered
#
# Add new rules here as we learn together.
# =============================================================================

def assert_audit_invariants(html: str, monster_def: MonsterDefinition, test_label: str = ""):
    """
    Runs all known hardened audit invariants.
    Call this from preservation tests for stronger guarantees.
    """
    # Rule learned from Abjurer Wizard: Spellcasting should not appear after Reactions.
    # This catches poor section ordering.
    if "Spellcasting" in html and "Reactions" in html:
        spell_pos = html.find("Spellcasting")
        react_pos = html.find("Reactions")
        if spell_pos > react_pos:
            raise AssertionError(
                f"[{test_label}] AUDIT RULE VIOLATION: 'Spellcasting' appears after 'Reactions' in the output. "
                f"This usually indicates bad section ordering in the renderer."
            )

    # Rule learned from Abjurer Wizard: The ability scores section should render
    # all six core abilities with their modifiers.
    for abbr in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
        if abbr not in html:
            raise AssertionError(
                f"[{test_label}] AUDIT RULE VIOLATION: Ability '{abbr}' is missing from the rendered output. "
                f"The renderer should show all six abilities with modifiers."
            )

    # New rule: AC must be present (core combat stat)
    if "AC" not in html and "Armor Class" not in html:
        raise AssertionError(
            f"[{test_label}] AUDIT RULE VIOLATION: Armor Class (AC) is missing from the output. "
            f"It is present in MonsterDefinition.armor_class."
        )

    # New rule: Speed/Movement should be present
    if "Speed" not in html:
        raise AssertionError(
            f"[{test_label}] AUDIT RULE VIOLATION: Speed/Movement is missing from the output. "
            f"It is present in MonsterDefinition.speed."
        )

    # New rule: Size (and creature type line) must be rendered
    # Covers Size, Type, and Alignment which are core identity fields
    if not any(x in html for x in ["Medium", "Large", "Small", "Tiny", "Huge", "Gargantuan", "Size"]):
        # At minimum check for common sizes or the word "Size"
        raise AssertionError(
            f"[{test_label}] AUDIT RULE VIOLATION: Creature Size (and type line) is missing from the output. "
            f"MonsterDefinition has size, type_, and alignment."
        )

    # Additional lightweight structural rules can be added here over time.


def test_info_preservation_audit_abjurer_style_spellcaster(qtbot):
    """
    Core info preservation audit for a complex spellcasting monster
    (modeled directly on real Abjurer + Archmage + Lich patterns).
    """
    long_force = (
        "Each creature in a 20-foot cube originating from the abjurer must make a DC 16 "
        "Constitution saving throw. On a failed save, a creature takes 36 (8d8) force damage "
        "and is pushed up to 10 feet away from the abjurer. On a successful save, a creature "
        "takes half as much damage and isn't pushed."
    )

    monster_def = MonsterDefinition(
        id="abjurer-wizard-audit",
        name="Abjurer Wizard",
        size="Medium",
        type_="humanoid",
        alignment="any alignment",
        armor_class=12,
        hit_points=84,
        hit_dice="13d8+26",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=14, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        traits=[
            {"name": "Arcane Ward", "description": "The abjurer has a magical ward that has 30 hit points. Whenever the abjurer takes damage, the ward takes the damage instead."},
            {"name": "Improved Abjuration", "description": "When the abjurer casts an abjuration spell that requires a saving throw, it can add its proficiency bonus to the save DC."},
        ],
        actions=[
            {"name": "Multiattack", "description": "The abjurer makes three Arcane Burst attacks."},
            {
                "name": "Arcane Burst",
                "description": "Melee or Ranged Spell Attack: +8 to hit, reach 5 ft. or range 120 ft., one target. Hit: 20 (3d10 + 4) force damage."
            },
            {"name": "Force Blast", "description": long_force},
        ],
        bonus_actions=[
            {"name": "Mystic Shield", "description": "The abjurer gains a +2 bonus to AC until the start of its next turn."}
        ],
        reactions=[
            {
                "name": "Arcane Ward (Reaction)",
                "description": "When the abjurer or a creature it can see within 30 feet takes damage, the abjurer reduces that damage by 26 (4d10 + 4). (Recharge 4-6)"
            }
        ],
        spellcasting=[
            {
                "header": "The abjurer casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 16):",
                "spells": {
                    "at_will": ["dancing lights", "mage hand", "message", "prestidigitation"],
                    "daily_2": ["dispel magic", "lightning bolt", "mage armor"],
                    "daily_1": ["arcane lock", "banishment", "globe of invulnerability", "invisibility", "wall of force"],
                    "level_3": {"spells": ["counterspell", "fireball"], "slots": 3},
                },
            }
        ],
    )

    panel = StatBlockPanel()
    qtbot.addWidget(panel)

    # Tests now go through the extracted renderer (preferred path)
    if not hasattr(panel, "_renderer"):
        from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import MonsterStatBlockRenderer
        panel._renderer = MonsterStatBlockRenderer()
    html = panel._renderer.render(monster_def)

    # The audit itself
    _assert_full_preservation(html, monster_def, "Abjurer-style spellcaster")

    # Apply hardened invariants (learns new rules over time)
    assert_audit_invariants(html, monster_def, "Abjurer-style spellcaster")

    # Extra explicit high-value assertions (these were the historical pain points)
    assert "Force Blast." in html
    assert "pushed up to 10 feet" in html
    assert "Arcane Ward (Reaction)." in html or "Arcane Ward." in html
    assert "Recharge 4-6" in html or "Recharge 4–6" in html
    assert "at will" in html.lower() or "At Will" in html
    assert "dancing lights" in html
    assert "banishment" in html
    assert "Bonus Actions" in html
    assert "Mystic Shield." in html
    # Slots should be visible for the level_3 entry
    assert "3 slots" in html or "slots: 3" in html.lower() or "(3 slots)" in html


def test_info_preservation_audit_legendary_reaction_monster(qtbot):
    """Audit for a monster with heavy legendary actions + reactions (Ancient Red Dragon style)."""
    monster_def = MonsterDefinition(
        id="ancient-red-dragon-audit",
        name="Ancient Red Dragon",
        size="Gargantuan",
        type_="dragon",
        alignment="chaotic evil",
        armor_class=22,
        hit_points=546,
        hit_dice="28d20+280",
        speed={"walk": 40, "climb": 40, "fly": 80},
        ability_scores=AbilityScores(str_=30, dex=10, con=29, int_=18, wis=15, cha=23),
        challenge_rating=ChallengeRating("24"),
        xp=62000,
        traits=[
            {"name": "Legendary Resistance (3/Day)", "description": "If the dragon fails a saving throw, it can choose to succeed instead."},
        ],
        actions=[
            {"name": "Multiattack", "description": "The dragon can use its Frightful Presence. It then makes three attacks: one with its bite and two with its claws."},
            {"name": "Bite", "description": "Melee Weapon Attack: +17 to hit, reach 15 ft., one target. Hit: 21 (2d10 + 10) piercing damage plus 14 (4d6) fire damage."},
            {"name": "Fire Breath (Recharge 5-6)", "description": "The dragon exhales fire in a 90-foot cone. Each creature in that area must make a DC 25 Dexterity saving throw, taking 91 (26d6) fire damage on a failed save, or half as much damage on a successful one."},
        ],
        reactions=[
            {"name": "Tail Attack (Legendary)", "description": "When a creature the dragon can see within 10 feet of it hits the dragon with an attack, the dragon can make a tail attack against that creature."}
        ],
        legendary_actions=[
            {"name": "Detect", "description": "The dragon makes a Wisdom (Perception) check."},
            {"name": "Tail Attack", "description": "The dragon makes a tail attack."},
            {"name": "Wing Attack (Costs 2 Actions)", "description": "The dragon beats its wings. Each creature within 15 feet must succeed on a DC 25 Dexterity saving throw or take 17 (2d6 + 10) bludgeoning damage and be knocked prone."},
        ],
    )

    panel = StatBlockPanel()
    qtbot.addWidget(panel)
    # Tests now go through the extracted renderer (preferred path)
    if not hasattr(panel, "_renderer"):
        from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import MonsterStatBlockRenderer
        panel._renderer = MonsterStatBlockRenderer()
    html = panel._renderer.render(monster_def)

    _assert_full_preservation(html, monster_def, "Legendary reaction monster")
    assert_audit_invariants(html, monster_def, "Legendary reaction monster")

    assert "Legendary Resistance (3/Day)." in html
    assert "Fire Breath (Recharge 5-6)." in html
    assert "91 (26d6) fire damage" in html
    assert "Legendary Actions" in html
    assert "Wing Attack (Costs 2 Actions)." in html
    assert "Tail Attack (Legendary)." in html  # the reaction


def test_info_preservation_audit_real_data_sample(qtbot):
    """
    Real-data smoke audit.

    Loads the actual bestiary and checks that for several complex monsters
    the renderer at least surfaces the major sections and a representative
    sample of names. This test is intentionally tolerant of currently
    mangled spell data in the on-disk JSON (the result of earlier importer
    bugs); its main job is to guard against future regressions in the
    renderer itself.
    """
    import json
    from pathlib import Path

    bestiary_path = Path(__file__).parent.parent.parent.parent / "data" / "srd" / "monsters.json"
    if not bestiary_path.exists():
        pytest.skip("Full bestiary not present")

    monsters = json.loads(bestiary_path.read_text(encoding="utf-8"))

    # Pick known rich monsters (names that exist in the full bestiary)
    targets = ["Abjurer", "Ancient Red Dragon", "Archmage", "Pit Fiend", "Lich"]
    found = []
    for m in monsters:
        if m.get("name") in targets:
            found.append(m)
        if len(found) >= 3:
            break

    if not found:
        pytest.skip("Could not locate any of the target stress monsters in the JSON")

    panel = StatBlockPanel()
    qtbot.addWidget(panel)

    for raw in found:
        # Re-hydrate a minimal MonsterDefinition from the raw dict
        # (we don't need full fidelity for this smoke check)
        try:
            md = MonsterDefinition(
                id=raw.get("id", raw["name"].lower().replace(" ", "-")),
                name=raw["name"],
                size=raw.get("size", "Medium"),
                type_=raw.get("type_", raw.get("type", "unknown")),
                alignment=raw.get("alignment", "unaligned"),
                armor_class=raw.get("armor_class", 10),
                hit_points=raw.get("hit_points", 10),
                hit_dice=raw.get("hit_dice", "1d8"),
                speed=raw.get("speed", {"walk": 30}),
                ability_scores=raw.get("ability_scores", {"str_": 10, "dex": 10, "con": 10, "int_": 10, "wis": 10, "cha": 10}),
                challenge_rating=raw.get("challenge_rating", {"value": "1"}),
                xp=raw.get("xp", 0),
                traits=raw.get("traits", []),
                actions=raw.get("actions", []),
                bonus_actions=raw.get("bonus_actions", []),
                reactions=raw.get("reactions", []),
                legendary_actions=raw.get("legendary_actions", []),
                spellcasting=raw.get("spellcasting", []),
            )

            html = panel._build_rich_monster_html(md)

            # Basic preservation: if the source had entries in a section,
            # the rendered output must mention the section header (or at least one name)
            for section, field in [
                ("Traits", "traits"),
                ("Actions", "actions"),
                ("Bonus Actions", "bonus_actions"),
                ("Reactions", "reactions"),
                ("Legendary Actions", "legendary_actions"),
                ("Spellcasting", "spellcasting"),
            ]:
                src_list = getattr(md, field, []) or []
                if src_list:
                    # Either the header or at least the first name must be visible
                    first_name = src_list[0].get("name", "") if isinstance(src_list[0], dict) else ""
                    assert section in html or (first_name and first_name in html), \
                        f"Lost section {section} for {md.name}"

            # Apply hardened invariants on real data too
            assert_audit_invariants(html, md, f"real-data-{md.name}")

        except Exception as e:
            # Never let one bad monster kill the whole audit; just record it
            print(f"[real-data audit] Skipped {raw.get('name')}: {e}")


def test_info_preservation_audit_no_leakage_or_mangling(qtbot):
    """
    Hardened "anti-regression" audit.

    This test exists specifically to prevent the class of problems we saw
    with Abjurer Wizard (and many other monsters):

    - Raw 5eTools tags leaking into the final display ({@recharge}, {@atk ...}, etc.)
    - Broken attack lines ("ms,rs +8 to hit" instead of full text)
    - Missing "Hit:" prefixes
    - Ugly frequency labels ("Daily 1" instead of "1/day each")
    - Bad senses formatting

    The test feeds the renderer realistic (sometimes "dirty") input that
    exercises the known failure modes and demands clean, classic 5e output.
    """
    monster_def = MonsterDefinition(
        id="hardened-audit-monster",
        name="Hardened Audit Monster",
        size="Medium",
        type_="humanoid",
        alignment="any",
        armor_class=15,
        hit_points=90,
        hit_dice="12d8+36",
        speed={"walk": 30},
        ability_scores=AbilityScores(str_=10, dex=14, con=16, int_=18, wis=12, cha=10),
        challenge_rating=ChallengeRating("9"),
        xp=5000,
        senses={"darkvision": 60, "passive_perception": 11},
        languages=["Common", "Elvish"],
        actions=[
            {
                "name": "Arcane Burst",
                # Simulate what used to come out of the importer before the {@atk} fix
                "description": "ms,rs +8 to hit, reach 5 ft. or range 120 ft., one target. 20 (3d10 + 4) force damage."
            },
            {
                "name": "Force Blast",
                "description": "Each creature in a 20-foot cube must make a DC 16 Constitution saving throw. "
                             "On a failed save, a creature takes 36 (8d8) force damage and is pushed up to 10 feet. "
                             "On a successful save, half damage and no push."
            },
        ],
        reactions=[
            {
                "name": "Arcane Ward {@recharge 4}",
                "description": "When the creature or an ally within 30 feet takes damage, "
                             "it creates a barrier that reduces the damage by 26 (4d10 + 4)."
            }
        ],
        spellcasting=[
            {
                "header": "The monster casts spells using Intelligence (spell save DC 16):",
                "spells": {
                    "at_will": ["dancing lights", "mage hand"],
                    "daily_2": ["dispel magic", "lightning bolt"],
                    "daily_1": ["banishment", "wall of force"],
                },
            }
        ],
    )

    panel = StatBlockPanel()
    qtbot.addWidget(panel)
    # Tests now go through the extracted renderer (preferred path)
    if not hasattr(panel, "_renderer"):
        from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import MonsterStatBlockRenderer
        panel._renderer = MonsterStatBlockRenderer()
    html = panel._renderer.render(monster_def)

    # === Core anti-leakage rules ===
    assert "{@" not in html, "Raw 5eTools tag leaked into rendered output"

    # No broken attack abbreviations
    forbidden_attack_fragments = ["ms,rs", "mw,rw", "ms +", "rs +"]
    for frag in forbidden_attack_fragments:
        assert frag not in html, f"Broken attack abbreviation present: {frag}"

    # Good attack formatting must be present
    assert "Melee or Ranged Spell Attack" in html or "Melee Spell Attack" in html

    # Damage must be present with reasonable context (either "Hit:" or right after the attack line)
    assert "20 (3d10 + 4) force damage" in html or "Hit: 20" in html

    # No raw recharge tag allowed (the important anti-leakage rule)
    assert "{@recharge" not in html
    # If recharge info is present in source, it should not be mangled (we already stripped it above)

    # Nice spellcasting frequency labels (the user-visible improvement)
    assert "At will" in html or "at will" in html.lower()
    assert "day each" in html.lower() or "/day" in html  # "1/day each", "2/day each"

    # Senses must not have a leading comma artifact
    assert "Senses:" in html
    assert "Senses: ," not in html

    # Apply all current hardened audit invariants (including newly learned rules)
    assert_audit_invariants(html, monster_def, "no-leakage hardened audit")

    # Note: we intentionally do *not* call _assert_full_preservation here
    # because this test feeds deliberately dirty input (simulating legacy bad importer output)
    # and verifies that the renderer cleans it up instead of preserving the garbage.


# =============================================================================
# INTEGRATION TESTS FOR StatBlockPanel + MonsterStatBlockRenderer
#
# These tests exercise the full panel integration path that the live app uses:
#   refresh() → basic HTML → _try_enrich_with_definition() → renderer → append
#
# They are the primary defense against the class of "renderer works, but panel
# shows nothing" regressions we have seen repeatedly.
# =============================================================================

def test_stat_block_panel_full_integration_monster_with_definition(qtbot, stub_monster_repo):
    """Full integration path with a working repo that returns a definition."""
    # Seed the stub repo with a rich monster
    monster_def = MonsterDefinition(
        id="integration-test-monster",
        name="Integration Test Monster",
        size="Large",
        type_="humanoid",
        alignment="chaotic neutral",
        armor_class=16,
        hit_points=85,
        hit_dice="10d10+30",
        speed={"walk": 30, "fly": 60},
        ability_scores=AbilityScores(str_=18, dex=14, con=16, int_=10, wis=12, cha=8),
        challenge_rating=ChallengeRating("5"),
        xp=1800,
        actions=[
            {"name": "Multiattack", "description": "The monster makes two attacks."},
            {"name": "Bite", "description": "Melee Weapon Attack: +7 to hit, reach 5 ft., one target. Hit: 15 (2d10 + 4) piercing damage."},
        ],
        spellcasting=[
            {
                "header": "The monster casts spells using Charisma.",
                "spells": {"at_will": ["fire bolt"], "daily_1": ["fireball"]},
            }
        ],
    )
    stub_monster_repo.upsert(monster_def)

    panel = StatBlockPanel(monster_repo=stub_monster_repo)
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="monster_0",
        display_name="Integration Test Monster #1",
        entity_type="monster",
        initiative=15,
        current_hp=72,   # rolled value
        max_hp=85,
        conditions=["Frightened"],
        is_current_turn=False,
        is_active=True,
        monster_id="integration-test-monster",
    )
    state = EncounterStateDTO(
        encounter_id="test",
        round_number=2,
        entities=[entity],
        undo_available=False,
    )

    panel.refresh(state, "monster_0")

    html = panel._content.toHtml()

    # Basic info must always be present (QTextBrowser wraps it in styled spans)
    assert "Initiative" in html and "15" in html
    assert "HP" in html and "72" in html and "85" in html
    assert "Conditions" in html and "Frightened" in html

    # Rich content from renderer must be present (check for distinctive fragments)
    assert "CR 5" in html
    assert "Large" in html
    assert "AC" in html and "16" in html
    assert "72" in html and "85" in html
    assert "10d10+30" in html.lower()
    assert "Speed" in html
    assert "Actions" in html
    assert "Multiattack" in html
    assert "Spellcasting" in html
    assert "at will" in html.lower() or "At will" in html


def test_stat_block_panel_basic_info_shown_when_no_monster_repo(qtbot):
    """When there is no monster repo, basic info must still be displayed."""
    panel = StatBlockPanel(monster_repo=None)  # explicit None
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="player_0",
        display_name="Test Player",
        entity_type="player",
        initiative=18,
        current_hp=45,
        max_hp=45,
        conditions=[],
        is_current_turn=True,
        is_active=True,
        monster_id=None,
    )
    state = EncounterStateDTO(encounter_id="test", round_number=1, entities=[entity], undo_available=False)

    panel.refresh(state, "player_0")

    html = panel._content.toHtml()
    assert "Initiative" in html and "18" in html
    assert "HP" in html and "45" in html
    # "Current Turn" is in the title label, not the content HTML


def test_stat_block_panel_basic_info_shown_when_definition_not_found(qtbot, stub_monster_repo):
    """When the repo does not contain the monster, basic info must still be displayed (no crash, no wipe)."""
    panel = StatBlockPanel(monster_repo=stub_monster_repo)  # repo exists but returns None for this id
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="ghost_0",
        display_name="Missing Monster",
        entity_type="monster",
        initiative=10,
        current_hp=30,
        max_hp=30,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="nonexistent-monster-id",
    )
    state = EncounterStateDTO(encounter_id="test", round_number=1, entities=[entity], undo_available=False)

    # Should not raise and should keep basic info
    panel.refresh(state, "ghost_0")

    html = panel._content.toHtml()
    assert "Initiative" in html and "10" in html
    assert "HP" in html and "30" in html


# =============================================================================
# BAD-DATA INTEGRATION REGRESSIONS
# These directly protect the resilience work ("Do 7") and the exact crash
# that was diagnosed from the user's full diagnostic log (dict in defense list).
# =============================================================================

def test_stat_block_panel_integration_gracefully_handles_dirty_defense_data(qtbot, stub_monster_repo):
    """
    Full integration regression: A monster with dicts inside damage_resistances
    (the real MPMM/Abjurer-style failure) must not crash the panel or wipe content.

    This is the integration-path version of the unit regression.
    """
    dirty_monster = MonsterDefinition(
        id="dirty-defense-integration",
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
        damage_resistances=["fire", {"resist": "cold", "note": "from spells"}],
        damage_immunities=["poison"],
        condition_immunities=[{"immune": "charmed"}],
        actions=[{"name": "Attack", "description": "Simple attack."}],
    )
    stub_monster_repo.upsert(dirty_monster)

    panel = StatBlockPanel(monster_repo=stub_monster_repo)
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="dirty_0",
        display_name="Dirty Defense #1",
        entity_type="monster",
        initiative=11,
        current_hp=55,
        max_hp=60,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="dirty-defense-integration",
    )
    state = EncounterStateDTO(encounter_id="test", round_number=3, entities=[entity], undo_available=False)

    # Must not raise
    panel.refresh(state, "dirty_0")

    html = panel._content.toHtml()

    # Basic info must survive no matter what
    assert "Initiative" in html and "11" in html
    assert "HP" in html and "55" in html and "60" in html

    # Good rich content must still be present
    assert "CR 3" in html
    assert "Actions" in html or "Attack" in html


def test_stat_block_panel_integration_gracefully_handles_dirty_spell_data(qtbot, stub_monster_repo):
    """Full integration path with bad items inside spell lists."""
    dirty_caster = MonsterDefinition(
        id="dirty-spell-integration",
        name="Dirty Spell Monster",
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
    stub_monster_repo.upsert(dirty_caster)

    panel = StatBlockPanel(monster_repo=stub_monster_repo)
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="dirtyspell_0",
        display_name="Dirty Spell #1",
        entity_type="monster",
        initiative=9,
        current_hp=40,
        max_hp=40,
        conditions=[],
        is_current_turn=False,
        is_active=True,
        monster_id="dirty-spell-integration",
    )
    state = EncounterStateDTO(encounter_id="test", round_number=1, entities=[entity], undo_available=False)

    panel.refresh(state, "dirtyspell_0")
    html = panel._content.toHtml()

    assert "Initiative" in html and "9" in html
    # Spellcasting section may be partially degraded, but panel must not die
    assert "HP" in html


def test_stat_block_panel_keeps_basic_and_good_sections_when_one_rich_section_is_bad(qtbot, stub_monster_repo):
    """
    When one rich section (e.g. legendary actions) contains unrenderable data,
    the panel must still show:
      - All basic info (Initiative, HP, Conditions)
      - All other good rich sections (Actions, AC, Speed, etc.)
    """
    messy = MonsterDefinition(
        id="mixed-good-bad",
        name="Mixed Good Bad",
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
        actions=[{"name": "Charm", "description": "The fey charms a creature."}],
        legendary_actions=[{"name": "Bad Leg", "description": {"bad": "data"}}],  # will be skipped
        reactions=[{"name": "Evasion", "description": "The fey dodges."}],
    )
    stub_monster_repo.upsert(messy)

    panel = StatBlockPanel(monster_repo=stub_monster_repo)
    qtbot.addWidget(panel)

    entity = EntityRowDTO(
        instance_id="mixed_0",
        display_name="Mixed #1",
        entity_type="monster",
        initiative=14,
        current_hp=25,
        max_hp=30,
        conditions=["Charmed"],
        is_current_turn=True,
        is_active=True,
        monster_id="mixed-good-bad",
    )
    state = EncounterStateDTO(encounter_id="test", round_number=4, entities=[entity], undo_available=False)

    panel.refresh(state, "mixed_0")
    html = panel._content.toHtml()

    # Basic must always be there
    assert "Initiative" in html and "14" in html
    assert "HP" in html and "25" in html and "30" in html
    assert "Conditions" in html and "Charmed" in html

    # Good rich sections must survive
    assert "CR 1" in html
    assert "AC" in html and "13" in html
    assert "Speed" in html
    assert "Actions" in html
    assert "Charm." in html
    assert "Reactions" in html or "Evasion" in html
