"""
MonsterImageManager

Handles on-demand downloading of monster tokens from the 5eTools image mirror,
with local caching. Designed to be used from Qt UI code.

Usage:
    manager = MonsterImageManager()
    manager.image_ready.connect(self._on_image_ready)
    manager.request_image(monster_definition)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QObject, QThread, Signal, Slot

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition


class _DownloadWorker(QObject):
    """Worker that runs in a background thread to download a single image."""

    finished = Signal(str, Path)      # monster_id, local_path
    failed = Signal(str, str)         # monster_id, error_message

    BASE_URL = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-img/main/img"

    def __init__(self, definition: MonsterDefinition, target_dir: Path):
        super().__init__()
        self.definition = definition
        self.target_dir = target_dir

    @Slot()
    def run(self):
        try:
            urls = self._build_candidate_urls()
            local_path = self._determine_local_path()

            for url in urls:
                try:
                    resp = requests.get(url, timeout=12)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        local_path.parent.mkdir(parents=True, exist_ok=True)
                        local_path.write_bytes(resp.content)
                        self.finished.emit(self.definition.id, local_path)
                        return
                except requests.RequestException:
                    continue

            self.failed.emit(self.definition.id, "Could not find a matching token on the mirror.")

        except Exception as e:
            self.failed.emit(self.definition.id, str(e))

    def _sanitize_name(self, name: str) -> str:
        """Rough approximation of 5eTools nameToTokenName."""
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"\s+", "_", name.strip())
        return name

    def _build_candidate_urls(self) -> list[str]:
        """Return likely raw GitHub URLs for this monster."""
        urls: list[str] = []
        name = self.definition.name
        source = getattr(self.definition, "source", "") or ""
        sanitized = self._sanitize_name(name)

        # Primary pattern used by 5eTools
        if source:
            urls.append(f"{self.BASE_URL}/bestiary/tokens/{source}/{sanitized}.webp")
            urls.append(f"{self.BASE_URL}/bestiary/tokens/{source}/{sanitized}.png")

        # Fallback without source folder
        urls.append(f"{self.BASE_URL}/bestiary/tokens/{sanitized}.webp")
        urls.append(f"{self.BASE_URL}/bestiary/tokens/{sanitized}.png")

        # Also try the image_path we stored during import if it looks like a relative path
        stored = getattr(self.definition, "image_path", None)
        if stored:
            # Convert our stored relative path into a possible raw URL
            clean = stored.replace("bestiary/tokens/", "").lstrip("/")
            urls.append(f"{self.BASE_URL}/bestiary/tokens/{clean}")

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)
        return unique_urls

    def _determine_local_path(self) -> Path:
        """Decide where we will save the downloaded file."""
        name = self.definition.name
        source = getattr(self.definition, "source", "") or ""
        sanitized = self._sanitize_name(name)

        target = self.target_dir
        if source:
            target = target / source

        # Prefer webp if we can, but we'll save whatever we actually download
        return target / f"{sanitized}.webp"


class MonsterImageManager(QObject):
    """
    High-level manager for monster images.

    - Checks local cache first
    - Triggers background download when needed
    - Emits signals when an image becomes available
    """

    image_ready = Signal(str, Path)   # monster_id, path to local image
    image_failed = Signal(str, str)   # monster_id, error message

    def __init__(self, images_root: Optional[Path] = None, parent: QObject | None = None):
        super().__init__(parent)
        self.images_root = images_root or (Path.cwd() / "data" / "images" / "bestiary" / "tokens")
        self._active_threads: dict[str, QThread] = {}   # monster_id -> thread

    def get_local_image(self, definition: MonsterDefinition) -> Optional[Path]:
        """Synchronous check for a locally cached image."""
        candidates = self._build_local_candidates(definition)
        for path in candidates:
            if path.exists() and path.stat().st_size > 500:
                return path
        return None

    def request_image(self, definition: MonsterDefinition):
        """
        Request an image for the given monster.

        - If already local → emit image_ready immediately
        - If download already in progress → do nothing
        - Otherwise start a background download
        """
        monster_id = definition.id

        # 1. Check local first
        local = self.get_local_image(definition)
        if local:
            self.image_ready.emit(monster_id, local)
            return

        # 2. Don't start duplicate downloads
        if monster_id in self._active_threads:
            return

        # 3. Only attempt download if the monster is known to have a token
        if not getattr(definition, "has_token", False):
            self.image_failed.emit(monster_id, "No official token available.")
            return

        # 4. Start background download
        self._start_download(definition)

    def _start_download(self, definition: MonsterDefinition):
        thread = QThread()
        worker = _DownloadWorker(definition, self.images_root)
        worker.moveToThread(thread)

        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_download_finished)
        worker.failed.connect(self._on_download_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

        self._active_threads[definition.id] = thread
        thread.start()

    @Slot(str, Path)
    def _on_download_finished(self, monster_id: str, path: Path):
        if monster_id in self._active_threads:
            del self._active_threads[monster_id]
        self.image_ready.emit(monster_id, path)

    @Slot(str, str)
    def _on_download_failed(self, monster_id: str, error: str):
        if monster_id in self._active_threads:
            del self._active_threads[monster_id]
        self.image_failed.emit(monster_id, error)

    def _build_local_candidates(self, definition: MonsterDefinition) -> list[Path]:
        """Return possible local file paths for this monster."""
        candidates: list[Path] = []
        name = definition.name
        source = getattr(definition, "source", "") or ""
        sanitized = re.sub(r"[^\w\s-]", "", name).replace(" ", "_").strip("_")

        base = self.images_root

        if source:
            candidates.append(base / source / f"{sanitized}.webp")
            candidates.append(base / source / f"{sanitized}.png")

        candidates.append(base / f"{sanitized}.webp")
        candidates.append(base / f"{sanitized}.png")

        # Also respect the image_path stored at import time
        stored = getattr(definition, "image_path", None)
        if stored:
            candidates.append(base.parent.parent / stored)   # relative to data/images/

        return candidates