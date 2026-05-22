from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QMenu,
    QPushButton,
    QSizePolicy,
)

from .initiative_list_model import InitiativeListModel, EncounterStateDTO


class SidebarWidget(QWidget):
    """Sidebar showing live initiative order (QListView + custom model).

    Emits entity_selected(instance_id) on click.
    MainWindow calls refresh(state) on EncounterSignals.state_changed.
    """

    entity_selected = Signal(str)

    # New action signals for discoverability (small buttons + context menu)
    add_monster_requested = Signal()
    add_player_requested = Signal()
    remove_requested = Signal()
    rename_requested = Signal(str)          # instance_id
    edit_initiative_requested = Signal(str) # instance_id
    conditions_requested = Signal(str)      # instance_id for quick conditions from menu
    hp_adjust_requested = Signal(str, int)  # instance_id, delta for quick HP from menu

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

        # Compact action buttons (small, near the list, logical location)
        button_bar = QHBoxLayout()
        button_bar.setSpacing(4)
        button_bar.setContentsMargins(0, 0, 0, 2)

        self.btn_add_monster = QPushButton("+M")
        self.btn_add_player = QPushButton("+P")
        self.btn_remove = QPushButton("Remove")

        for btn in (self.btn_add_monster, self.btn_add_player, self.btn_remove):
            btn.setMaximumHeight(22)
            btn.setMinimumWidth(40)
            btn.setStyleSheet("font-size: 11px;")

        self.btn_add_monster.clicked.connect(self.add_monster_requested.emit)
        self.btn_add_player.clicked.connect(self.add_player_requested.emit)
        self.btn_remove.clicked.connect(self.remove_requested.emit)

        button_bar.addWidget(self.btn_add_monster)
        button_bar.addWidget(self.btn_add_player)
        button_bar.addStretch()
        button_bar.addWidget(self.btn_remove)

        layout.addLayout(button_bar)

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

        # Right-click context menu support
        self._list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_view.customContextMenuRequested.connect(self._show_context_menu)

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

        # Find current turn actor for clear visualization (Priority #2)
        current_name = None
        for e in getattr(state, "entities", []):
            if getattr(e, "is_current_turn", False):
                current_name = getattr(e, "display_name", None)
                break

        if current_name:
            self._status_label.setText(f"{n} entities | Round {rnd} — Now Acting: {current_name}")
            self._status_label.setStyleSheet("color: #2a7; font-size: 11px; font-weight: bold;")
        else:
            self._status_label.setText(f"{n} entities | Round {rnd}")
            self._status_label.setStyleSheet("color: #666; font-size: 11px;")

    def _on_selection_changed(self, selected, deselected) -> None:
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            iid = self._model.get_instance_id(row)
            if iid:
                self.entity_selected.emit(iid)

    def clear_selection(self) -> None:
        self._list_view.clearSelection()

    def get_selected_instance_id(self) -> str | None:
        """Return the instance_id of the currently selected row, if any."""
        indexes = self._list_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            return self._model.get_instance_id(row)
        return None

    def _show_context_menu(self, pos) -> None:
        """Show right-click context menu on the initiative list."""
        index = self._list_view.indexAt(pos)
        if not index.isValid():
            return

        instance_id = self._model.get_instance_id(index.row())
        if not instance_id:
            return

        # Select the clicked row so that MainWindow's _current_instance_id gets updated
        self._list_view.setCurrentIndex(index)

        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        rename_action = menu.addAction("Rename...")
        edit_init_action = menu.addAction("Edit Initiative...")
        conditions_action = menu.addAction("Conditions...")
        hp_plus_action = menu.addAction("+1 HP")
        hp_minus_action = menu.addAction("-1 HP")

        action = menu.exec(self._list_view.viewport().mapToGlobal(pos))

        if action == remove_action:
            self.remove_requested.emit()
        elif action == rename_action:
            self.rename_requested.emit(instance_id)
        elif action == edit_init_action:
            self.edit_initiative_requested.emit(instance_id)
        elif action == conditions_action:
            self.conditions_requested.emit(instance_id)
        elif action == hp_plus_action:
            self.hp_adjust_requested.emit(instance_id, 1)
        elif action == hp_minus_action:
            self.hp_adjust_requested.emit(instance_id, -1)
