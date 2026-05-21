# adapters/inbound/desktop_ui/main_window.py
"""
New MainWindow (adapters layer).

Thin orchestrator that composes the new UI widgets and drives them
via EncounterSignals + EncounterStateDTO.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

        # Basic top menu (minimal for now)
        self._create_menu_bar()

        # Initial load
        self._refresh_state()

    def _refresh_state(self) -> None:
        try:
            state = self._service.get_state()
            self._signals.state_changed.emit(state)
        except Exception:
            # Fallback for early migration phase
            pass

    def _on_state_changed(self, state: EncounterStateDTO) -> None:
        self.sidebar.refresh(state)
        if self._current_instance_id:
            self.stat_panel.refresh(state, self._current_instance_id)

    def _on_entity_selected(self, instance_id: str) -> None:
        try:
            state = self._service.get_state()
            self.stat_panel.refresh(state, instance_id)
            self._current_instance_id = instance_id
        except Exception:
            pass

    def _create_menu_bar(self) -> None:
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Add Monster", self._on_add_monster)
        file_menu.addAction("Add Player", self._on_add_player)
        file_menu.addSeparator()
        file_menu.addAction("Advance Turn", self._on_advance_turn)
        file_menu.addAction("Remove Selected", self._on_remove_selected)

    def _on_add_monster(self):
        dialog = AddMonsterDialog(self._service, self)
        if dialog.exec():
            monster_id = dialog.get_selected_monster_id()
            if monster_id:
                self._service.add_monster(monster_id)
                self._refresh_state()

    def _on_add_player(self):
        dialog = AddPlayerDialog(self)
        if dialog.exec():
            data = dialog.get_player_data()
            if data:
                name, initiative, max_hp = data
                self._service.add_player(name, initiative, max_hp)
                self._refresh_state()

    def _on_advance_turn(self):
        self._service.advance_turn()
        self._refresh_state()

    def _on_remove_selected(self):
        if self._current_instance_id:
            self._service.remove_entity(self._current_instance_id)
            self._current_instance_id = None
            self._refresh_state()

    def _show_conditions(self):
        if not hasattr(self, "_current_instance_id") or not self._current_instance_id:
            return
        panel = ConditionPanel(self)
        panel.condition_toggled.connect(self._on_condition_toggled)
        panel.exec()

    def _on_condition_toggled(self, instance_id: str, condition: str, checked: bool):
        try:
            self._service.toggle_condition(instance_id, condition)
            self._refresh_state()
        except Exception as e:
            print(f"[UI] Toggle condition error: {e}")
