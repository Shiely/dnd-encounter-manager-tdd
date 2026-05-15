# tests/unit/domain/test_hp_rules.py
# DOMAIN LAYER TEST - No external imports allowed

from src.dnd_encounter.domain.rules.hp_rules import apply_hp_edit, is_auto_remove


def test_apply_hp_edit_normal():
    assert apply_hp_edit(7, 3) == 3


def test_apply_hp_edit_zero():
    assert apply_hp_edit(7, 0) == 0


def test_apply_hp_edit_negative():
    assert apply_hp_edit(7, -2) == 0


def test_apply_hp_edit_temporary_hp():
    assert apply_hp_edit(7, 10) == 10  # temp HP allowed, no upper clamp


def test_is_auto_remove_zero():
    assert is_auto_remove(0) is True


def test_is_auto_remove_negative():
    assert is_auto_remove(-1) is True


def test_is_auto_remove_positive():
    assert is_auto_remove(1) is False
