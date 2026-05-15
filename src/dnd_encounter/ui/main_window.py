# ui/main_window.py
# Thin UI layer - only calls EncounterService and reacts to events

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QPushButton, QSpinBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

from dnd_encounter.application.services.encounter_service import EncounterService
from dnd_encounter.ui.add_monster_dialog import AddMonsterDialog


class MainWindow(QMainWindow):
    def __init__(self, service: EncounterService):
        super().__init__()
        self.service = service
        self.setWindowTitle("D&D Encounter Manager")
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        sidebar = self._create_sidebar()
        layout.addWidget(sidebar, 1)

        stat_panel = self._create_stat_panel()
        layout.addWidget(stat_panel, 2)

        self.refresh()

    def _create_sidebar(self) -> QWidget:
        group = QGroupBox("Initiative Order")
        layout = QVBoxLayout(group)

        self.entity_list = QListWidget()
        self.entity_list.currentRowChanged.connect(self._on_entity_selected)
        layout.addWidget(self.entity_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Monster")
        self.btn_add.clicked.connect(self._on_add_monster)
        btn_layout.addWidget(self.btn_add)
        layout.addLayout(btn_layout)

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
        state = self.service.get_state()
        self.entity_list.clear()

        for entity in state.entities:
            text = f"{entity.display_name} (Init: {entity.initiative}, HP: {entity.current_hp})"
            self.entity_list.addItem(text)

    def _on_entity_selected(self, row: int):
        if row < 0:
            return
        state = self.service.get_state()
        if row < len(state.entities):
            e = state.entities[row]
            self.lbl_name.setText(e.display_name)
            self.lbl_hp.setText(f"{e.current_hp} / {e.max_hp}")
            self.lbl_initiative.setText(str(e.initiative))
            self.lbl_conditions.setText(", ".join(e.conditions) if e.conditions else "None")
            self.spin_hp.setValue(e.current_hp or 0)

    def _on_add_monster(self):
        dialog = AddMonsterDialog(self.service, self)
        if dialog.exec():
            monster_id = dialog.get_selected_monster_id()
            if monster_id:
                self.service.add_monster(monster_id)
                self.refresh()

    def _on_edit_hp(self):
        if not self.entity_list.currentItem():
            return
        row = self.entity_list.currentRow()
        state = self.service.get_state()
        if row < len(state.entities):
            entity = state.entities[row]
            new_hp = self.spin_hp.value()
            self.service.edit_hp(entity.instance_id, new_hp)
            self.refresh()
