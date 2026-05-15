# ui/add_player_dialog.py
# Add Player dialog

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QSpinBox, QPushButton, QLabel, QWidget
from PySide6.QtCore import Qt


class AddPlayerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.player_name: str | None = None
        self.initiative: int | None = None
        self.max_hp: int | None = None

        self.setWindowTitle("Add Player Character")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Aragorn")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Initiative
        init_layout = QHBoxLayout()
        init_layout.addWidget(QLabel("Initiative:"))
        self.init_input = QSpinBox()
        self.init_input.setRange(0, 30)
        self.init_input.setValue(15)
        init_layout.addWidget(self.init_input)
        layout.addLayout(init_layout)

        # Max HP
        hp_layout = QHBoxLayout()
        hp_layout.addWidget(QLabel("Max HP:"))
        self.hp_input = QSpinBox()
        self.hp_input.setRange(1, 500)
        self.hp_input.setValue(45)
        hp_layout.addWidget(self.hp_input)
        layout.addLayout(hp_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Add Player")
        self.btn_ok.clicked.connect(self._on_add)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _on_add(self) -> None:
        name = self.name_input.text().strip()
        if name:
            self.player_name = name
            self.initiative = self.init_input.value()
            self.max_hp = self.hp_input.value()
            self.accept()
        else:
            self.reject()

    def get_player_data(self) -> tuple[str, int, int] | None:
        if self.player_name and self.initiative is not None and self.max_hp is not None:
            return (self.player_name, self.initiative, self.max_hp)
        return None
