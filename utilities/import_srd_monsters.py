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

REPO_URL = "https://github.com/5etools-mirror-3/5etools-src.git"
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


# ---------- 5eTools entry rendering & helper converters (NEW) ----------

def _strip_5etools_tags(text: str) -> str:
    """Roughly convert 5eTools {@tag|...} syntax into readable text.
    Improved to handle damage and dice expressions.
    """
    import re

    if not isinstance(text, str):
        return str(text)

    def replace_tag(match: re.Match) -> str:
        content = match.group(0)

        # Handle {@damage 8d8 force} or {@damage 8d8|force}
        if '{@damage ' in content:
            inner = content.replace('{@damage ', '').rstrip('}')
            # Try to extract formula and type
            parts = inner.split('|')
            formula = parts[0].strip()
            dmg_type = parts[1].strip() if len(parts) > 1 else ""
            if dmg_type:
                return f"{formula} {dmg_type}"
            return formula

        # Handle {@dice 8d8}
        if '{@dice ' in content:
            inner = content.replace('{@dice ', '').rstrip('}')
            return inner.split('|')[0].strip()

        if '|' in content:
            inner = content.split('|')[-1].rstrip('}')
            return inner
        if '{@dc ' in content:
            return content.replace('{@dc ', 'DC ').rstrip('}')
        if '{@hit ' in content:
            return content.replace('{@hit ', '+').rstrip('}')

        # Handle common tags like {@spell Foo Bar}, {@item Wand}, {@condition Blinded}, etc.
        tag_match = re.match(r'\{@(\w+)\s+(.+?)\}$', content)
        if tag_match:
            tag = tag_match.group(1).lower()
            rest = tag_match.group(2).strip()

            # Special handling for attack type abbreviations used in 5eTools
            if tag == "atk":
                atk_map = {
                    "mw": "Melee Weapon Attack",
                    "rw": "Ranged Weapon Attack",
                    "ms": "Melee Spell Attack",
                    "rs": "Ranged Spell Attack",
                    "ms,rs": "Melee or Ranged Spell Attack",
                    "mw,rw": "Melee or Ranged Weapon Attack",
                    "m": "Melee Attack",
                    "r": "Ranged Attack",
                }
                return atk_map.get(rest.lower(), rest)

            return rest

        # Handle {@recharge 4}, {@recharge 4-6}, {@recharge 5|6}, etc.
        if '{@recharge' in content:
            m = re.search(r'\{@recharge\s*([^}]+)\}', content)
            if m:
                val = m.group(1).strip()
                # Normalize "4-6" or "4|6" style
                val = val.replace('|', '–').replace('-', '–')
                return f"(Recharge {val})"

        # Last resort: remove the tag entirely
        return re.sub(r'\{@[^}]+}', '', content)

    text = re.sub(r'\{@[^}]+}', replace_tag, text)
    text = re.sub(r'[{}]', '', text)
    return text.strip()


def render_entries(entries: Any) -> str:
    if entries is None:
        return ""
    if isinstance(entries, str):
        return _strip_5etools_tags(entries)
    if isinstance(entries, (int, float)):
        return str(entries)
    if isinstance(entries, list):
        parts = [render_entries(e) for e in entries]
        return " ".join(p for p in parts if p).strip()
    if isinstance(entries, dict):
        # Handle structured damage objects
        if entries.get("type") == "damage" and "damage" in entries:
            damage_parts = []
            for d in entries["damage"]:
                avg = d.get("average")
                formula = d.get("formula") or d.get("dice")
                dmg_type = d.get("type", "")
                if avg is not None and formula:
                    damage_parts.append(f"{avg} ({formula})")
                elif formula:
                    damage_parts.append(f"({formula})")
            return " ".join(damage_parts)

        # Handle standalone dice objects
        if entries.get("type") == "dice":
            avg = entries.get("average")
            formula = entries.get("formula") or entries.get("dice")
            if avg is not None and formula:
                return f"{avg} ({formula})"
            if formula:
                return f"({formula})"
            return ""

        # Recursively handle common wrapper structures
        for key in ("entries", "text", "entry", "items"):
            if key in entries:
                text = render_entries(entries[key])
                name = entries.get("name")
                if name:
                    return f"{name}. {text}".strip() if text else str(name)
                return text

        return str(entries)
    return str(entries)


def convert_saving_throws(save: dict[str, Any]) -> dict[str, int]:
    if not isinstance(save, dict):
        return {}
    result = {}
    for ability, val in save.items():
        try:
            result[ability] = int(val)
        except (ValueError, TypeError):
            pass
    return result


def convert_skills(skill: dict[str, Any]) -> dict[str, int]:
    if not isinstance(skill, dict):
        return {}
    result = {}
    for sk, val in skill.items():
        try:
            result[sk] = int(val)
        except (ValueError, TypeError):
            pass
    return result


def _normalize_defense_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for k in ("resist", "immune", "vulnerable"):
                    if k in item:
                        out.extend(_normalize_defense_list(item[k]))
        return out
    return []


def convert_defenses(monster: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "damage_resistances": _normalize_defense_list(monster.get("resist")),
        "damage_immunities": _normalize_defense_list(monster.get("immune")),
        "damage_vulnerabilities": _normalize_defense_list(monster.get("vulnerable")),
        "condition_immunities": _normalize_defense_list(monster.get("conditionImmune")),
    }


def convert_languages(languages: Any) -> list[str]:
    if not languages:
        return []
    if isinstance(languages, str):
        return [languages]
    if isinstance(languages, list):
        return [str(x) for x in languages if x]
    return []


def convert_senses(monster: dict[str, Any]) -> dict[str, Any]:
    senses = monster.get("senses")
    if isinstance(senses, str):
        import re
        out = {"darkvision": 0, "blindsight": 0, "tremorsense": 0, "truesight": 0}
        for sense, dist in re.findall(r'(darkvision|blindsight|tremorsense|truesight)\s*(\d+)', senses, re.I):
            out[sense.lower()] = int(dist)
        out["passive_perception"] = monster.get("passive", 10)
        return out
    if isinstance(senses, dict):
        return {
            "darkvision": senses.get("darkvision", 0),
            "blindsight": senses.get("blindsight", 0),
            "tremorsense": senses.get("tremorsense", 0),
            "truesight": senses.get("truesight", 0),
            "passive_perception": monster.get("passive", senses.get("passive", 10)),
        }
    return {
        "darkvision": 0, "blindsight": 0, "tremorsense": 0, "truesight": 0,
        "passive_perception": monster.get("passive", 10),
    }


def convert_entry_list(raw_list: list[dict[str, Any]]) -> list[dict[str, str]]:
    result = []
    for item in raw_list or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or "Feature"
        desc = render_entries(item.get("entries") or item.get("entry") or item.get("text") or "")
        if desc:
            # High cap for info preservation; UI can scroll. Real descriptions rarely exceed 2000 chars.
            result.append({"name": str(name), "description": desc[:8000]})
    return result


def convert_spellcasting(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert spellcasting using the unified shape also produced by convert_spellcasting_mpmm:
    "spells": { "at_will": [...], "daily_2": [...], "level_3": {"spells": [...], "slots": N}, ... }
    """
    out = []
    for sc in raw or []:
        if not isinstance(sc, dict):
            continue
        name = sc.get("name", "Spellcasting")
        header = render_entries(sc.get("headerEntries", []))

        spells_by_freq: dict[str, Any] = {}

        # Classic keys directly on the spellcasting object
        for classic_key in ("will", "atWill", "at_will"):
            if classic_key in sc and sc[classic_key]:
                val = sc[classic_key]
                lst = val if isinstance(val, list) else (val.get("spells") if isinstance(val, dict) else [])
                spells_by_freq["at_will"] = [_strip_5etools_tags(s) for s in lst if s]

        daily = sc.get("daily") or sc.get("Daily")
        if isinstance(daily, dict):
            for freq, spell_list in daily.items():
                if not spell_list:
                    continue
                num = "".join(ch for ch in str(freq) if ch.isdigit())
                key = f"daily_{num}" if num else f"daily_{freq}"
                clean = [_strip_5etools_tags(s) for s in (spell_list if isinstance(spell_list, list) else [spell_list])]
                spells_by_freq[key] = clean

        leg = sc.get("legendary")
        if isinstance(leg, list) and leg:
            spells_by_freq["legendary"] = [_strip_5etools_tags(s) for s in leg]

        # Modern "spells" dict with numeric levels
        spells_data = sc.get("spells", {})
        if isinstance(spells_data, dict):
            for level_str, level_info in spells_data.items():
                if not isinstance(level_info, dict):
                    continue
                try:
                    level = int(level_str)
                except (ValueError, TypeError):
                    continue
                spell_list = level_info.get("spells", []) or []
                slots = level_info.get("slots")
                clean = [_strip_5etools_tags(s) for s in spell_list if s]
                if level == 0:
                    spells_by_freq["at_will"] = clean
                else:
                    key = f"level_{level}"
                    entry: dict[str, Any] = {"spells": clean}
                    if slots is not None:
                        entry["slots"] = slots
                    spells_by_freq[key] = entry

        # Fallback capture of any remaining spells* keys
        if not spells_by_freq:
            for k, v in list(sc.items())[:8]:
                if str(k).lower().startswith("spells") and v:
                    if isinstance(v, list):
                        spells_by_freq["other"] = [_strip_5etools_tags(s) for s in v if s]
                    break

        out.append({
            "name": name,
            "header": header,
            "ability": sc.get("ability", "int"),
            "spells": spells_by_freq,
        })
    return out


def _get_conventional_image_path(monster: dict[str, Any]) -> str | None:
    """Best-effort conventional path for a monster token / image.
    Actual files should be placed under data/images/ following this path.
    """
    if not (monster.get("hasToken") or monster.get("hasFluffImages")):
        return None

    name = monster.get("name", "")
    # Sanitize name similar to 5eTools conventions
    slug = (
        name.replace(" ", "_")
            .replace("'", "")
            .replace("/", "-")
            .replace(":", "")
            .replace("?", "")
            .replace("!", "")
    )
    # Common location used by many 5eTools mirrors
    return f"bestiary/tokens/{slug}.png"


# ---------- Main conversion function (greatly expanded) ----------

def convert_monster(monster: dict[str, Any]) -> dict[str, Any] | None:
    try:
        name = monster.get("name", "Unknown")
        monster_id = name.lower().replace(" ", "-").replace("'", "").replace("/", "-")

        # CR handling
        cr = monster.get("cr")
        if isinstance(cr, dict):
            cr_value = cr.get("cr", cr.get("value", "0"))
        else:
            cr_value = str(cr) if cr else "0"

        # Basic combat stats
        ac = 10
        if isinstance(monster.get("ac"), list) and monster["ac"]:
            first = monster["ac"][0]
            ac = first.get("ac", first) if isinstance(first, dict) else first
        elif isinstance(monster.get("ac"), (int, str)):
            ac = int(monster["ac"])

        hp = monster.get("hp", {})
        if isinstance(hp, dict):
            hit_points = hp.get("average", 10)
            hit_dice = hp.get("formula", "1d8")
        else:
            hit_points = int(hp) if hp else 10
            hit_dice = "1d8"

        # Ability scores (5eTools stores them at top level as str/dex/...)
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

            # Defenses
            **convert_defenses(monster),

            # Senses & languages
            "senses": convert_senses(monster),
            "languages": convert_languages(monster.get("languages")),

            # Rich descriptive content (greatly improved)
            "traits": convert_entry_list(monster.get("trait", [])),
            "actions": convert_entry_list(monster.get("action", [])),
            "bonus_actions": convert_entry_list(monster.get("bonus", [])),
            "reactions": convert_entry_list(monster.get("reaction", [])),
            "legendary_actions": convert_entry_list(monster.get("legendary", [])),

            # Spellcasting
            "spellcasting": convert_spellcasting(monster.get("spellcasting", [])),

            # Misc
            "environments": monster.get("environment", []) if isinstance(monster.get("environment"), list) else [],
            "source": monster.get("source", "SRD"),

            # Image / token support (metadata only — actual files are user-provided)
            "has_token": bool(monster.get("hasToken")),
            "has_fluff_image": bool(monster.get("hasFluffImages")),
            "image_path": _get_conventional_image_path(monster),
        }
        return result

    except Exception as e:
        print(f"[WARN] Skipping monster '{monster.get('name', '???')}': {e}")
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
