"""
MonsterFormDialog

A comprehensive form for creating (and eventually editing) custom monsters.
All fields from MonsterDefinition are supported, but only `name` and `hit_points`
are required.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QTabWidget,
    QWidget,
    QScrollArea,
    QTextEdit,
    QFormLayout,
    QGroupBox,
)

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition
from dnd_encounter.domain.value_objects.ability_scores import AbilityScores
from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating
from dnd_encounter.ports.outbound.i_monster_repository import IMonsterRepository


class MonsterFormDialog(QDialog):
    """Form for creating a new custom monster."""

    def __init__(self, repo: IMonsterRepository | None = None, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.created_monster: MonsterDefinition | None = None

        self.setWindowTitle("Create Custom Monster")
        self.setMinimumSize(720, 620)

        self._feature_widgets = {
            "traits": [],
            "actions": [],
            "bonus_actions": [],
            "reactions": [],
            "legendary_actions": [],
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, stretch=1)

        self._build_basic_tab()
        self._build_combat_tab()
        self._build_abilities_tab()
        self._build_defenses_tab()
        self._build_features_tab()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("Save Monster")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # Set some sensible defaults
        self._set_defaults()

    def _build_basic_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Required")
        form.addRow("Name *", self.name_edit)

        self.size_combo = QComboBox()
        self.size_combo.addItems(["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"])
        form.addRow("Size", self.size_combo)

        self.type_edit = QLineEdit()
        form.addRow("Type", self.type_edit)

        self.alignment_edit = QLineEdit()
        form.addRow("Alignment", self.alignment_edit)

        self.source_edit = QLineEdit()
        self.source_edit.setText("Custom")
        form.addRow("Source", self.source_edit)

        self.tabs.addTab(tab, "Basic Info")

    def _build_combat_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.ac_spin = QSpinBox()
        self.ac_spin.setRange(1, 30)
        form.addRow("Armor Class", self.ac_spin)

        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 2000)
        self.hp_spin.setValue(10)
        form.addRow("Hit Points *", self.hp_spin)

        self.hit_dice_edit = QLineEdit()
        form.addRow("Hit Dice", self.hit_dice_edit)

        self.cr_edit = QLineEdit()
        self.cr_edit.setPlaceholderText("e.g. 5 or 1/2")
        form.addRow("Challenge Rating", self.cr_edit)

        self.xp_spin = QSpinBox()
        self.xp_spin.setRange(0, 100000)
        form.addRow("XP", self.xp_spin)

        self.tabs.addTab(tab, "Combat Stats")

    def _build_abilities_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("Ability Scores")
        form = QFormLayout(group)

        self.str_spin = QSpinBox()
        self.str_spin.setRange(1, 30)
        form.addRow("STR", self.str_spin)

        self.dex_spin = QSpinBox()
        self.dex_spin.setRange(1, 30)
        form.addRow("DEX", self.dex_spin)

        self.con_spin = QSpinBox()
        self.con_spin.setRange(1, 30)
        form.addRow("CON", self.con_spin)

        self.int_spin = QSpinBox()
        self.int_spin.setRange(1, 30)
        form.addRow("INT", self.int_spin)

        self.wis_spin = QSpinBox()
        self.wis_spin.setRange(1, 30)
        form.addRow("WIS", self.wis_spin)

        self.cha_spin = QSpinBox()
        self.cha_spin.setRange(1, 30)
        form.addRow("CHA", self.cha_spin)

        layout.addWidget(group)
        self.tabs.addTab(tab, "Abilities")

    def _build_defenses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.saves_edit = QLineEdit()
        self.saves_edit.setPlaceholderText("e.g. DEX +5, CON +8")
        layout.addWidget(QLabel("Saving Throws"))
        layout.addWidget(self.saves_edit)

        self.skills_edit = QLineEdit()
        self.skills_edit.setPlaceholderText("e.g. Perception +10, Stealth +6")
        layout.addWidget(QLabel("Skills"))
        layout.addWidget(self.skills_edit)

        self.resist_edit = QLineEdit()
        layout.addWidget(QLabel("Damage Resistances (comma separated)"))
        layout.addWidget(self.resist_edit)

        self.immune_edit = QLineEdit()
        layout.addWidget(QLabel("Damage Immunities (comma separated)"))
        layout.addWidget(self.immune_edit)

        self.vuln_edit = QLineEdit()
        layout.addWidget(QLabel("Damage Vulnerabilities (comma separated)"))
        layout.addWidget(self.vuln_edit)

        self.condition_immune_edit = QLineEdit()
        layout.addWidget(QLabel("Condition Immunities (comma separated)"))
        layout.addWidget(self.condition_immune_edit)

        self.tabs.addTab(tab, "Defenses")

    def _build_features_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._add_feature_section(layout, "Traits", "traits")
        self._add_feature_section(layout, "Actions", "actions")
        self._add_feature_section(layout, "Bonus Actions", "bonus_actions")
        self._add_feature_section(layout, "Reactions", "reactions")
        self._add_feature_section(layout, "Legendary Actions", "legendary_actions")

        self.tabs.addTab(tab, "Features & Actions")

    def _add_feature_section(self, parent_layout, title: str, key: str):
        group = QGroupBox(title)
        v = QVBoxLayout(group)

        add_btn = QPushButton(f"+ Add {title[:-1] if title.endswith('s') else title}")
        add_btn.clicked.connect(lambda _, k=key: self._add_feature_row(k))
        v.addWidget(add_btn)

        container = QWidget()
        container.setLayout(QVBoxLayout())
        v.addWidget(container)

        self._feature_widgets[key] = container.layout()

        parent_layout.addWidget(group)

    def _add_feature_row(self, key: str, name: str = "", description: str = ""):
        row = QHBoxLayout()

        name_edit = QLineEdit(name)
        name_edit.setPlaceholderText("Name")
        name_edit.setMinimumWidth(180)

        desc_edit = QTextEdit(description)
        desc_edit.setPlaceholderText("Description")
        desc_edit.setMaximumHeight(60)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self._remove_feature_row(key, row))

        row.addWidget(name_edit)
        row.addWidget(desc_edit, stretch=1)
        row.addWidget(remove_btn)

        self._feature_widgets[key].addLayout(row)

    def _remove_feature_row(self, key: str, row_layout: QHBoxLayout):
        # Remove all widgets in the row
        for i in reversed(range(row_layout.count())):
            item = row_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        row_layout.deleteLater()

    def _set_defaults(self):
        self.size_combo.setCurrentText("Medium")
        self.ac_spin.setValue(10)
        self.hp_spin.setValue(10)
        self.hit_dice_edit.setText("1d8")
        self.cr_edit.setText("1")
        self.str_spin.setValue(10)
        self.dex_spin.setValue(10)
        self.con_spin.setValue(10)
        self.int_spin.setValue(10)
        self.wis_spin.setValue(10)
        self.cha_spin.setValue(10)

    def _collect_feature_list(self, key: str) -> list[dict[str, str]]:
        result = []
        layout = self._feature_widgets.get(key)
        if not layout:
            return result

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.layout(), QHBoxLayout):
                h = item.layout()
                name_edit = h.itemAt(0).widget() if h.itemAt(0) else None
                desc_edit = h.itemAt(1).widget() if h.itemAt(1) else None

                if name_edit and desc_edit:
                    name = name_edit.text().strip()
                    desc = desc_edit.toPlainText().strip()
                    if name or desc:
                        result.append({"name": name or "Unnamed", "description": desc})
        return result

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            self.name_edit.setFocus()
            return

        hp = self.hp_spin.value()
        if hp < 1:
            self.hp_spin.setFocus()
            return

        # Build MonsterDefinition
        cr_value = self.cr_edit.text().strip() or "0"

        monster = MonsterDefinition(
            id=name.lower().replace(" ", "-").replace("'", ""),
            name=name,
            size=self.size_combo.currentText(),
            type_=self.type_edit.text().strip() or "unknown",
            alignment=self.alignment_edit.text().strip() or "unaligned",
            armor_class=self.ac_spin.value(),
            hit_points=hp,
            hit_dice=self.hit_dice_edit.text().strip() or "1d8",
            speed={"walk": 30, "fly": 0, "swim": 0, "climb": 0, "burrow": 0, "hover": False},
            ability_scores=AbilityScores(
                str_=self.str_spin.value(),
                dex=self.dex_spin.value(),
                con=self.con_spin.value(),
                int_=self.int_spin.value(),
                wis=self.wis_spin.value(),
                cha=self.cha_spin.value(),
            ),
            challenge_rating=ChallengeRating(cr_value),
            xp=self.xp_spin.value(),
            source=self.source_edit.text().strip() or "Custom",
            saving_throws={},
            skills={},
            damage_resistances=[],
            damage_immunities=[],
            damage_vulnerabilities=[],
            condition_immunities=[],
            senses={},
            languages=[],
            traits=self._collect_feature_list("traits"),
            actions=self._collect_feature_list("actions"),
            bonus_actions=self._collect_feature_list("bonus_actions"),
            reactions=self._collect_feature_list("reactions"),
            legendary_actions=self._collect_feature_list("legendary_actions"),
            spellcasting=[],
            environments=[],
        )

        # Save if repo is available
        if self.repo and hasattr(self.repo, "upsert"):
            try:
                self.repo.upsert(monster)
            except Exception as e:
                print(f"[MonsterForm] Failed to upsert monster: {e}")

        self.created_monster = monster
        self.accept()

    def get_created_monster(self) -> MonsterDefinition | None:
        return self.created_monster