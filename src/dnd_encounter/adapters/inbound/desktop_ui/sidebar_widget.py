from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListView,
    QSizePolicy,
)

try:
    from .initiative_list_model import InitiativeListModel
    from dnd_encounter.application.dtos import EncounterStateDTO
except ImportError:
    from initiative_list_model import InitiativeListModel
    from dataclasses import dataclass
    from typing import Any

    @dataclass
    class EncounterStateDTO:
        entities: list[Any]
        current_turn_index: int = 0
        round_number: int = 1
        error: str | None = None


class SidebarWidget(QWidget):
    """Left sidebar showing the initiative order as a QListView.

    Uses custom InitiativeListModel for rendering and current-turn highlighting.
    Emits entity_selected when user clicks a row.
    Provides refresh() for MainWindow to call on state changes.
    """

    entity_selected = Signal(str)  # instance_id of selected entity

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QLabel("Initiative Order")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self._model = InitiativeListModel(self)
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setAlternatingRowColors(True)
        self._list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self._list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self._list_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Connect selection
        sel_model = self._list_view.selectionModel()
        if sel_model:
            sel_model.selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self._list_view)

        # Optional status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._status_label)

    @Slot()
    def refresh(self, state: EncounterStateDTO | None = None) -> None:
        """Update the initiative list from current EncounterStateDTO.

        Called by MainWindow on state_changed signal.
        """
        if state is None:
            self._status_label.setText("No encounter loaded")
            self._model.update_from_state(
                type("obj", (object,), {"entities": [], "current_turn_index": -1})()  # type: ignore
            )
            return

        self._model.update_from_state(state)
        n = len(state.entities)
        self._status_label.setText(f"{n} active entities | Round {getattr(state, 'round_number', 1)}")

    def _on_selection_changed(self, selected, deselected) -> None:
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            instance_id = self._model.get_instance_id(row)
            if instance_id:
                self.entity_selected.emit(instance_id)

    def clear_selection(self) -> None:
        self._list_view.clearSelection()

    def select_entity(self, instance_id: str) -> None:
        """Programmatically select by instance_id (for future use)."""
        for row in range(self._model.rowCount()):
            if self._model.get_instance_id(row) == instance_id:
                self._list_view.setCurrentIndex(self._model.index(row, 0))
                break
