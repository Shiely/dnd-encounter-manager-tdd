# ui/main_window.py
# Thin UI layer - only calls EncounterService and reacts to events


try:
    import PySide6.QtWidgets  # noqa: F401

    HAS_QT = True
except ImportError:
    HAS_QT = False


from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QSpinBox,
    QGroupBox,
    QFormLayout,
    QMenu,
    QInputDialog,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QKeyEvent

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.adapters.outbound.event_publisher import EventPublisher
from dnd_encounter.ui.add_monster_dialog import AddMonsterDialog
from dnd_encounter.ui.add_player_dialog import AddPlayerDialog


class MainWindow(QMainWindow):
    def __init__(self, service: EncounterService, publisher: EventPublisher | None = None) -> None:
        super().__init__()
        self.service = service
        self.publisher = publisher
        self.setWindowTitle("D&D Encounter Manager")
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        sidebar = self._create_sidebar()
        layout.addWidget(sidebar, 1)

        stat_panel = self._create_stat_panel()
        layout.addWidget(stat_panel, 2)

        # Subscribe to events for reactive updates
        if self.publisher:
            self.publisher.event_fired.connect(self._on_event)

        self.refresh()

    def _on_event(self, event_type: str, payload: dict):
        """React to domain events by refreshing the UI."""
        if event_type in ("hp_changed", "entity_auto_removed", "entity_removed"):
            self.refresh()

    def _create_sidebar(self) -> QWidget:
        group = QGroupBox("Initiative Order")
        layout = QVBoxLayout(group)

        self.entity_list = QListWidget()
        self.entity_list.currentRowChanged.connect(self._on_entity_selected)
        self.entity_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.entity_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.entity_list)

        btn_layout = QHBoxLayout()
        self.btn_add_monster = QPushButton("Add Monster")
        self.btn_add_monster.clicked.connect(self._on_add_monster)
        self.btn_add_player = QPushButton("Add Player")
        self.btn_add_player.clicked.connect(self._on_add_player)
        self.btn_advance = QPushButton("Advance Turn")
        self.btn_advance.clicked.connect(self._on_advance_turn)
        btn_layout.addWidget(self.btn_add_monster)
        btn_layout.addWidget(self.btn_add_player)
        btn_layout.addWidget(self.btn_advance)
        layout.addLayout(btn_layout)

        self.lbl_round = QLabel("Round: 1")
        layout.addWidget(self.lbl_round)

        return group

    def _create_stat_panel(self) -> QWidget:
        group = QGroupBox("Selected Entity")
        layout = QFormLayout(group)

        self.lbl_name = QLabel("-")
        self.lbl_hp = QLabel("-")
        self.lbl_initiative = QLabel("-")
        self.lbl_conditions = QLabel("-")

        layout.addRow("Name:", self.lbl_name)
        layout.addRow("HP:", self.lbl_hp)
        layout.addRow("Initiative:", self.lbl_initiative)
        layout.addRow("Conditions:", self.lbl_conditions)

        self.spin_hp = QSpinBox()
        self.spin_hp.setRange(0, 999)
        self.btn_edit_hp = QPushButton("Set HP")
        self.btn_edit_hp.clicked.connect(self._on_edit_hp)

        layout.addRow(self.spin_hp, self.btn_edit_hp)

        return group

    def refresh(self):
        # Build directly from live in-memory encounter
        self.entity_list.clear()
        for entity in self.service.encounter.entities:
            hp_display = entity.current_hp if entity.current_hp is not None else "-"
            text = f"{entity.display_name} (Init: {entity.initiative}, HP: {hp_display})"
            self.entity_list.addItem(text)

        self.lbl_round.setText(f"Round: {self.service.encounter.round_number}")

    def _on_entity_selected(self, row: int):
        if row < 0:
            return
        if row < len(self.service.encounter.entities):
            e = self.service.encounter.entities[row]
            self.lbl_name.setText(e.display_name)
            hp_display = f"{e.current_hp} / {e.max_hp}" if e.current_hp is not None else "- / -"
            self.lbl_hp.setText(hp_display)
            self.lbl_initiative.setText(str(e.initiative))
            # Handle both Condition objects and plain strings (for test compatibility)
            if e.conditions:
                if hasattr(e.conditions[0], "value"):
                    conditions_text = ", ".join([c.value for c in e.conditions])
                else:
                    conditions_text = ", ".join(e.conditions)
            else:
                conditions_text = "None"
            self.lbl_conditions.setText(conditions_text)
            self.spin_hp.setValue(e.current_hp or 0)

    def _on_add_monster(self):
        dialog = AddMonsterDialog(self.service, self)
        if dialog.exec():
            monster_id = dialog.get_selected_monster_id()
            if monster_id:
                self.service.add_monster(monster_id)
                self.refresh()

    def _on_add_player(self):
        dialog = AddPlayerDialog(self)
        if dialog.exec():
            data = dialog.get_player_data()
            if data:
                name, initiative, max_hp = data
                self.service.add_player(name, initiative, max_hp)
                self.refresh()

    def _on_edit_hp(self):
        if not self.entity_list.currentItem():
            return
        row = self.entity_list.currentRow()
        if row < len(self.service.encounter.entities):
            entity = self.service.encounter.entities[row]
            new_hp = self.spin_hp.value()
            self.service.edit_hp(entity.instance_id, new_hp)
            self.refresh()
            if row < self.entity_list.count():
                self.entity_list.setCurrentRow(row)
                hp_display = f"{new_hp} / {entity.max_hp}" if new_hp is not None else "- / -"
                self.lbl_hp.setText(hp_display)
                self.spin_hp.setValue(new_hp)

    def _on_advance_turn(self):
        self.service.advance_turn()
        self.refresh()

    def _show_context_menu(self, position: QPoint):
        item = self.entity_list.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        row = self.entity_list.row(item)
        if row < len(self.service.encounter.entities):
            entity = self.service.encounter.entities[row]

            remove_action = menu.addAction("Remove Entity")
            remove_action.triggered.connect(lambda: self._remove_entity(entity.instance_id))

            rename_action = menu.addAction("Rename Entity")
            rename_action.triggered.connect(lambda: self._rename_entity(entity.instance_id))

            edit_init_action = menu.addAction("Edit Initiative")
            edit_init_action.triggered.connect(lambda: self._edit_initiative(entity.instance_id))

            menu.exec(self.entity_list.mapToGlobal(position))

    def _remove_entity(self, instance_id: str):
        self.service.remove_entity(instance_id)
        self.refresh()

    def _rename_entity(self, instance_id: str):
        new_name, ok = QInputDialog.getText(self, "Rename Entity", "New name:")
        if ok and new_name:
            self.service.rename_entity(instance_id, new_name)
            self.refresh()

    def _edit_initiative(self, instance_id: str):
        new_init, ok = QInputDialog.getInt(self, "Edit Initiative", "New initiative:", 0, 0, 99)
        if ok:
            self.service.change_initiative(instance_id, new_init)
            self.refresh()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Space:
            self._on_advance_turn()
        elif event.key() == Qt.Key.Key_Delete:
            if self.entity_list.currentItem():
                row = self.entity_list.currentRow()
                if row < len(self.service.encounter.entities):
                    self._remove_entity(self.service.encounter.entities[row].instance_id)
        else:
            super().keyPressEvent(event)
