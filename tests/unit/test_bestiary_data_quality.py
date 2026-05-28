"""
Basic smoke tests for the committed bestiary data quality.

These tests exist to catch regressions in the generated monsters.json
and to ensure that the data we ship to users/clones is reasonably clean.

They are intentionally lightweight and do not replace proper importer tests.
"""
import json
import pytest
from pathlib import Path


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
    assert len(problems) < 50, f"Too many raw tags found:\n" + "\n".join(problems[:20])


def test_no_xphb_leaking_in_display_text(bestiary):
    """
    XPHB is the 2024 PHB source code. It should not appear raw in
    descriptions or spell lists that users see.
    """
    problems = []
    for monster in bestiary:
        name = monster.get("name", "Unknown")
        # Check spellcasting and action descriptions
        for field in ["spellcasting", "actions", "traits"]:
            val = monster.get(field)
            if val:
                text = json.dumps(val)
                if "XPHB" in text:
                    problems.append(name)
                    break

    # For now we allow some, but this should be driven toward zero
    # by improving the importer + renderer stripping.
    assert len(problems) < 100, f"XPHB leaking in too many monsters: {problems[:10]}"


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
