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
import urllib.parse
from pathlib import Path

import requests
from PySide6.QtCore import QObject, QThread, Signal, Slot

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition


class _DownloadWorker(QObject):
    """Worker that runs in a background thread to download a single image."""

    finished = Signal(str, Path)      # monster_id, local_path
    failed = Signal(str, str)         # monster_id, error_message

    MIRROR_BASE = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-img/main/img/bestiary/tokens"
    OFFICIAL_BASE = "https://5e.tools/img/bestiary/tokens"

    def __init__(self, definition: MonsterDefinition, target_dir: Path):
        super().__init__()
        self.definition = definition
        self.target_dir = target_dir

    @Slot()
    def run(self):
        try:
            urls = self._build_candidate_urls()
            name = self.definition.name
            source = getattr(self.definition, "source", "") or ""
            sanitized = self._sanitize_name(name)

            for url in urls:
                try:
                    resp = requests.get(url, timeout=12)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        # Save using the actual extension from the URL that worked (webp or png)
                        ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".png"
                        if ext not in (".png", ".webp", ".jpg", ".jpeg"):
                            ext = ".png"
                        target = self.target_dir
                        if source:
                            target = target / source
                        target.mkdir(parents=True, exist_ok=True)
                        local_path = target / f"{sanitized}{ext}"
                        local_path.write_bytes(resp.content)
                        print(f"[MonsterImage] SUCCESS downloaded {len(resp.content)} bytes for {name} from {url} -> {local_path}")
                        self.finished.emit(self.definition.id, local_path)
                        return
                except requests.RequestException:
                    continue

            err = "Could not download any matching token (tried 5e.tools + mirror, underscore + %20 names)."
            print(f"[MonsterImage] FAILED for {name}: {err}")
            self.failed.emit(self.definition.id, err)

        except Exception as e:
            print(f"[MonsterImage] EXCEPTION for {self.definition.name}: {e}")
            self.failed.emit(self.definition.id, str(e))

    def _sanitize_name(self, name: str) -> str:
        """Rough approximation of 5eTools nameToTokenName."""
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"\s+", "_", name.strip())
        return name

    def _build_candidate_urls(self) -> list[str]:
        """Build a list of likely token URLs, trying both the GitHub mirror
        and the official 5e.tools site (with both underscore and %20 names)."""
        import urllib.parse

        urls: list[str] = []
        name = self.definition.name
        source = getattr(self.definition, "source", "") or ""
        sanitized = self._sanitize_name(name)                    # Ancient_Red_Dragon
        encoded = urllib.parse.quote(name)                       # Ancient%20Red%20Dragon

        # GitHub mirror (prefers underscore)
        if source:
            urls.append(f"{self.MIRROR_BASE}/{source}/{sanitized}.webp")
            urls.append(f"{self.MIRROR_BASE}/{source}/{sanitized}.png")
        urls.append(f"{self.MIRROR_BASE}/{sanitized}.webp")
        urls.append(f"{self.MIRROR_BASE}/{sanitized}.png")

        # Official 5e.tools site - try both naming styles
        name_variants = [sanitized, encoded]
        for variant in name_variants:
            if source:
                urls.append(f"{self.OFFICIAL_BASE}/{source}/{variant}.webp")
                urls.append(f"{self.OFFICIAL_BASE}/{source}/{variant}.png")
            urls.append(f"{self.OFFICIAL_BASE}/{variant}.webp")
            urls.append(f"{self.OFFICIAL_BASE}/{variant}.png")

        # Also try the stored image_path from import
        stored = getattr(self.definition, "image_path", None)
        if stored:
            filename = Path(stored.replace("bestiary/tokens/", "")).name
            urls.append(f"{self.MIRROR_BASE}/{filename}")
            urls.append(f"{self.OFFICIAL_BASE}/{filename}")

        # Deduplicate
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

    def __init__(self, images_root: Path | None = None, parent: QObject | None = None):
        super().__init__(parent)
        if images_root is not None:
            self.images_root = images_root
        else:
            self.images_root = self._discover_images_root()
        self._active_threads: dict[str, QThread] = {}     # monster_id -> QThread
        self._active_workers: dict[str, _DownloadWorker] = {}  # keep strong ref so Python GC doesn't kill the worker before it finishes
        print(f"[MonsterImageManager] Using images root: {self.images_root}")

    @staticmethod
    def _discover_images_root() -> Path:
        """Find a writable data/images/bestiary/tokens directory using the same
        multi-candidate strategy that SrdMonsterRepository uses for monsters.json.
        This guarantees that when the test utility writes a token, the running
        app will see it even if launched via different cwd / entry points.
        """
        candidates: list[Path] = []

        # 1. Relative to this source file (best when running from a git checkout)
        try:
            here = Path(__file__).resolve()
            for up in range(6):
                root = here.parents[up]
                cand = root / "data" / "images" / "bestiary" / "tokens"
                candidates.append(cand)
                candidates.append(root / "src" / "data" / "images" / "bestiary" / "tokens")
        except Exception:
            pass

        # 2. Current working directory and a few parents (covers uv run, python -m, etc.)
        try:
            cwd = Path.cwd().resolve()
            candidates.append(cwd / "data" / "images" / "bestiary" / "tokens")
            candidates.append(cwd.parent / "data" / "images" / "bestiary" / "tokens")
            candidates.append(cwd.parent.parent / "data" / "images" / "bestiary" / "tokens")
        except Exception:
            pass

        # 3. If we can locate the SRD monsters.json, put the images next to it
        try:
            srd_candidates = [
                Path.cwd() / "data" / "srd" / "monsters.json",
                Path(__file__).resolve().parents[4] / "data" / "srd" / "monsters.json",
            ]
            for srd in srd_candidates:
                if srd.exists():
                    images = srd.parent.parent / "images" / "bestiary" / "tokens"
                    candidates.append(images)
                    break
        except Exception:
            pass

        # Pick the first one that already exists and looks plausible
        for cand in candidates:
            if cand.exists():
                if (cand / "MM").exists() or cand.parent.exists() or any(cand.glob("**/*.webp")) or any(cand.glob("**/*.png")):
                    return cand
                if cand.is_dir():
                    return cand

        # Nothing existed — return the most likely place so first download lands
        # in the exact same directory the utility would have used.
        best = candidates[0] if candidates else (Path.cwd() / "data" / "images" / "bestiary" / "tokens")
        return best

    def get_local_image(self, definition: MonsterDefinition) -> Path | None:
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
        print(f"[MonsterImageManager] Starting background download for {getattr(definition, 'name', definition.id)} (has_token=True, not local yet)")
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

        # Safe cleanup: only drop the QThread after it has truly stopped.
        # This prevents "QThread destroyed while still running" crashes.
        thread.finished.connect(lambda tid=definition.id: self._cleanup_finished_thread(tid))
        thread.finished.connect(thread.deleteLater)

        self._active_threads[definition.id] = thread
        self._active_workers[definition.id] = worker   # prevent Python GC from killing the worker too early
        thread.start()

    @Slot(str, Path)
    def _on_download_finished(self, monster_id: str, path: Path):
        # Keep the thread reference until the thread actually stops (see _cleanup_finished_thread)
        self._active_workers.pop(monster_id, None)
        self.image_ready.emit(monster_id, path)

    @Slot(str, str)
    def _on_download_failed(self, monster_id: str, error: str):
        self._active_workers.pop(monster_id, None)
        self.image_failed.emit(monster_id, error)

    def _cleanup_finished_thread(self, monster_id: str):
        """Called from thread.finished signal — safe moment to drop the QThread."""
        self._active_threads.pop(monster_id, None)
        # The worker was already removed when it emitted finished/failed

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