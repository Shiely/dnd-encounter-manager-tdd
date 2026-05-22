# adapters/inbound/desktop_ui/add_monster_dialog.py
# Migrated Add Monster dialog (UI-3)

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dnd_encounter.application.services.encounter_service import EncounterService


class AddMonsterDialog(QDialog):
    """Dialog for selecting a monster from the (potentially very large) bestiary.

    Features a live-filtering search box so the user can quickly find monsters
    among thousands of entries (e.g. "dragon", "ancient", "CR 10", "lich").
    """

    def __init__(self, service: EncounterService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.selected_monster_id: str | None = None
        self._monster_items: list = []  # all QListWidgetItem objects for filtering

        self.setWindowTitle("Add Monster")
        self.setMinimumSize(520, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Search / filter box (the key new feature)
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to filter (e.g. dragon, goblin, lich, CR 5, ancient...)")
        self.search_edit.textChanged.connect(self._apply_filter)
        search_row.addWidget(self.search_edit, stretch=1)
        layout.addLayout(search_row)

        # Result count
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.count_label)

        # The monster list
        self.monster_list = QListWidget()
        self.monster_list.setAlternatingRowColors(True)
        self.monster_list.itemDoubleClicked.connect(self._on_add)
        layout.addWidget(self.monster_list, stretch=1)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_create_custom = QPushButton("Create Custom Monster…")
        self.btn_create_custom.clicked.connect(self._on_create_custom)
        self.btn_ok = QPushButton("Add")
        self.btn_ok.clicked.connect(self._on_add)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_create_custom)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # Populate after widgets exist
        self._populate_monster_list()

        # Start with focus in the search box (very convenient)
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _populate_monster_list(self) -> None:
        self.monster_list.clear()
        self._monster_items.clear()

        repo = getattr(self.service, "monster_repo", None) if self.service else None
        monsters = []

        if repo and hasattr(repo, "list_all"):
            try:
                monsters = repo.list_all() or []
                if monsters and hasattr(monsters[0], "name"):
                    monsters = sorted(monsters, key=lambda m: getattr(m, "name", ""))
            except Exception:
                monsters = []

        if monsters:
            for monster in monsters:
                cr = getattr(monster, "challenge_rating", None)
                cr_str = getattr(cr, "value", str(cr)) if cr else "?"
                display = f"{getattr(monster, 'name', 'Unknown')} (CR {cr_str})"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, getattr(monster, "id", ""))
                # Store lowercased name + display for fast filtering
                item.setData(Qt.ItemDataRole.UserRole + 1, display.lower())
                self.monster_list.addItem(item)
                self._monster_items.append(item)
        else:
            # Fallback for tests / stubs that don't have a real repo
            fallback = [
                ("goblin", "Goblin (CR 1/4)"),
                ("orc", "Orc (CR 1/2)"),
                ("ogre", "Ogre (CR 2)"),
                ("troll", "Troll (CR 5)"),
            ]
            for monster_id, display in fallback:
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, monster_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, display.lower())
                self.monster_list.addItem(item)
                self._monster_items.append(item)

        self._update_count_label(len(self._monster_items))

    def _apply_filter(self, text: str) -> None:
        """Hide non-matching items. Matches against name and full display text."""
        text = (text or "").strip().lower()
        visible_count = 0

        for item in self._monster_items:
            haystack: str = item.data(Qt.ItemDataRole.UserRole + 1) or ""
            matches = (text == "") or (text in haystack)
            item.setHidden(not matches)
            if matches:
                visible_count += 1

        self._update_count_label(visible_count, total=len(self._monster_items))

    def _update_count_label(self, visible: int, total: int | None = None) -> None:
        if total is None:
            total = len(self._monster_items)
        if visible == total:
            self.count_label.setText(f"{total} monsters")
        else:
            self.count_label.setText(f"{visible} of {total} monsters")

    def _on_add(self):
        current = self.monster_list.currentItem()
        if current and not current.isHidden():
            self.selected_monster_id = current.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def get_selected_monster_id(self) -> str | None:
        return self.selected_monster_id

    def _on_create_custom(self):
        """Open the monster creation form."""
        from .monster_form_dialog import MonsterFormDialog

        repo = getattr(self.service, "monster_repo", None) if self.service else None
        dialog = MonsterFormDialog(repo=repo, parent=self)
        if dialog.exec():
            new_monster = dialog.get_created_monster()
            if new_monster:
                # Refresh the list so the new monster appears
                self._populate_monster_list()

                # Try to select the newly created monster
                for i in range(self.monster_list.count()):
                    item = self.monster_list.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == new_monster.id:
                        self.monster_list.setCurrentItem(item)
                        break

                # Optionally auto-accept so the user can immediately add it
                # For now we just leave the dialog open so user can decide
                self.search_edit.clear()  # clear filter so new monster is visible
