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
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from pathlib import Path

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

    def __init__(self, parent: QWidget | None = None, monster_repo=None) -> None:
        super().__init__(parent)
        self.setObjectName("StatBlockPanel")
        self.setWidgetResizable(True)
        self._monster_repo = monster_repo   # optional – used for rich monster details

        self._container = QWidget()
        self.setWidget(self._container)

        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        # Header row: Title on left, monster image/token on right
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        self._title = QLabel()
        self._title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._title.setWordWrap(True)
        header_layout.addWidget(self._title, stretch=1)

        self._image_label = QLabel()
        self._image_label.setFixedSize(140, 140)
        self._image_label.setStyleSheet("border: 1px solid #555; background: #222;")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setScaledContents(False)
        header_layout.addWidget(self._image_label)

        self._layout.addLayout(header_layout)

        self._content = QLabel()
        self._content.setWordWrap(True)
        self._content.setStyleSheet("font-size: 13px; line-height: 1.35;")
        self._content.setOpenExternalLinks(False)
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
            self._clear_image()
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

        # --- Try to enrich with full monster definition (new rich data) ---
        self._try_enrich_with_definition(entity)

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

    # ------------------------------------------------------------------
    # Rich monster definition rendering (NEW)
    # ------------------------------------------------------------------

    def _try_enrich_with_definition(self, entity) -> None:
        """If we have a monster_repo and this is a monster, fetch the full definition and show rich data + image."""
        if not self._monster_repo or not entity:
            self._clear_image()
            return
        if getattr(entity, "entity_type", "monster") != "monster":
            self._clear_image()
            return

        monster_id = getattr(entity, "monster_id", None)
        if not monster_id:
            self._clear_image()
            return

        try:
            definition = self._monster_repo.get(monster_id)
            if definition:
                rich_html = self._build_rich_monster_html(definition)
                current = self._content.text()
                self._content.setText(current + "<hr>" + rich_html)

                # Load image if available
                self._load_monster_image(definition)
            else:
                self._clear_image()
        except Exception:
            self._clear_image()

    def _build_rich_monster_html(self, m) -> str:
        """Produce a nice HTML block for the full monster stat block."""
        parts: list[str] = []

        # Header line
        cr = getattr(getattr(m, "challenge_rating", None), "value", "?")
        parts.append(f"<b><i>CR {cr}</i></b>")

        # Ability scores (compact)
        ab = getattr(m, "ability_scores", None)
        if ab:
            scores = "  |  ".join([
                f"STR {getattr(ab, 'str_', 10)}",
                f"DEX {getattr(ab, 'dex', 10)}",
                f"CON {getattr(ab, 'con', 10)}",
                f"INT {getattr(ab, 'int_', 10)}",
                f"WIS {getattr(ab, 'wis', 10)}",
                f"CHA {getattr(ab, 'cha', 10)}",
            ])
            parts.append(f"<small>{scores}</small>")

        # Saving Throws + Skills
        saves = getattr(m, "saving_throws", {}) or {}
        skills = getattr(m, "skills", {}) or {}
        if saves or skills:
            def fmt(d): return ", ".join(f"{k.upper()} +{v}" for k, v in d.items())
            line = ""
            if saves:
                line += f"<b>Saves:</b> {fmt(saves)}"
            if skills:
                if line: line += "   "
                line += f"<b>Skills:</b> {fmt(skills)}"
            parts.append(line)

        # Defenses
        resists = getattr(m, "damage_resistances", []) or []
        immunes = getattr(m, "damage_immunities", []) or []
        vulns = getattr(m, "damage_vulnerabilities", []) or []
        cond_immune = getattr(m, "condition_immunities", []) or []

        def fmt_list(lst, label):
            return f"<b>{label}:</b> {', '.join(lst)}" if lst else ""

        def_lines = [
            fmt_list(resists, "Resist"),
            fmt_list(immunes, "Immune"),
            fmt_list(vulns, "Vulnerable"),
            fmt_list(cond_immune, "Condition Immune"),
        ]
        def_lines = [d for d in def_lines if d]
        if def_lines:
            parts.append(" | ".join(def_lines))

        # Senses + Languages
        senses = getattr(m, "senses", {}) or {}
        langs = getattr(m, "languages", []) or []
        sense_str = ", ".join(f"{k} {v}" for k, v in senses.items() if v and k != "passive_perception")
        if senses.get("passive_perception"):
            sense_str += f", passive Perception {senses['passive_perception']}"
        if sense_str:
            parts.append(f"<b>Senses:</b> {sense_str}")
        if langs:
            parts.append(f"<b>Languages:</b> {', '.join(langs)}")

        # Traits / Features
        traits = getattr(m, "traits", []) or []
        if traits:
            parts.append("<b>Traits</b>")
            for t in traits[:6]:   # limit for UI space
                parts.append(f"• <b>{t.get('name','')}</b> — {t.get('description','')[:180]}")

        # Actions
        actions = getattr(m, "actions", []) or []
        if actions:
            parts.append("<b>Actions</b>")
            for a in actions[:5]:
                parts.append(f"• <b>{a.get('name','')}</b> — {a.get('description','')[:160]}")

        # Legendary Actions
        leg = getattr(m, "legendary_actions", []) or []
        if leg:
            parts.append("<b>Legendary Actions</b>")
            for l in leg[:4]:
                parts.append(f"• <b>{l.get('name','')}</b> — {l.get('description','')[:140]}")

        # Spellcasting (very abbreviated)
        sc = getattr(m, "spellcasting", []) or []
        if sc:
            parts.append("<b>Spellcasting</b>")
            for entry in sc[:2]:
                header = entry.get("header", "")
                if header:
                    parts.append(f"• {header[:200]}")

        return "<br>".join(parts)

    def _load_monster_image(self, definition) -> None:
        """Try to load a monster token using the real 5eTools path conventions.

        5eTools stores tokens at:
            img/bestiary/tokens/<SOURCE>/<SanitizedName>.webp
        (with .png fallbacks for user-provided files)
        """
        self._clear_image()

        candidates: list[Path] = []

        name = getattr(definition, "name", "") or ""
        source = getattr(definition, "source", "") or ""
        mid = getattr(definition, "id", "") or ""
        stored_path = getattr(definition, "image_path", None)

        # 1. Respect any explicit path we stored during import (under data/images/)
        if stored_path:
            candidates.append(Path("data/images") / stored_path)
            # Also try .webp variant
            if stored_path.endswith(".png"):
                candidates.append(Path("data/images") / stored_path.replace(".png", ".webp"))

        # Sanitized name used by 5eTools
        def sanitize(n: str) -> str:
            return (
                n.replace(" ", "_")
                 .replace("'", "")
                 .replace("/", "-")
                 .replace(":", "")
                 .replace("?", "")
                 .replace("!", "")
                 .replace(",", "")
            )

        slug = sanitize(name)
        src = source.upper() if source else ""

        # 2. Most accurate 5eTools-style paths (what the real site uses)
        # Primary location when user clones 5etools-img
        img_root = Path("data/5etools-img/img")

        if src:
            candidates.append(img_root / "bestiary/tokens" / src / f"{slug}.webp")
            candidates.append(img_root / "bestiary/tokens" / src / f"{slug}.png")
        candidates.append(img_root / "bestiary/tokens" / f"{slug}.webp")
        candidates.append(img_root / "bestiary/tokens" / f"{slug}.png")

        # 3. User-friendly flat location under data/images/
        images_root = Path("data/images/bestiary/tokens")
        if src:
            candidates.append(images_root / src / f"{slug}.webp")
            candidates.append(images_root / src / f"{slug}.png")
        candidates.append(images_root / f"{slug}.webp")
        candidates.append(images_root / f"{slug}.png")

        # Also try id-based names
        if mid and mid != slug:
            candidates.append(images_root / f"{mid}.png")
            candidates.append(images_root / f"{mid}.webp")

        # Try all candidates
        for candidate in candidates:
            if candidate.exists():
                pix = QPixmap(str(candidate))
                if not pix.isNull():
                    scaled = pix.scaled(
                        140, 140,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._image_label.setPixmap(scaled)
                    self._image_label.setToolTip(str(candidate))
                    return

        # Nothing found
        self._image_label.setText("no token")

    def _clear_image(self) -> None:
        self._image_label.clear()
        self._image_label.setText("no token")
        self._image_label.setToolTip("")
