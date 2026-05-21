from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListView,
    QSizePolicy,
)

from .initiative_list_model import InitiativeListModel, EncounterStateDTO


class SidebarWidget(QWidget):
    """Sidebar showing live initiative order (QListView + custom model).

    Emits entity_selected(instance_id) on click.
    MainWindow calls refresh(state) on EncounterSignals.state_changed.
    """

    entity_selected = Signal(str)

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

        sel_model = self._list_view.selectionModel()
        if sel_model is not None:
            sel_model.selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self._list_view)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._status_label)

    @Slot()
    def refresh(self, state: EncounterStateDTO | None = None) -> None:
        if state is None:
            self._status_label.setText("No encounter loaded")
            return
        self._model.update_from_state(state)
        n = len(getattr(state, "entities", []))
        rnd = getattr(state, "round_number", 1)
        self._status_label.setText(f"{n} entities | Round {rnd}")

    def _on_selection_changed(self, selected, deselected) -> None:
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            iid = self._model.get_instance_id(row)
            if iid:
                self.entity_selected.emit(iid)

    def clear_selection(self) -> None:
        self._list_view.clearSelection()
