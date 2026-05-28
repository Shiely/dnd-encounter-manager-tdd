#!/usr/bin/env python3
"""
Full Bestiary Importer with MPMM Priority

This script processes the full set of 5eTools bestiary sources and produces
a large, high-quality monsters.json.

Priority order (later sources override earlier ones):
- All older sources (VGM, MM, etc.)
- MPMM last (so updated MPMM versions take priority)

This gives us the best of both worlds:
- Broad coverage (~4400+ monsters)
- Best available stat blocks (MPMM where they exist)

Usage:
    uv run python utilities/import_full_bestiary.py

Output:
    data/srd/monsters.json
"""

import json
from pathlib import Path
from typing import Any, Callable

from import_srd_monsters import (
    clone_5etools_repo,
    convert_monster as convert_vgm_style,
    render_entries,
    _strip_5etools_tags,
)

from import_mpmm_monsters import (
    convert_monster_mpmm,
    convert_spellcasting_mpmm,
    convert_reactions,
)

REPO_DIR = Path("data/5etools-src")
BESTIARY_DIR = REPO_DIR / "data" / "bestiary"
OUTPUT_FILE = Path("data/srd/monsters.json")


# Automatically load all bestiary-*.json files.
# MPMM is loaded last so its versions override older sources.
all_bestiary_files = sorted(BESTIARY_DIR.glob("bestiary-*.json"))

# Move MPMM to the end if present
mpmm_file = BESTIARY_DIR / "bestiary-mpmm.json"
if mpmm_file in all_bestiary_files:
    all_bestiary_files.remove(mpmm_file)
    all_bestiary_files.append(mpmm_file)

SOURCE_PRIORITY = []
for path in all_bestiary_files:
    source_name = path.stem.replace("bestiary-", "").upper()
    converter = convert_monster_mpmm if path.name == "bestiary-mpmm.json" else convert_vgm_style
    SOURCE_PRIORITY.append((path.name, source_name, converter))


def load_bestiary_monsters(filename: str) -> list[dict[str, Any]]:
    """Load monsters from a specific bestiary JSON file."""
    path = BESTIARY_DIR / filename
    if not path.exists():
        print(f"[WARN] Bestiary file not found: {path}")
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("monster", [])


def convert_monster(monster: dict[str, Any], converter: Callable) -> dict[str, Any] | None:
    """Wrapper to call the appropriate converter function."""
    try:
        return converter(monster)
    except Exception as e:
        name = monster.get("name", "Unknown")
        print(f"[WARN] Failed to convert '{name}': {e}")
        return None


def main() -> None:
    print("=== Full Bestiary Importer (with MPMM Priority) ===\n")

    clone_5etools_repo()

    all_monsters: dict[str, dict[str, Any]] = {}
    source_stats = {}

    for filename, source_name, converter in SOURCE_PRIORITY:
        print(f"[INFO] Loading {source_name} from {filename}...")
        raw_monsters = load_bestiary_monsters(filename)
        source_stats[source_name] = len(raw_monsters)

        for raw in raw_monsters:
            monster = convert_monster(raw, converter)
            if not monster:
                continue

            mid = monster["id"]

            # Later sources override earlier ones
            if mid in all_monsters:
                print(f"[INFO] Overriding '{monster['name']}' with {source_name} version")

            all_monsters[mid] = monster

    # Sort alphabetically for nicer output
    final_list = sorted(all_monsters.values(), key=lambda m: m["name"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    print("\n=== Import Summary ===")
    for source, count in source_stats.items():
        print(f"  {source}: {count} monsters processed")

    print(f"\n  Total unique monsters after merging: {len(final_list)}")
    print(f"\n[SUCCESS] Full bestiary written to: {OUTPUT_FILE}")
    print("Restart your application to use the updated data.")


if __name__ == "__main__":
    main()
