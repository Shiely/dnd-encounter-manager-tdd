# ui/add_monster_dialog.py
# Improved Add Monster dialog

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
from PySide6.QtCore import Qt


from dnd_encounter.application.services.encounter_service import EncounterService


class AddMonsterDialog(QDialog):
    def __init__(self, service: EncounterService, parent=None):
        super().__init__(parent)
        self.service = service
        self.selected_monster_id = None

        self.setWindowTitle("Add Monster")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Select a monster to add:")
        layout.addWidget(label)

        # Monster list
        self.monster_list = QListWidget()
        self._populate_monster_list()
        layout.addWidget(self.monster_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Add")
        self.btn_ok.clicked.connect(self._on_add)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _populate_monster_list(self):
        # For now, use a hardcoded list (later we'll pull from service)
        monsters = [
            ("goblin", "Goblin (CR 1/4)"),
            ("orc", "Orc (CR 1/2)"),
            ("ogre", "Ogre (CR 2)"),
            ("troll", "Troll (CR 5)"),
        ]

        for monster_id, display in monsters:
            self.monster_list.addItem(display)
            # Store monster_id in item data
            item = self.monster_list.item(self.monster_list.count() - 1)
            item.setData(Qt.UserRole, monster_id)

    def _on_add(self):
        current = self.monster_list.currentItem()
        if current:
            self.selected_monster_id = current.data(Qt.UserRole)
            self.accept()
        else:
            self.reject()

    def get_selected_monster_id(self):
        return self.selected_monster_id
