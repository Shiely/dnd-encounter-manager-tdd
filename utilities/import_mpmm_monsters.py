#!/usr/bin/env python3
"""
MPMM Monster Importer (Mordenkainen Presents: Monsters of the Multiverse)

This is a dedicated converter for the newer MPMM data from 5eTools.
It produces a cleaner monsters.json focused on the updated stat blocks
that include proper Reactions and better-formatted abilities.

Usage:
    uv run python utilities/import_mpmm_monsters.py

Output:
    data/srd/monsters.json   (overwrites the current one with MPMM data)
"""

import json
from pathlib import Path
from typing import Any

# Reuse the existing importer logic where possible
from import_srd_monsters import (
    clone_5etools_repo,
    render_entries,
    _strip_5etools_tags,
    convert_ability_scores,
    convert_speed,
    convert_saving_throws,
    convert_skills,
    convert_defenses,
    convert_languages,
    convert_senses,
)

REPO_DIR = Path("data/5etools-src")
OUTPUT_FILE = Path("data/srd/monsters.json")


def convert_spellcasting_mpmm(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Robust spellcasting converter for MPMM (and many other 5eTools sources).

    Handles multiple shapes seen in the wild:
    - Modern: "spells": {"0": {"spells": [...]}, "1": {"slots": 4, "spells": [...]}, ...}
    - Classic MPMM/SRD: "will": [...], "daily": {"1e": [...], "2e": [...]}, "atWill", "legendary"
    """
    out = []
    for sc in raw or []:
        if not isinstance(sc, dict):
            continue

        header = render_entries(sc.get("headerEntries", []))
        ability = sc.get("ability", "int")

        spells_by_freq: dict[str, Any] = {}

        # 1) Modern per-level "spells" object
        spells_data = sc.get("spells", {})
        if isinstance(spells_data, dict) and spells_data:
            for level_str, level_info in spells_data.items():
                if not isinstance(level_info, dict):
                    continue
                try:
                    level = int(level_str)
                except (ValueError, TypeError):
                    # Sometimes keys are like "1e" inside daily already handled below
                    continue

                spell_list = level_info.get("spells", []) or []
                slots = level_info.get("slots")

                clean_spells = [_strip_5etools_tags(s) for s in spell_list if s]

                if level == 0:
                    spells_by_freq["at_will"] = clean_spells
                else:
                    key = f"level_{level}"
                    entry: dict[str, Any] = {"spells": clean_spells}
                    if slots is not None:
                        entry["slots"] = slots
                    spells_by_freq[key] = entry

        # 2) Classic top-level will / daily / atWill / legendary keys (very common in MPMM)
        for classic_key in ("will", "atWill", "at_will"):
            if classic_key in sc and sc[classic_key]:
                val = sc[classic_key]
                if isinstance(val, list):
                    spells_by_freq["at_will"] = [_strip_5etools_tags(s) for s in val]
                elif isinstance(val, dict):
                    # rare
                    spells_by_freq["at_will"] = [_strip_5etools_tags(s) for s in (val.get("spells") or [])]

        daily = sc.get("daily") or sc.get("Daily")
        if isinstance(daily, dict):
            for freq, spell_list in daily.items():
                if not spell_list:
                    continue
                # Normalize "1e", "2e", "3" etc. -> daily_1, daily_2
                num = "".join(ch for ch in str(freq) if ch.isdigit())
                if num:
                    key = f"daily_{num}"
                else:
                    key = f"daily_{freq}"
                clean = [_strip_5etools_tags(s) for s in (spell_list if isinstance(spell_list, list) else [spell_list])]
                # Merge if the modern path already put something here (shouldn't happen)
                if key in spells_by_freq:
                    existing = spells_by_freq[key]
                    if isinstance(existing, list):
                        spells_by_freq[key] = existing + clean
                    elif isinstance(existing, dict):
                        existing["spells"] = (existing.get("spells") or []) + clean
                else:
                    spells_by_freq[key] = clean

        # Also capture "legendary" spellcasting frequency if present
        leg = sc.get("legendary")
        if isinstance(leg, list) and leg:
            spells_by_freq["legendary"] = [_strip_5etools_tags(s) for s in leg]

        # Fallback: if nothing was captured but there are "spells*" keys at top level, try them
        if not spells_by_freq:
            for k, v in sc.items():
                if str(k).lower().startswith("spells") and v:
                    if isinstance(v, list):
                        spells_by_freq["other"] = [_strip_5etools_tags(s) for s in v]
                    break

        out.append({
            "name": sc.get("name", "Spellcasting"),
            "header": header,
            "ability": ability,
            "spells": spells_by_freq,
        })

    return out


def convert_reactions(raw: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert reactions using the improved entry renderer."""
    result = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or "Reaction"
        desc = render_entries(item.get("entries") or item.get("entry") or "")
        if desc:
            result.append({
                "name": str(name),
                "description": _strip_5etools_tags(desc)
            })
    return result


def convert_monster_mpmm(monster: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a single monster from MPMM data."""
    try:
        name = monster.get("name", "Unknown")
        monster_id = name.lower().replace(" ", "-").replace("'", "").replace("/", "-")

        # CR
        cr = monster.get("cr")
        if isinstance(cr, dict):
            cr_value = cr.get("cr", cr.get("value", "0"))
        else:
            cr_value = str(cr) if cr else "0"

        # AC
        ac = 10
        if isinstance(monster.get("ac"), list) and monster["ac"]:
            first = monster["ac"][0]
            ac = first.get("ac", first) if isinstance(first, dict) else first
        elif isinstance(monster.get("ac"), (int, str)):
            ac = int(monster["ac"])

        # HP
        hp = monster.get("hp", {})
        if isinstance(hp, dict):
            hit_points = hp.get("average", 10)
            hit_dice = hp.get("formula", "1d8")
        else:
            hit_points = int(hp) if hp else 10
            hit_dice = "1d8"

        ability_raw = {
            "str": monster.get("str", 10),
            "dex": monster.get("dex", 10),
            "con": monster.get("con", 10),
            "int": monster.get("int", 10),
            "wis": monster.get("wis", 10),
            "cha": monster.get("cha", 10),
        }

        result = {
            "id": monster_id,
            "name": name,
            "size": monster.get("size", ["Medium"])[0] if isinstance(monster.get("size"), list) else monster.get("size", "Medium"),
            "type_": monster.get("type", "unknown"),
            "alignment": ", ".join(monster.get("alignment", [])) if isinstance(monster.get("alignment"), list) else str(monster.get("alignment", "unaligned")),
            "armor_class": ac,
            "hit_points": hit_points,
            "hit_dice": hit_dice,
            "speed": convert_speed(monster.get("speed", {})),
            "ability_scores": convert_ability_scores(ability_raw),
            "saving_throws": convert_saving_throws(monster.get("save", {})),
            "skills": convert_skills(monster.get("skill", {})),
            "challenge_rating": {"value": str(cr_value)},
            "xp": monster.get("xp", 0),

            **convert_defenses(monster),
            "senses": convert_senses(monster),
            "languages": convert_languages(monster.get("languages")),

            # Rich content
            "traits": convert_entry_list(monster.get("trait", [])),
            "actions": convert_entry_list(monster.get("action", [])),
            "bonus_actions": convert_entry_list(monster.get("bonus", [])),
            "reactions": convert_reactions(monster.get("reaction", [])),
            "legendary_actions": convert_entry_list(monster.get("legendary", [])),

            # Improved MPMM spellcasting
            "spellcasting": convert_spellcasting_mpmm(monster.get("spellcasting", [])),

            "environments": monster.get("environment", []) if isinstance(monster.get("environment"), list) else [],
            "source": monster.get("source", "MPMM"),

            "has_token": bool(monster.get("hasToken")),
            "has_fluff_image": bool(monster.get("hasFluffImages")),
            "image_path": None,  # Can be populated later
        }
        return result

    except Exception as e:
        print(f"[WARN] Skipping monster '{monster.get('name', '???')}': {e}")
        return None


def convert_entry_list(raw_list: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Re-exported for convenience."""
    from import_srd_monsters import convert_entry_list as original_convert
    return original_convert(raw_list)


def main() -> None:
    print("=== MPMM Monster Importer ===\n")

    clone_5etools_repo()

    bestiary_file = REPO_DIR / "data" / "bestiary" / "bestiary-mpmm.json"

    if not bestiary_file.exists():
        print(f"[ERROR] MPMM bestiary not found at {bestiary_file}")
        print("Please make sure the 5eTools repo is fully cloned.")
        return

    print(f"[INFO] Loading MPMM data from {bestiary_file}")
    with open(bestiary_file, encoding="utf-8") as f:
        data = json.load(f)

    monsters_raw = data.get("monster", [])
    print(f"[INFO] Found {len(monsters_raw)} monsters in MPMM")

    converted = []
    for m in monsters_raw:
        result = convert_monster_mpmm(m)
        if result:
            converted.append(result)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Converted {len(converted)} MPMM monsters.")
    print(f"Output written to: {OUTPUT_FILE}")
    print("\nYou can now restart your app to use the new MPMM data.")


if __name__ == "__main__":
    main()
