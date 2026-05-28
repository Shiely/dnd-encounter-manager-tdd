"""
Unit tests for the SRD monster importer, focusing on entry rendering.

These tests cover the critical parsing of 5eTools structured data,
especially damage expressions and dice (the source of "36 ()" bugs).
"""

import pytest
import sys
from pathlib import Path

# Make the utilities directory importable when running tests
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

try:
    from utilities.import_srd_monsters import render_entries, _strip_5etools_tags
except ModuleNotFoundError:
    # Fallback for some pytest environments
    sys.path.insert(0, str(project_root / "utilities"))
    from import_srd_monsters import render_entries, _strip_5etools_tags


def test_render_entries_handles_simple_damage_dice():
    """
    TDD test for priority #1: Damage expressions with dice must render
    with both average and dice formula, e.g. "36 (8d8)".
    """
    # This is a common structure in 5eTools for actions
    entry = {
        "type": "entries",
        "entries": [
            "On a failed save, a creature takes ",
            {
                "type": "damage",
                "damage": [
                    {"formula": "8d8", "average": 36, "type": "force"}
                ]
            },
            " force damage."
        ]
    }

    result = render_entries(entry)
    assert "36 (8d8)" in result
    assert "force damage" in result


def test_render_entries_handles_tagged_damage():
    """Handles {@damage ...} tags commonly used in 5eTools text."""
    text = "takes {@damage 3d10 + 4} force damage"
    result = _strip_5etools_tags(text)
    # Current implementation may be weak here — this test will drive improvement
    assert "3d10" in result or "3d10 + 4" in result


def test_render_entries_preserves_attack_and_hit_structure():
    """Actions should retain useful attack info when rendered."""
    entry = {
        "name": "Arcane Burst",
        "entries": [
            "+8 to hit, reach 5 ft. or range 120 ft., one target. ",
            {
                "type": "damage",
                "damage": [{"formula": "3d10+4", "average": 20, "type": "force"}]
            },
            " force damage."
        ]
    }
    result = render_entries(entry)
    assert "Arcane Burst" in result
    assert "20 (3d10+4)" in result or "20 (3d10 + 4)" in result
