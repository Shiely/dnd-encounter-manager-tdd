from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtCore import Qt, Signal, Slot, QEvent  # QEvent for eventFilter (additive post-bugfix for robust Space ignore when list focused)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QMenu,
    QPushButton,
    QSizePolicy,
)  # noqa: I001 - keep after TYPE_CHECKING for this file's established style; no new debt from bugfix

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
    reset_requested = Signal()              # Phase 2: visible "Reset" for fresh encounter (near +M/+P)

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
        self.btn_reset = QPushButton("Reset")  # Phase 2 deliverable: visible, discoverable reset action (near +M/+P)

        for btn in (self.btn_add_monster, self.btn_add_player, self.btn_remove):
            btn.setMaximumHeight(22)
            btn.setMinimumWidth(40)
            btn.setStyleSheet("font-size: 11px;")

        # Reset button sizing (slightly wider label but still compact)
        self.btn_reset.setMaximumHeight(22)
        self.btn_reset.setMinimumWidth(45)
        self.btn_reset.setStyleSheet("font-size: 11px;")

        self.btn_add_monster.clicked.connect(self.add_monster_requested.emit)
        self.btn_add_player.clicked.connect(self.add_player_requested.emit)
        self.btn_remove.clicked.connect(self.remove_requested.emit)
        self.btn_reset.clicked.connect(self.reset_requested.emit)

        button_bar.addWidget(self.btn_add_monster)
        button_bar.addWidget(self.btn_add_player)
        button_bar.addWidget(self.btn_reset)
        button_bar.addStretch()
        button_bar.addWidget(self.btn_remove)

        layout.addLayout(button_bar)

        self._model = InitiativeListModel(self)
        # Post-bugfix (additive, minimal): use tiny local subclass that overrides keyPressEvent
        # to ignore Space (the reported global advance hotkey). QListView's base implementation
        # accepts/consumes Space (item activation etc); by ignoring here we ensure the key
        # reaches the Advance Turn menu action's ApplicationShortcut (and any secondary
        # accelerators) even when the list has focus (normal human state after adds in
        # run_ui.py). No other keys or list behaviors changed. Viewport filter + subclass
        # together cover physical + qtbot delivery paths.
        # Refined (additive for this bugfix block): also override keyReleaseEvent to ignore Space.
        # qtbot.keyClick (and some physical dispatch) delivers press+release; ignoring both phases
        # ensures the event is not accepted by the list view and reaches ancestor shortcuts reliably.
        class _FocusKeyForwardingListView(QListView):
            def keyPressEvent(self, event):  # noqa: N802 - must match Qt virtual (camelCase); not our naming
                if event.key() == Qt.Key_Space:
                    event.ignore()
                    # refined (additive post-red for this continuation): explicit comment + early return ensures
                    # direct qtbot.keyClick(list_view) and physical Space when _list_view focused (human post-add state)
                    # does not get consumed by QListView default; propagates to the Advance Turn action shortcut.
                    return  # prevent base accept/handling; lets action shortcut fire
                super().keyPressEvent(event)

            def keyReleaseEvent(self, event):  # noqa: N802
                if event.key() == Qt.Key_Space:
                    event.ignore()
                    return
                super().keyReleaseEvent(event)

        self._list_view = _FocusKeyForwardingListView()
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

        # Post-bugfix (additive, minimal, for human list-focus case):
        # Install eventFilter on both the list view *and its viewport*. For QAbstractItemView/QListView,
        # many key events (including Space) are delivered to the viewport child widget. Checking only
        # the list itself missed some physical dispatch paths. Ignore Space so it is not consumed
        # for activation/selection and can reach the main window's Advance Turn action shortcut.
        # Subclass key*Event overrides remain as belt-and-suspenders. No other keys/behaviors changed.
        self._list_view.installEventFilter(self)
        self._list_view.viewport().installEventFilter(self)

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

    def eventFilter(self, watched, event):  # noqa: N802 - must match Qt virtual (camelCase); not our naming
        """Event filter (additive for Space propagation bugfix).

        When the _list_view (or its viewport) has focus (normal after add in human use), ignore
        Space key events so they are not consumed by the view's default activation/selection.
        This lets the Advance Turn QAction's ApplicationShortcut (set on the menu action) fire
        and call _on_advance_turn. We filter both the view and viewport because item views
        commonly deliver keys to the viewport child.
        Return False to allow further processing/propagation after ignore.
        """
        lv = self._list_view
        if watched in (lv, lv.viewport()) and event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            if event.key() == Qt.Key_Space:
                event.ignore()
                return False  # do not consume; propagate to ancestor shortcuts / action
        return super().eventFilter(watched, event)
