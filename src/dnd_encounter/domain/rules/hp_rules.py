# DOMAIN LAYER: stdlib imports only.


def apply_hp_edit(current_hp: int, new_value: int) -> int:
    """Return clamped HP. Floor is 0. No upper clamp (temporary HP allowed).
    Invariant: only called from EditHpCommand.execute() and EditHpCommand.undo().
    """
    return max(0, new_value)


def is_auto_remove(hp: int) -> bool:
    """Return True when a monster entity should be auto-removed."""
    return hp <= 0
