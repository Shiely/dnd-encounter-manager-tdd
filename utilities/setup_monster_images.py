#!/usr/bin/env python3
"""
Monster Image Setup Helper

Run this after cloning the repository to prepare the local directory structure
for monster tokens and portraits.

Usage:
    uv run python utilities/setup_monster_images.py
    uv run python utilities/setup_monster_images.py --stats
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_image_directories() -> Path:
    """Create the standard image directory structure."""
    root = get_project_root()
    tokens_dir = root / "data" / "images" / "bestiary" / "tokens"
    tokens_dir.mkdir(parents=True, exist_ok=True)

    # Also create a source-based example folder (common pattern)
    (tokens_dir / "MM").mkdir(exist_ok=True)
    (tokens_dir / "MTF").mkdir(exist_ok=True)
    (tokens_dir / "VGM").mkdir(exist_ok=True)

    # Keep the directory in git even when empty
    (tokens_dir / ".gitkeep").touch(exist_ok=True)

    return tokens_dir


def load_bestiary() -> list[dict[str, Any]]:
    root = get_project_root()
    bestiary_path = root / "data" / "srd" / "monsters.json"

    if not bestiary_path.exists():
        print(f"[WARN] Could not find {bestiary_path}")
        return []

    with open(bestiary_path, encoding="utf-8") as f:
        return json.load(f)


def print_stats(monsters: list[dict[str, Any]]) -> None:
    total = len(monsters)
    with_token = sum(1 for m in monsters if m.get("has_token"))
    with_fluff = sum(1 for m in monsters if m.get("has_fluff_image"))
    with_any = sum(1 for m in monsters if m.get("has_token") or m.get("has_fluff_image"))

    print("\n=== Monster Image Statistics ===")
    print(f"Total monsters in bestiary: {total}")
    print(f"Have official token (has_token): {with_token}")
    print(f"Have fluff art (has_fluff_image): {with_fluff}")
    print(f"Have any official image data: {with_any}")
    print(f"Percentage with image data: {with_any / total * 100:.1f}%" if total else "N/A")


def create_guidance_readme(tokens_dir: Path) -> None:
    """Write a helpful README inside the tokens folder."""
    readme_path = tokens_dir / "README.md"

    content = """# Monster Tokens & Portraits

This folder is where the D&D Encounter Manager looks for monster images.

## Supported Locations (in search order)

1. `data/images/bestiary/tokens/<SOURCE>/<Monster_Name>.webp`   (preferred)
2. `data/images/bestiary/tokens/<Monster_Name>.webp`
3. `data/images/bestiary/tokens/<Monster_Name>.png`
4. `data/5etools-img/img/bestiary/tokens/<SOURCE>/<Monster_Name>.webp`  (if cloned)

Examples:
- `data/images/bestiary/tokens/MM/Ancient_Red_Dragon.webp`
- `data/images/bestiary/tokens/Ancient_Red_Dragon.png`

## How to Add Images (Practical Options)

### Option A — On-demand (Recommended for most users)
1. Run this script: `uv run python utilities/setup_monster_images.py`
2. When you encounter a monster you like in the app, note its name.
3. Download the token from:
   - The 5e.tools website (inspect element on the bestiary)
   - Or the 5eTools image mirror: https://github.com/5etools-mirror-3/5etools-img
4. Save it with the correct filename in this folder (or a source subfolder).

### Option B — Full mirror (large)
```bash
git clone --depth 1 https://github.com/5etools-mirror-3/5etools-img.git ../../5etools-img
```
The app will automatically find tokens under `5etools-img/img/bestiary/tokens/`.

## Naming Rules
- Replace spaces with underscores (`Ancient Red Dragon` → `Ancient_Red_Dragon`)
- Remove most special characters (`'`, `/`, `:`, `?`, `!`)
- Use `.webp` for original 5eTools files, `.png` works fine too.

The StatBlockPanel will automatically display any image it finds for the currently selected monster.
"""

    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] Created guidance: {readme_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare monster image directories and show stats.")
    parser.add_argument("--stats", action="store_true", help="Only show image statistics")
    args = parser.parse_args()

    tokens_dir = ensure_image_directories()
    print(f"[OK] Image directory ready: {tokens_dir}")

    monsters = load_bestiary()
    if not monsters:
        return

    if args.stats:
        print_stats(monsters)
        return

    print_stats(monsters)
    create_guidance_readme(tokens_dir)

    print("\nYou're all set!")
    print("Place token images in the folder above following the naming rules.")
    print("Restart the app and select a monster — the token should appear automatically if found.")


if __name__ == "__main__":
    main()