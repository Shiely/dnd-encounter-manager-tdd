"""
Basic smoke tests for the committed bestiary data quality.

These tests exist to catch regressions in the generated monsters.json
and to ensure that the data we ship to users/clones is reasonably clean.

They are intentionally lightweight and do not replace proper importer tests.
"""
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def bestiary():
    path = Path(__file__).parent.parent.parent / "data" / "srd" / "monsters.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_bestiary_loads(bestiary):
    assert len(bestiary) > 1000, "Bestiary seems suspiciously small"


def test_no_obvious_raw_tags_in_key_fields(bestiary):
    """Catch raw 5eTools tags leaking into descriptions we display."""
    bad_tags = ["{@spell", "{@damage", "{@dice", "{@atk"]
    problems = []

    for monster in bestiary:
        name = monster.get("name", "Unknown")
        for field in ["description", "header"]:
            text = str(monster.get(field, ""))
            for tag in bad_tags:
                if tag in text:
                    problems.append(f"{name} has {tag} in {field}")

    # We allow a small number for now, but this should trend toward zero
    assert len(problems) < 50, "Too many raw tags found:\n" + "\n".join(problems[:20])


def test_no_xphb_leaking_in_display_text(bestiary):
    """
    XPHB (and similar source codes like XDMG, XMM) must NEVER appear raw
    in the committed bestiary data that ships to users and fresh clones.

    These are 5eTools internal source abbreviations. The importer's
    _strip_5etools_tags MUST convert them to readable names or remove them.
    """
    source_codes = {"XPHB", "XDMG", "XMM", "XDmg"}  # common 2024 sources
    problems = []
    examples = []

    for monster in bestiary:
        name = monster.get("name", "Unknown")
        for field in ["spellcasting", "actions", "traits", "bonus_actions",
                      "reactions", "legendary_actions", "description", "header"]:
            val = monster.get(field)
            if val:
                text = json.dumps(val) if not isinstance(val, str) else val
                for code in source_codes:
                    if code in text:
                        problems.append(name)
                        if len(examples) < 5:
                            # capture a small snippet for diagnosis
                            idx = text.find(code)
                            snip = text[max(0, idx-30):idx+40]
                            examples.append(f"{name}.{field}: ...{snip}...")
                        break
            if name in problems:
                break

    # This audit MUST catch the problem. Zero tolerance for source codes
    # leaking into user-visible data.
    assert len(problems) == 0, (
        f"XPHB/XDMG/etc. source codes leaking into bestiary display text "
        f"({len(problems)} monsters). This breaks StatBlockPanel rendering.\n"
        f"Examples:\n" + "\n".join(examples) +
        "\n\nFix: improve _strip_5etools_tags in utilities/import_srd_monsters.py "
        "then re-run import_full_bestiary.py and commit the new monsters.json."
    )


def test_abjurer_spellcasting_is_reasonably_clean(bestiary):
    """Specific regression test for a historically problematic monster."""
    abjurer = next((m for m in bestiary if m.get("id") == "abjurer-wizard"), None)
    assert abjurer is not None, "Abjurer Wizard not found in bestiary"

    spellcasting = abjurer.get("spellcasting", [])
    assert len(spellcasting) > 0

    # Check that we have a structured spells dict rather than raw garbage
    first = spellcasting[0]
    spells = first.get("spells", {})
    assert isinstance(spells, dict), f"Abjurer spellcasting 'spells' should be a dict, got {type(spells)}"

    # Should have at least one clean frequency key
    has_clean_key = any(k in spells for k in ["at_will", "daily_1", "daily_2", "level_3"])
    assert has_clean_key, "Abjurer spellcasting does not appear to have clean frequency keys"
