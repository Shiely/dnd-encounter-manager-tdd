from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtGui import QColor

# Use the single source of truth for DTOs (hexagonal boundary)
try:
    from dnd_encounter.application.dto.encounter_dto import (
        EncounterStateDTO,
        EntityRowDTO,
    )
except ImportError:  # fallback for isolated testing
    from dataclasses import dataclass

    @dataclass
    class EntityRowDTO:  # type: ignore[no-redef]
        instance_id: str
        display_name: str
        entity_type: str = "monster"
        initiative: int = 0
        current_hp: int | None = None
        max_hp: int | None = None
        conditions: list[str] = None  # type: ignore[assignment]
        is_current_turn: bool = False
        is_active: bool = True
        monster_id: str | None = None

    @dataclass
    class EncounterStateDTO:  # type: ignore[no-redef]
        encounter_id: str = "test"
        round_number: int = 1
        entities: list[EntityRowDTO] = None  # type: ignore[assignment]
        undo_available: bool = False


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
            is_monster = getattr(entity, "entity_type", "monster") == "monster"
            hp_part = f" | HP: {entity.current_hp}" if is_monster and getattr(entity, "current_hp", None) is not None else ""
            return f"{entity.display_name} | Init: {entity.initiative}{hp_part}"

        if role == Qt.BackgroundRole and getattr(entity, "is_current_turn", False):
            return QColor("#4a90d9")
        if role == Qt.ForegroundRole and getattr(entity, "is_current_turn", False):
            return QColor("white")

        if role == Qt.UserRole:
            return entity.instance_id

        if role == Qt.ToolTipRole:
            conds = ", ".join(getattr(entity, "conditions", []) or [])
            return f"Conditions: {conds or 'None'} | Active: {getattr(entity, 'is_active', True)}"

        return None

    def update_from_state(self, state: EncounterStateDTO) -> None:
        self.beginResetModel()
        self._entities = list(state.entities)
        # Prefer per-entity flag (real DTO); fall back to legacy index attr
        computed_index = -1
        for i, e in enumerate(self._entities):
            if getattr(e, "is_current_turn", False):
                computed_index = i
                break
        self._current_turn_index = computed_index if computed_index >= 0 else getattr(state, "current_turn_index", -1)
        self.endResetModel()

    def get_instance_id(self, row: int) -> str | None:
        if 0 <= row < len(self._entities):
            return self._entities[row].instance_id
        return None
