from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)

try:
    from .initiative_list_model import EntityRowDTO, EncounterStateDTO
except ImportError:
    from initiative_list_model import EntityRowDTO, EncounterStateDTO  # type: ignore


class StatBlockPanel(QScrollArea):
    """Right-hand panel showing live stat block for selected entity.

    Displays current_hp and active conditions from the EntityRowDTO
    (live state), not from static monster definition.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatBlockPanel")
        self.setWidgetResizable(True)

        self._container = QWidget()
        self.setWidget(self._container)

        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self._title)

        self._content = QLabel()
        self._content.setWordWrap(True)
        self._content.setStyleSheet("font-size: 13px; line-height: 1.4;")
        self._layout.addWidget(self._content)

        self._layout.addStretch()

        self._current_instance_id: str | None = None

    @Slot()
    def refresh(self, state: EncounterStateDTO | None, instance_id: str | None = None) -> None:
        if state is None or instance_id is None:
            self._title.setText("No entity selected")
            self._content.setText("")
            self._current_instance_id = None
            return

        entity = next((e for e in state.entities if e.instance_id == instance_id), None)
        if entity is None:
            self._title.setText("Entity not found")
            self._content.setText("")
            return

        self._current_instance_id = instance_id

        # Title
        title_text = entity.display_name
        if entity.is_monster:
            title_text += " (Monster)"
        else:
            title_text += " (Player)"
        self._title.setText(title_text)

        # Content
        lines: list[str] = []
        lines.append(f"<b>Initiative:</b> {entity.initiative}")

        if entity.is_monster and entity.current_hp is not None:
            lines.append(f"<b>Current HP:</b> {entity.current_hp}")

        conditions = entity.conditions or []
        if conditions:
            lines.append(f"<b>Conditions:</b> {', '.join(conditions)}")
        else:
            lines.append("<b>Conditions:</b> None")

        self._content.setText("<br>".join(lines))
