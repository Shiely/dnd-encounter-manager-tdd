from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
)

# Use canonical DTO from application layer (self-heal for consistency with Sidebar)
try:
    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO
except ImportError:
    from .initiative_list_model import EncounterStateDTO, EntityRowDTO  # type: ignore fallback


class StatBlockPanel(QScrollArea):
    """Right-hand panel showing live stat block for selected entity.

    Displays current_hp and active conditions from the EntityRowDTO
    (live state), not from static monster definition.
    """

    hp_adjusted = Signal(str, int)  # (instance_id, delta)
    hp_set = Signal(str, int)       # (instance_id, absolute_new_hp) for direct set

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

        # HP Adjustment controls (Priority #1 - HP Editing UI)
        hp_layout = QHBoxLayout()
        self.btn_hp_minus = QPushButton("-1 HP")
        self.btn_hp_plus = QPushButton("+1 HP")
        self.btn_hp_minus.clicked.connect(self._on_hp_minus)
        self.btn_hp_plus.clicked.connect(self._on_hp_plus)
        hp_layout.addWidget(self.btn_hp_minus)
        hp_layout.addWidget(self.btn_hp_plus)
        self._layout.addLayout(hp_layout)

        # Direct HP setter (enrichment for StatBlockPanel)
        direct_hp_layout = QHBoxLayout()
        self.hp_input = QLineEdit()
        self.hp_input.setPlaceholderText("Set HP")
        self.hp_input.setMaximumWidth(60)
        self.hp_input.returnPressed.connect(self._on_set_hp)  # Enter key support
        self.btn_set_hp = QPushButton("Set")
        self.btn_set_hp.clicked.connect(self._on_set_hp)
        direct_hp_layout.addWidget(self.hp_input)
        direct_hp_layout.addWidget(self.btn_set_hp)
        self._layout.addLayout(direct_hp_layout)

        self._layout.addStretch()

        self._current_instance_id: str | None = None

    @Slot()
    def refresh(self, state: EncounterStateDTO | None, instance_id: str | None = None) -> None:
        if state is None or instance_id is None:
            self._title.setText("No entity selected")
            self._content.setText("")
            self._current_instance_id = None
            return

        entity = None
        for e in getattr(state, "entities", []):
            if getattr(e, "instance_id", None) == instance_id:
                entity = e
                break

        if entity is None:
            self._title.setText("Entity not found")
            self._content.setText("")
            return

        self._current_instance_id = instance_id

        title_text = getattr(entity, "display_name", "Unknown")
        is_monster = getattr(entity, "entity_type", "monster") == "monster"
        title_text += " (Monster)" if is_monster else " (Player)"

        if getattr(entity, "is_current_turn", False):
            title_text += "  ★ Current Turn"

        self._title.setText(title_text)

        lines: list[str] = []
        lines.append(f"<b>Initiative:</b> {getattr(entity, 'initiative', '?')}")

        current_hp = getattr(entity, "current_hp", None)
        max_hp = getattr(entity, "max_hp", None)

        if current_hp is not None:
            if max_hp is not None:
                lines.append(f"<b>HP:</b> {current_hp} / {max_hp}")
            else:
                lines.append(f"<b>Current HP:</b> {current_hp}")

        conditions = getattr(entity, "conditions", []) or []
        if conditions:
            lines.append(f"<b>Conditions:</b> {', '.join(conditions)}")
        else:
            lines.append("<b>Conditions:</b> None")

        self._content.setText("<br>".join(lines))

    def _on_hp_minus(self) -> None:
        if self._current_instance_id:
            self.hp_adjusted.emit(self._current_instance_id, -1)

    def _on_hp_plus(self) -> None:
        if self._current_instance_id:
            self.hp_adjusted.emit(self._current_instance_id, +1)

    def _on_set_hp(self) -> None:
        if self._current_instance_id:
            try:
                new_hp = int(self.hp_input.text().strip())
                self.hp_set.emit(self._current_instance_id, new_hp)
                self.hp_input.clear()
            except ValueError:
                pass  # ignore bad input in UI
