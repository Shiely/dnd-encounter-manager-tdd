# adapters/inbound/desktop_ui/encounter_signals.py
"""
Central Qt signals for the desktop UI layer.

This class acts as the reactive bridge between the application layer
and the UI widgets, as described in Part 4.
"""

from PySide6.QtCore import QObject, Signal

from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO


class EncounterSignals(QObject):
    """
    Qt signals used to drive UI updates reactively.

    Widgets should connect to these signals instead of being manually refreshed.
    """

    # Emitted whenever the encounter state changes (after commands, load, etc.)
    state_changed = Signal(EncounterStateDTO)

    # Emitted when a specific entity is selected (e.g. from sidebar)
    entity_selected = Signal(str)  # instance_id

    # Optional: error notifications
    error_occurred = Signal(str)
