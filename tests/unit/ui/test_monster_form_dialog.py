"""
Tests for MonsterFormDialog (Custom Monster creation form).

These tests focus on the data collection and MonsterDefinition construction logic.
"""

import pytest
from PySide6.QtWidgets import QDialog

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from dnd_encounter.adapters.inbound.desktop_ui.monster_form_dialog import MonsterFormDialog
from dnd_encounter.domain.entities.monster_definition import MonsterDefinition


@pytest.fixture
def form_dialog(qtbot):
    """Create a MonsterFormDialog for testing."""
    dialog = MonsterFormDialog(repo=None, parent=None)
    qtbot.addWidget(dialog)
    return dialog


def test_basic_monster_creation(form_dialog, qtbot):
    """Test creating a minimal valid custom monster (only required fields)."""
    form_dialog.name_edit.setText("Test Goblin")
    form_dialog.hp_spin.setValue(7)

    # Simulate clicking save
    qtbot.mouseClick(form_dialog.btn_save, Qt.LeftButton)

    assert form_dialog.result() == QDialog.Accepted
    monster = form_dialog.get_created_monster()
    assert monster is not None
    assert monster.name == "Test Goblin"
    assert monster.hit_points == 7
    assert monster.size == "Medium"  # default


def test_collect_feature_list(form_dialog):
    """Test that feature rows (traits, actions, etc.) are collected correctly."""
    # Manually add a trait row
    form_dialog._add_feature_row("traits", name="Pack Tactics", description="Advantage when ally is nearby")

    traits = form_dialog._collect_feature_list("traits")
    assert len(traits) == 1
    assert traits[0]["name"] == "Pack Tactics"
    assert "Advantage" in traits[0]["description"]


def test_rich_custom_monster(form_dialog, qtbot):
    """Test that a monster with many optional fields is built correctly."""
    form_dialog.name_edit.setText("Custom Dragon")
    form_dialog.hp_spin.setValue(120)
    form_dialog.ac_spin.setValue(18)
    form_dialog.cr_edit.setText("8")

    # Add a trait and an action
    form_dialog._add_feature_row("traits", "Legendary Resistance", "Re-roll a failed save 3/day")
    form_dialog._add_feature_row("actions", "Fire Breath", "Recharge 5-6, 60 ft cone, Dex save")

    qtbot.mouseClick(form_dialog.btn_save, Qt.LeftButton)

    monster: MonsterDefinition = form_dialog.get_created_monster()
    assert monster is not None
    assert monster.name == "Custom Dragon"
    assert monster.hit_points == 120
    assert len(monster.traits) == 1
    assert len(monster.actions) == 1
    assert monster.traits[0]["name"] == "Legendary Resistance"
    assert "Fire Breath" in monster.actions[0]["name"]