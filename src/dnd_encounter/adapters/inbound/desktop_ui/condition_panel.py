from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    from dnd_encounter.application.dto.encounter_dto import EntityRowDTO
except ImportError:
    from .initiative_list_model import EntityRowDTO  # type: ignore fallback


CONDITIONS = [
    "Blinded",
    "Charmed",
    "Deafened",
    "Frightened",
    "Grappled",
    "Incapacitated",
    "Invisible",
    "Paralyzed",
    "Petrified",
    "Poisoned",
    "Prone",
    "Restrained",
    "Stunned",
    "Unconscious",
    "Exhaustion",
]


class ConditionPanel(QDialog):
    """Modal dialog for toggling conditions on the selected entity.

    Checkboxes reflect current EntityRowDTO.conditions.
    Emits condition_toggled when user changes a checkbox.
    """

    condition_toggled = Signal(str, str, bool)  # (instance_id, condition_name, checked)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Conditions")
        self.setModal(True)
        self.resize(320, 480)

        self._instance_id: str | None = None
        self._checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        header = QLabel("Toggle Conditions")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        for cond in CONDITIONS:
            cb = QCheckBox(cond)
            cb.toggled.connect(self._make_handler(cond))
            layout.addWidget(cb)
            self._checkboxes[cond] = cb

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _make_handler(self, condition_name: str):
        def handler(checked: bool) -> None:
            if self._instance_id:
                self.condition_toggled.emit(
                    self._instance_id, condition_name, checked
                )
        return handler

    def refresh(self, entity: EntityRowDTO | None) -> None:
        if entity is None:
            self._instance_id = None
            for cb in self._checkboxes.values():
                cb.setChecked(False)
            return

        self._instance_id = entity.instance_id
        current = set(getattr(entity, "conditions", []) or [])

        for name, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(name in current)
            cb.blockSignals(False)

    def _on_toggled(self, condition_name: str, checked: bool) -> None:
        if self._instance_id:
            self.condition_toggled.emit(self._instance_id, condition_name, checked)
