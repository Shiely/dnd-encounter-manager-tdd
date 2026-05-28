#!/usr/bin/env python3
"""
Combined Monster Importer

This script merges monsters from multiple 5eTools sources.
Priority order (later sources override earlier ones):
1. VGM (Volo's Guide to Monsters) + other older sources
2. MPMM (Mordenkainen Presents: Monsters of the Multiverse) - preferred for updated stat blocks

This gives you the best of both worlds:
- Broad coverage from older books
- Updated and improved stat blocks from MPMM where available

Usage:
    uv run python utilities/import_combined_monsters.py

Output:
    data/srd/monsters.json
"""

import json
from pathlib import Path
from typing import Any

from import_srd_monsters import (
    clone_5etools_repo,
    convert_monster as convert_monster_vgm_style,
    render_entries,
    _strip_5etools_tags,
)

from import_mpmm_monsters import (
    convert_monster_mpmm,
    convert_spellcasting_mpmm,
    convert_reactions,
)

REPO_DIR = Path("data/5etools-src")
OUTPUT_FILE = Path("data/srd/monsters.json")


def load_bestiary(source_file: str) -> list[dict[str, Any]]:
    """Load a bestiary JSON file from the 5eTools repo."""
    path = REPO_DIR / "data" / "bestiary" / source_file
    if not path.exists():
        print(f"[WARN] Bestiary file not found: {path}")
        return []
    
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("monster", [])


def normalize_id(name: str) -> str:
    """Create a consistent monster ID."""
    return name.lower().replace(" ", "-").replace("'", "").replace("/", "-")


def main() -> None:
    print("=== Combined Monster Importer (VGM + MPMM) ===\n")

    clone_5etools_repo()

    # Define source priority (later = higher priority)
    sources = [
        ("bestiary-vgm.json", "VGM", convert_monster_vgm_style),
        ("bestiary-mpmm.json", "MPMM", convert_monster_mpmm),
    ]

    all_monsters: dict[str, dict[str, Any]] = {}
    source_counts = {}

    for filename, source_name, converter in sources:
        print(f"[INFO] Loading {source_name} from {filename}...")
        raw_monsters = load_bestiary(filename)
        source_counts[source_name] = len(raw_monsters)

        for raw in raw_monsters:
            monster = converter(raw)
            if not monster:
                continue

            mid = monster["id"]

            # Later sources override earlier ones
            if mid in all_monsters:
                print(f"[INFO] Overriding '{monster['name']}' with {source_name} version")
            
            all_monsters[mid] = monster

    # Sort by name for nicer output
    final_list = sorted(all_monsters.values(), key=lambda m: m["name"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    print("\n=== Import Summary ===")
    for source, count in source_counts.items():
        print(f"  {source}: {count} monsters loaded")

    print(f"\n  Total unique monsters: {len(final_list)}")
    print(f"\n[SUCCESS] Combined monsters.json written to: {OUTPUT_FILE}")
    print("You can now restart your application to use the updated bestiary.")


if __name__ == "__main__":
    main()
