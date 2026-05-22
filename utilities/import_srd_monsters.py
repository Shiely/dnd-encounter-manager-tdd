#!/usr/bin/env python3
"""
SRD Monster Importer for D&D Encounter Manager

Clones the 5eTools data repository and converts bestiary JSON
into the format expected by this application.

Usage:
    python utilities/import_srd_monsters.py

Output:
    data/srd/monsters.json
"""

import json
import subprocess
from pathlib import Path
from typing import Any

REPO_URL = "https://github.com/5etools-mirror/5etools-src.git"
REPO_DIR = Path("data/5etools-src")
OUTPUT_DIR = Path("data/srd")
OUTPUT_FILE = OUTPUT_DIR / "monsters.json"


def clone_5etools_repo() -> None:
    if REPO_DIR.exists():
        print(f"[INFO] 5eTools repo already exists at {REPO_DIR}")
        return

    print("[INFO] Cloning 5eTools repository (this may take a minute)...")
    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(REPO_DIR)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("[SUCCESS] Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to clone repository: {e.stderr}")
        raise


def convert_ability_scores(abil: dict[str, Any]) -> dict[str, int]:
    return {
        "str_": abil.get("str", 10),
        "dex": abil.get("dex", 10),
        "con": abil.get("con", 10),
        "int_": abil.get("int", 10),
        "wis": abil.get("wis", 10),
        "cha": abil.get("cha", 10),
    }


def convert_speed(speed: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(speed, dict):
        speed = {}
    return {
        "walk": int(speed.get("walk", 30)) if isinstance(speed.get("walk"), (int, str)) else 30,
        "fly": int(speed.get("fly", 0)) if isinstance(speed.get("fly"), (int, str)) else 0,
        "swim": int(speed.get("swim", 0)) if isinstance(speed.get("swim"), (int, str)) else 0,
        "climb": int(speed.get("climb", 0)) if isinstance(speed.get("climb"), (int, str)) else 0,
        "burrow": int(speed.get("burrow", 0)) if isinstance(speed.get("burrow"), (int, str)) else 0,
        "hover": bool(speed.get("hover", False)),
    }


def convert_action_entry(action: dict[str, Any]) -> dict[str, Any]:
    entries = action.get("entries", [])
    description = " ".join(str(e) for e in entries) if entries else ""

    return {
        "name": action.get("name", "Unknown Action"),
        "description": description[:500],  # truncate long descriptions
        "attack_bonus": action.get("attackBonus"),
        "damage": None,
        "damage_type": None,
    }


def convert_monster(monster: dict[str, Any]) -> dict[str, Any] | None:
    try:
        name = monster.get("name", "Unknown")
        monster_id = name.lower().replace(" ", "-").replace("'", "")

        # Handle CR that can be string or dict
        cr = monster.get("cr")
        if isinstance(cr, dict):
            cr_value = cr.get("cr", "0")
        else:
            cr_value = str(cr) if cr else "0"

        return {
            "id": monster_id,
            "name": name,
            "size": monster.get("size", ["Medium"])[0] if isinstance(monster.get("size"), list) else monster.get("size", "Medium"),
            "type_": monster.get("type", "unknown"),
            "alignment": ", ".join(monster.get("alignment", [])) if isinstance(monster.get("alignment"), list) else str(monster.get("alignment", "unaligned")),
            "armor_class": monster.get("ac", [{}])[0].get("ac", 10) if monster.get("ac") else 10,
            "hit_points": monster.get("hp", {}).get("average", 10),
            "hit_dice": monster.get("hp", {}).get("formula", "1d8"),
            "speed": convert_speed(monster.get("speed", {})),
            "ability_scores": convert_ability_scores(monster.get("ability", {})),
            "challenge_rating": {"value": cr_value},
            "xp": monster.get("xp", 0),
            "actions": [convert_action_entry(a) for a in monster.get("action", []) or []],
            "bonus_actions": [convert_action_entry(a) for a in monster.get("bonus", []) or []],
            "reactions": [convert_action_entry(a) for a in monster.get("reaction", []) or []],
            "legendary_actions": [convert_action_entry(a) for a in monster.get("legendary", []) or []],
            "special_abilities": [convert_action_entry(a) for a in monster.get("trait", []) or []],
            "senses": {
                "darkvision": 0,
                "blindsight": 0,
                "tremorsense": 0,
                "truesight": 0,
                "passive_perception": monster.get("passive", 10),
            },
            "source": monster.get("source", "SRD"),
        }
    except Exception as e:
        print(f"[WARN] Skipping monster '{monster.get('name')}': {e}")
        return None


def main() -> None:
    print("=== SRD Monster Importer ===\n")
    clone_5etools_repo()

    bestiary_dir = REPO_DIR / "data" / "bestiary"
    if not bestiary_dir.exists():
        print(f"[ERROR] Bestiary directory not found at {bestiary_dir}")
        return

    all_monsters: list[dict] = []

    # Process main bestiary files
    for json_file in sorted(bestiary_dir.glob("bestiary-*.json")):
        print(f"[INFO] Processing {json_file.name}...")
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            for monster in data.get("monster", []):
                converted = convert_monster(monster)
                if converted:
                    all_monsters.append(converted)
        except Exception as e:
            print(f"[WARN] Failed to process {json_file.name}: {e}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_monsters, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Converted {len(all_monsters)} monsters.")
    print(f"[SUCCESS] Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
