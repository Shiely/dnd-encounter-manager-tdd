from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtGui import QColor

try:
    from dnd_encounter.application.dtos import EntityRowDTO, EncounterStateDTO
except ImportError:
    # Fallback for early UI phase - will be replaced when DTOs are confirmed
    from dataclasses import dataclass
    from typing import Any

    @dataclass
    class EntityRowDTO:
        instance_id: str
        display_name: str
        initiative: int
        current_hp: int | None = None
        is_monster: bool = False
        conditions: list[str] | None = None
        is_active: bool = True

    @dataclass
    class EncounterStateDTO:
        entities: list[EntityRowDTO]
        current_turn_index: int = 0
        round_number: int = 1
        error: str | None = None


class InitiativeListModel(QAbstractListModel):
    """Custom model for displaying initiative order in QListView.

    Each row shows display_name, initiative, and HP (for monsters).
    Current turn row is highlighted with a distinct background.
    """

    def __init__(self, parent: QWidget | None = None) -> None:  # type: ignore[name-defined]
        super().__init__(parent)
        self._entities: list[EntityRowDTO] = []
        self._current_turn_index: int = -1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._entities)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._entities):
            return None

        entity = self._entities[index.row()]

        if role == Qt.DisplayRole:
            hp_part = f" | HP: {entity.current_hp}" if entity.is_monster and entity.current_hp is not None else ""
            return f"{entity.display_name} | Init: {entity.initiative}{hp_part}"

        if role == Qt.BackgroundRole:
            if index.row() == self._current_turn_index:
                return QColor("#4a90d9")  # Distinct blue highlight for current turn
            return None

        if role == Qt.ForegroundRole:
            if index.row() == self._current_turn_index:
                return QColor("white")
            return None

        if role == Qt.UserRole:
            return entity.instance_id

        if role == Qt.ToolTipRole:
            conds = ", ".join(entity.conditions or [])
            return f"Conditions: {conds or 'None'} | Active: {entity.is_active}"

        return None

    def update_from_state(self, state: EncounterStateDTO) -> None:
        """Replace model data from EncounterStateDTO and highlight current turn."""
        self.beginResetModel()
        self._entities = list(state.entities)  # copy
        self._current_turn_index = state.current_turn_index
        self.endResetModel()

    def get_instance_id(self, row: int) -> str | None:
        if 0 <= row < len(self._entities):
            return self._entities[row].instance_id
        return None
