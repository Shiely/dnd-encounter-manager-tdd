from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtGui import QColor


# Minimal DTO fallbacks (UI layer only - real DTOs live in application layer)
# This allows Commit 2 to be self-contained while DTO module is finalized
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
    """Custom QAbstractListModel for initiative order sidebar.

    Renders display_name | Init: X | HP: Y (monsters only).
    Current-turn row gets distinct blue background + white text.
    Supports entity_selected via UserRole.
    """

    def __init__(self, parent: "QWidget | None" = None) -> None:
        super().__init__(parent)
        self._entities: list[EntityRowDTO] = []
        self._current_turn_index: int = -1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
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

        if role == Qt.BackgroundRole and index.row() == self._current_turn_index:
            return QColor("#4a90d9")
        if role == Qt.ForegroundRole and index.row() == self._current_turn_index:
            return QColor("white")

        if role == Qt.UserRole:
            return entity.instance_id

        if role == Qt.ToolTipRole:
            conds = ", ".join(entity.conditions or [])
            return f"Conditions: {conds or 'None'} | Active: {entity.is_active}"

        return None

    def update_from_state(self, state: EncounterStateDTO) -> None:
        self.beginResetModel()
        self._entities = list(state.entities)
        self._current_turn_index = getattr(state, "current_turn_index", -1)
        self.endResetModel()

    def get_instance_id(self, row: int) -> str | None:
        if 0 <= row < len(self._entities):
            return self._entities[row].instance_id
        return None
