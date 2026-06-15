from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from dnd_encounter.utils.monster_image_manager import MonsterImageManager
from dnd_encounter.adapters.inbound.desktop_ui.monster_stat_block_renderer import MonsterStatBlockRenderer

import re

# Use canonical DTO from application layer (self-heal for consistency with Sidebar)
try:
    from dnd_encounter.application.dto.encounter_dto import EncounterStateDTO, EntityRowDTO
except ImportError:
    from .initiative_list_model import EncounterStateDTO  # type: ignore fallback


class StatBlockPanel(QScrollArea):
    """Right-hand panel showing live stat block for selected entity.

    Displays current_hp and active conditions from the EntityRowDTO
    (live state), not from static monster definition.
    """

    hp_adjusted = Signal(str, int)  # (instance_id, delta)
    hp_set = Signal(str, int)       # (instance_id, absolute_new_hp) for direct set

    def __init__(self, parent: QWidget | None = None, monster_repo=None, images_root: Path | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatBlockPanel")
        self.setWidgetResizable(True)
        # Allow the panel to expand vertically to use available space in the main window
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._monster_repo = monster_repo   # optional – used for rich monster details

        # On-demand monster token downloader (polished background fetching + caching)
        self._image_manager = MonsterImageManager(images_root=images_root)
        self._image_manager.image_ready.connect(self._on_image_ready)
        self._image_manager.image_failed.connect(self._on_image_failed)
        self._current_monster_id_for_image: str | None = None
        self._current_definition_for_image = None   # last MonsterDefinition we tried to show an image for

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

        # Use QTextBrowser instead of QLabel so users can highlight and copy
        # text from the rich stat block (very useful for debugging data issues).
        self._content = QTextBrowser()
        self._content.setOpenExternalLinks(False)
        self._content.setStyleSheet("font-size: 13px; line-height: 1.35;")
        # Allow the rich text area to expand and use available vertical space
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        # Removed final addStretch() so the panel can use more vertical space
        # when the parent layout gives it extra room (reduces unnecessary scrolling).

        self._current_instance_id: str | None = None

    @Slot()
    def refresh(self, state: EncounterStateDTO | None, instance_id: str | None = None) -> None:
        if state is None or instance_id is None:
            self._title.setText("No entity selected")
            self._content.setHtml("")
            self._current_instance_id = None
            self._clear_token_image_only()
            return

        entity = None
        for e in getattr(state, "entities", []):
            if getattr(e, "instance_id", None) == instance_id:
                entity = e
                break

        if entity is None:
            self._title.setText("Entity not found")
            self._content.setHtml("")
            self._clear_token_image_only()
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

        # Phase 4: render core combat stats (AC, Speed, CR) from enriched EntityRowDTO (or repo path) in clean scannable format
        # alongside existing live HP/conditions/title/token. Uses "•" per spec example for glance value.
        # This is the minimal update to refresh (delegated renderer keeps full rich after <hr>).
        # Phase 5: extend glance additively with XP (keeps P4 line co-present and unchanged for protected strings; "AC ... • CR ... • XP N").
        ac = getattr(entity, "ac", None)
        spd = getattr(entity, "speed", None)
        crv = getattr(entity, "cr", None)
        xp = getattr(entity, "xp", None)
        if ac is not None or spd or crv or xp is not None:
            core_parts = []
            if ac is not None:
                core_parts.append(f"AC {ac}")
            if spd:
                core_parts.append(f"Speed {spd}")
            if crv:
                core_parts.append(f"CR {crv}")
            if xp is not None:
                core_parts.append(f"XP {xp}")
            if core_parts:
                lines.append(" • ".join(core_parts))

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

        basic_html = "<br>".join(lines)

        # Always start with basic info. Enrichment will rebuild the full content.
        self._set_full_content(basic_html)

        # --- Try to enrich with full monster definition (new rich data) ---
        self._try_enrich_with_definition(entity, basic_html)

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

    def _try_enrich_with_definition(self, entity, basic_html: str = "") -> None:
        """If we have a monster_repo and this is a monster, fetch the full definition and show rich data + image.

        Uses safe one-shot HTML composition via _set_full_content().
        Never wipes the main text content on failure paths.
        """
        if not self._monster_repo or not entity:
            self._clear_token_image_only()
            return
        if getattr(entity, "entity_type", "monster") != "monster":
            self._clear_token_image_only()
            return

        monster_id = getattr(entity, "monster_id", None)
        if not monster_id:
            self._clear_token_image_only()
            return

        try:
            definition = self._monster_repo.get(monster_id)
            if definition:
                if not hasattr(self, "_renderer"):
                    self._renderer = MonsterStatBlockRenderer()

                current_hp = getattr(entity, "current_hp", None)
                max_hp = getattr(entity, "max_hp", None)

                rich_html = self._renderer.render(
                    definition,
                    current_hp=current_hp,
                    max_hp=max_hp,
                )

                if rich_html:
                    self._set_full_content(basic_html, rich_html)
                else:
                    self._set_full_content(basic_html)

                self._load_monster_image(definition)
            else:
                self._clear_token_image_only()
        except Exception:
            # On any error, ensure we at least keep the basic info
            if basic_html:
                self._set_full_content(basic_html)
            self._clear_token_image_only()

    # _build_rich_monster_html has been fully extracted to MonsterStatBlockRenderer.
    # The old method body has been removed.

    def _load_monster_image(self, definition) -> None:
        """
        Polished image loading with on-demand download support.

        - Shows local image immediately if present
        - Shows "Downloading token..." + triggers background download if the monster has official art
        """
        self._current_monster_id_for_image = getattr(definition, "id", None)
        self._current_definition_for_image = definition

        local_path = self._image_manager.get_local_image(definition)
        if local_path:
            self._display_image(local_path)
            return

        if getattr(definition, "has_token", False):
            self._image_label.setText("Downloading\n token...")
            self._image_label.setToolTip("Fetching token from 5e.tools (official) in background. This takes 1-3s on first view.")
            self._image_manager.request_image(definition)
        else:
            # Do not wipe text content here.
            self._image_label.clear()
            self._image_label.setText("no token")
            self._image_label.setToolTip("")

    def _clear_token_image_only(self) -> None:
        """Only clear the token image area. Never wipe the main stat text content."""
        self._image_label.clear()
        self._image_label.setText("no token")
        self._image_label.setToolTip("")
        self._current_monster_id_for_image = None
        self._current_definition_for_image = None

    def _set_full_content(self, basic_html: str, rich_html: str | None = None) -> None:
        """Safely set the complete content of the stat block in one operation.

        This is the preferred way to update the QTextBrowser to avoid
        incremental HTML concatenation bugs and partial state issues.
        """
        if not basic_html:
            basic_html = ""

        if rich_html:
            full_html = basic_html + "<hr>" + rich_html
        else:
            full_html = basic_html

        self._content.setHtml(full_html)

    def _display_image(self, path: Path) -> None:
        """Load and display the token image, with robust fallback for webp/png and plugin edge cases."""
        self._image_label.setText("")  # ensure we are in pixmap mode, not text mode
        pix = QPixmap(str(path))
        if pix.isNull():
            # More explicit loader with auto-detect (helps when extension != actual format or partial plugin support)
            try:
                from PySide6.QtGui import QImageReader
                reader = QImageReader(str(path))
                reader.setAutoDetectImageFormat(True)
                image = reader.read()
                if not image.isNull():
                    pix = QPixmap.fromImage(image)
            except Exception:
                pass
        if not pix.isNull():
            scaled = pix.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._image_label.setPixmap(scaled)
            self._image_label.setToolTip(str(path))
            self._image_label.update()
            self.update()  # ensure the scroll area / parent also repaints
        else:
            self._image_label.setText("Image\nerror")
            self._image_label.setToolTip(f"Could not load token image at {path} (webp support?)")

    @Slot(str, Path)
    def _on_image_ready(self, monster_id: str, path: Path):
        """Called when a background download finishes successfully (for any monster).

        If this is the monster we are currently viewing, display it.
        Otherwise, opportunistically check whether the monster we *are* currently
        viewing now has a local file (it may have been the one that just landed).
        This makes "add several monsters at once" work reliably.
        """
        if monster_id == self._current_monster_id_for_image:
            self._display_image(path)
            return

        # Any download finishing is an opportunity to see if the currently
        # selected monster's token has become available.
        if self._current_definition_for_image is not None:
            local = self._image_manager.get_local_image(self._current_definition_for_image)
            if local:
                self._display_image(local)

    @Slot(str, str)
    def _on_image_failed(self, monster_id: str, error: str):
        """Called when background download fails."""
        if monster_id == self._current_monster_id_for_image:
            self._image_label.clear()
            self._image_label.setText("Download\nfailed")
            self._image_label.setToolTip(f"Could not download token: {error}")

    # ------------------------------------------------------------------
    # Proactive preloading for the whole encounter (so every added monster
    # starts downloading its token even if it is not currently selected)
    # ------------------------------------------------------------------

    def preload_images_for_state(self, state) -> None:
        """Kick off background token downloads for every monster currently
        in the encounter that has has_token=True. This makes 'add a bunch of
        monsters then browse them' work without having to click each one first.
        """
        if not self._monster_repo or not state:
            return
        entities = getattr(state, "entities", []) or []
        for e in entities:
            if getattr(e, "entity_type", None) != "monster":
                continue
            mid = getattr(e, "monster_id", None)
            if not mid:
                continue
            try:
                definition = self._monster_repo.get(mid)
                if definition and getattr(definition, "has_token", False):
                    # request_image is idempotent (checks local + active threads)
                    self._image_manager.request_image(definition)
            except Exception:
                pass  # never let preloading break the UI
