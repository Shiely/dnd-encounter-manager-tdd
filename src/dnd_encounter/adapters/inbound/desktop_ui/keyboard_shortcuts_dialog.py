"""
Keyboard Shortcuts Dialog

Provides discoverability for all global keyboard shortcuts in the application.
"""

from PySide6.QtWidgets import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
    QPushButton,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt


SHORTCUTS = [
    ("Add Monster", "Ctrl + M"),
    ("Add Player", "Ctrl + P"),
    ("Remove Selected", "Delete  /  Backspace"),
    ("Open Conditions Panel", "Ctrl + K"),
    ("Advance Turn", "Space"),
    ("Undo Last Action", "Ctrl + Z"),
    ("Increase HP (selected or global)", "+"),
    ("Decrease HP (selected or global)", "-"),
    ("Open this dialog", "F1"),
]


class KeyboardShortcutsDialog(QDialog):
    """Simple, clean dialog listing all keyboard shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumWidth(420)
        self.resize(480, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Table
        table = QTableWidget(len(SHORTCUTS), 2, self)
        table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        for row, (action, shortcut) in enumerate(SHORTCUTS):
            table.setItem(row, 0, QTableWidgetItem(action))
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, shortcut_item)

        layout.addWidget(table)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Also allow closing with Escape (default for QDialog)
        self.setModal(True)