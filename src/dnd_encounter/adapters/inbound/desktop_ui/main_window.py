# adapters/inbound/desktop_ui/main_window.py
"""
New MainWindow (adapters layer).

Thin orchestrator that composes the new UI widgets and drives them
via EncounterSignals + EncounterStateDTO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QShortcut
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .add_monster_dialog import AddMonsterDialog
from .add_player_dialog import AddPlayerDialog
from .condition_panel import ConditionPanel
from .encounter_signals import EncounterSignals
from .sidebar_widget import SidebarWidget
from .stat_block_panel import StatBlockPanel

if TYPE_CHECKING:
    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO
    from dnd_encounter.application.services.encounter_service import EncounterService


class MainWindow(QMainWindow):
    """New architecture-compliant MainWindow."""

    def __init__(
        self,
        service: EncounterService,
        signals: EncounterSignals | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._signals = signals or EncounterSignals()
        self._current_instance_id: str | None = None

        self.setWindowTitle("D&D Encounter Manager")
        self.setGeometry(100, 100, 1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Sidebar (left)
        self.sidebar = SidebarWidget()
        layout.addWidget(self.sidebar, 1)

        # Right side: Stat block + Condition button
        right_layout = QVBoxLayout()
        self.stat_panel = StatBlockPanel()
        right_layout.addWidget(self.stat_panel)

        self.btn_conditions = QPushButton("Conditions")
        self.btn_conditions.clicked.connect(self._show_conditions)
        right_layout.addWidget(self.btn_conditions)

        layout.addLayout(right_layout, 2)

        # Wire signals
        self.sidebar.entity_selected.connect(self._on_entity_selected)
        self._signals.state_changed.connect(self._on_state_changed)
        self.stat_panel.hp_adjusted.connect(self._on_hp_adjusted)
        self.stat_panel.hp_set.connect(self._on_hp_set)
        self._signals.error_occurred.connect(self._on_error_occurred)  # Priority 5

        # New discoverable action buttons + context menu from Sidebar
        self.sidebar.add_monster_requested.connect(self._on_add_monster)
        self.sidebar.add_player_requested.connect(self._on_add_player)
        self.sidebar.remove_requested.connect(self._on_remove_selected)
        self.sidebar.rename_requested.connect(self._on_rename_requested)
        self.sidebar.edit_initiative_requested.connect(self._on_edit_initiative_requested)
        self.sidebar.conditions_requested.connect(self._on_conditions_requested)
        self.sidebar.hp_adjust_requested.connect(self._on_hp_adjusted)

        # Basic top menu (minimal for now)
        self._create_menu_bar()

        # Additional keyboard shortcuts
        QShortcut("Backspace", self, activated=self._on_remove_selected)
        QShortcut("Delete", self, activated=self._on_remove_selected)
        QShortcut(Qt.CTRL | Qt.Key_K, self, activated=self._show_conditions)

        # Global HP hotkeys (Priority 7)
        QShortcut(Qt.Key_Plus, self, activated=self._on_global_hp_plus)
        QShortcut(Qt.Key_Minus, self, activated=self._on_global_hp_minus)

        # More hotkeys for coverage
        QShortcut("Ctrl+M", self, activated=self._on_add_monster)
        QShortcut("Ctrl+P", self, activated=self._on_add_player)

        # Initial load
        self._refresh_state()

    def _refresh_state(self) -> None:
        try:
            state = self._service.get_state()
            self._signals.state_changed.emit(state)
            if hasattr(self, 'undo_action'):
                can = self._service.can_undo()
                if isinstance(can, bool):
                    self.undo_action.setEnabled(can)
            self.statusBar().clearMessage()  # clear previous errors on refresh
        except Exception:
            # Fallback for early migration phase
            pass

    def _on_state_changed(self, state: EncounterStateDTO) -> None:
        self.sidebar.refresh(state)
        if self._current_instance_id:
            self.stat_panel.refresh(state, self._current_instance_id)
        self._update_conditions_button()
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self._service.can_undo())

    def _on_entity_selected(self, instance_id: str) -> None:
        try:
            state = self._service.get_state()
            self.stat_panel.refresh(state, instance_id)
            self._current_instance_id = instance_id
            self._update_conditions_button()
        except Exception:
            pass

    def _create_menu_bar(self) -> None:
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Add Monster", self._on_add_monster)
        file_menu.addAction("Add Player", self._on_add_player)
        file_menu.addSeparator()

        advance_action = file_menu.addAction("Advance Turn", self._on_advance_turn)
        advance_action.setShortcut("Space")

        remove_action = file_menu.addAction("Remove Selected", self._on_remove_selected)
        remove_action.setShortcut("Delete")

        file_menu.addSeparator()
        self.undo_action = file_menu.addAction("Undo", self._on_undo)
        self.undo_action.setShortcut("Ctrl+Z")

    def _on_add_monster(self):
        dialog = AddMonsterDialog(self._service, self)
        if dialog.exec():
            monster_id = dialog.get_selected_monster_id()
            if monster_id:
                try:
                    self._service.add_monster(monster_id)
                    self._refresh_state()
                    # Auto-select the newly added entity so Remove/HP/etc. work immediately
                    state = self._service.get_state()
                    if state.entities:
                        self._on_entity_selected(state.entities[-1].instance_id)
                except Exception as e:
                    print(f"[UI] Failed to add monster: {e}")
                    self._refresh_state()

    def _on_add_player(self):
        dialog = AddPlayerDialog(self)
        if dialog.exec():
            data = dialog.get_player_data()
            if data:
                name, initiative, max_hp = data
                try:
                    self._service.add_player(name, initiative, max_hp)
                    self._refresh_state()
                    # Auto-select the newly added entity
                    state = self._service.get_state()
                    if state.entities:
                        self._on_entity_selected(state.entities[-1].instance_id)
                except Exception as e:
                    print(f"[UI] Failed to add player: {e}")  # Helps debugging
                    # Still refresh in case partial state changed
                    self._refresh_state()

    def _on_advance_turn(self):
        self._service.advance_turn()
        self._refresh_state()

        # After advancing, try to select/highlight the new current turn actor (Priority #2)
        try:
            state = self._service.get_state()
            for e in getattr(state, "entities", []):
                if getattr(e, "is_current_turn", False):
                    self._on_entity_selected(e.instance_id)
                    break
        except Exception:
            pass  # non-fatal

    def _on_remove_selected(self):
        # Prefer the tracked ID, fall back to whatever the sidebar currently shows as selected
        instance_id = self._current_instance_id or self.sidebar.get_selected_instance_id()
        if instance_id:
            self._service.remove_entity(instance_id)
            self._current_instance_id = None
            self._refresh_state()

    def _show_conditions(self):
        """Open ConditionPanel pre-filled for the current/selected entity (Priority 3)."""
        instance_id = self._current_instance_id or self.sidebar.get_selected_instance_id()

        # Fallback to current turn actor if nothing explicitly selected
        if not instance_id:
            try:
                state = self._service.get_state()
                for e in getattr(state, "entities", []):
                    if getattr(e, "is_current_turn", False):
                        instance_id = e.instance_id
                        break
            except Exception:
                pass

        if not instance_id:
            return

        # Find the full entity data to pass to the panel
        state = self._service.get_state()
        current_entity = None
        for e in getattr(state, "entities", []):
            if getattr(e, "instance_id", None) == instance_id:
                current_entity = e
                break

        panel = ConditionPanel(self)
        panel.condition_toggled.connect(self._on_condition_toggled)
        panel.refresh(current_entity)
        panel.exec()

        # Refresh after dialog closes in case conditions were changed
        self._refresh_state()

    def _on_condition_toggled(self, instance_id: str, condition: str, checked: bool):
        try:
            self._service.toggle_condition(instance_id, condition)
            self._refresh_state()
        except Exception as e:
            print(f"[UI] Toggle condition error: {e}")

    def _on_hp_adjusted(self, instance_id: str, delta: int) -> None:
        """Handle +/- HP button presses from StatBlockPanel (Priority #1)."""
        try:
            state = self._service.get_state()
            for entity in getattr(state, "entities", []):
                if getattr(entity, "instance_id", None) == instance_id:
                    current = getattr(entity, "current_hp", 0) or 0
                    new_hp = max(0, current + delta)
                    self._service.edit_hp(instance_id, new_hp)
                    self._refresh_state()
                    # Re-select the same entity so the panel stays open
                    self._on_entity_selected(instance_id)
                    break
        except Exception as e:
            print(f"[UI] HP adjust error: {e}")

    def _update_conditions_button(self) -> None:
        """Update the Conditions button text to show the current entity (Priority 3 increment)."""
        instance_id = self._current_instance_id or self.sidebar.get_selected_instance_id()

        if not instance_id:
            self.btn_conditions.setText("Conditions")
            return

        # Try to find the display name
        try:
            state = self._service.get_state()
            for e in getattr(state, "entities", []):
                if getattr(e, "instance_id", None) == instance_id:
                    name = getattr(e, "display_name", instance_id)
                    self.btn_conditions.setText(f"Conditions ({name})")
                    return
        except Exception:
            pass

        self.btn_conditions.setText("Conditions")

    def _on_rename_requested(self, instance_id: str) -> None:
        """Handle Rename from context menu."""
        state = self._service.get_state()
        current_name = ""
        for e in state.entities:
            if e.instance_id == instance_id:
                current_name = e.display_name
                break

        new_name, ok = QInputDialog.getText(self, "Rename Entity", "New name:", text=current_name)
        if ok and new_name.strip():
            self._service.rename_entity(instance_id, new_name.strip())
            self._refresh_state()

    def _on_edit_initiative_requested(self, instance_id: str) -> None:
        """Handle Edit Initiative from context menu."""
        state = self._service.get_state()
        current_init = 0
        for e in state.entities:
            if e.instance_id == instance_id:
                current_init = e.initiative
                break

        new_init, ok = QInputDialog.getInt(self, "Edit Initiative", "New initiative:", value=current_init, min=0, max=50)
        if ok:
            self._service.change_initiative(instance_id, new_init)
            self._refresh_state()

    def _on_conditions_requested(self, instance_id: str) -> None:
        """Open conditions from context menu."""
        self._current_instance_id = instance_id
        self._show_conditions()

    def _on_undo(self) -> None:
        """Handle Undo from menu or Ctrl+Z."""
        if self._service.can_undo():
            self._service.undo()
            self._refresh_state()

    def _on_global_hp_plus(self):
        if self._current_instance_id:
            self._on_hp_adjusted(self._current_instance_id, +1)

    def _on_global_hp_minus(self):
        if self._current_instance_id:
            self._on_hp_adjusted(self._current_instance_id, -1)

    def _on_hp_set(self, instance_id: str, new_hp: int) -> None:
        """Handle absolute HP set from StatBlockPanel direct input."""
        try:
            self._service.edit_hp(instance_id, max(0, new_hp))
            self._refresh_state()
            self._on_entity_selected(instance_id)
        except Exception as e:
            print(f"[UI] HP set error: {e}")

    def _on_error_occurred(self, message: str):
        """Basic error feedback (Priority 5)."""
        self.statusBar().showMessage(f"Error: {message}", 5000)
