"""
MonsterStatBlockRenderer

Responsible for turning a MonsterDefinition into a rich HTML stat block.

This class was extracted from StatBlockPanel._build_rich_monster_html
to improve testability, separation of concerns, and long-term maintainability.

It is deliberately free of Qt dependencies.
"""

import re

from dnd_encounter.domain.entities.monster_definition import MonsterDefinition


def _clean_display_text(text: str) -> str:
    """Defensive cleaner for any text that may contain 5eTools tags or leaked source codes.
    Used in addition to the importer-time cleaning for custom monsters and robustness.
    """
    if not isinstance(text, str):
        text = str(text)
    # Remove any remaining 5eTools tags
    text = re.sub(r'\{@[^}]+}', '', text)
    # Nuke bare source codes that somehow reached the UI layer
    for code in ("XPHB", "XDMG", "XMM"):
        text = re.sub(rf'\b{code}\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class MonsterStatBlockRenderer:
    """Pure renderer: MonsterDefinition → HTML string for the stat block."""

    def render(
        self,
        m: MonsterDefinition,
        current_hp: int | None = None,
        max_hp: int | None = None,
    ) -> str:
        """Produce a nice HTML block for the full monster stat block.

        If current_hp and/or max_hp are provided, they represent the actual
        rolled values for this specific instance (preferred over the definition
        average for display purposes). The hit_dice formula is still shown for
        reference.
        """
        parts: list[str] = []

        # Header line
        cr = getattr(getattr(m, "challenge_rating", None), "value", "?")
        parts.append(f"<b><i>CR {cr}</i></b>")

        # Creature type line (Size, Type, Alignment) - robust against messy imported data
        # (type_ is sometimes a dict like {"type": "humanoid", "tags": [...]})
        def _normalize_type_field(val):
            if isinstance(val, str):
                return val
            if isinstance(val, dict):
                return val.get("type") or val.get("name") or ""
            return str(val) if val else ""

        raw_size = getattr(m, "size", "")
        raw_type = getattr(m, "type_", "")
        raw_alignment = getattr(m, "alignment", "")

        size = _normalize_type_field(raw_size)
        type_ = _normalize_type_field(raw_type)
        alignment = _normalize_type_field(raw_alignment)

        # Expand common abbreviations for readability
        size_map = {
            "T": "Tiny", "S": "Small", "M": "Medium",
            "L": "Large", "H": "Huge", "G": "Gargantuan",
        }
        size = size_map.get(size, size)

        align_map = {
            "A": "any alignment", "U": "unaligned",
            "N": "neutral", "NG": "neutral good", "NE": "neutral evil",
            "LG": "lawful good", "LN": "lawful neutral", "LE": "lawful evil",
            "CG": "chaotic good", "CN": "chaotic neutral", "CE": "chaotic evil",
        }
        alignment = align_map.get(alignment, alignment)

        if size or type_ or alignment:
            type_parts = [p for p in (size, type_, alignment) if p]
            if type_parts:
                type_line = ", ".join(type_parts)
                parts.append(f"<b>{type_line}</b>")

        # Ability scores (defensively)
        def _append_ability_scores(parts):
            ab = getattr(m, "ability_scores", None)
            saving_throws = getattr(m, "saving_throws", {}) or {}

            if ab:
                abilities = [
                    ("STR", getattr(ab, "str_", 10)),
                    ("DEX", getattr(ab, "dex", 10)),
                    ("CON", getattr(ab, "con", 10)),
                    ("INT", getattr(ab, "int_", 10)),
                    ("WIS", getattr(ab, "wis", 10)),
                    ("CHA", getattr(ab, "cha", 10)),
                ]

                score_lines = []
                for abbr, score in abilities:
                    mod = (score - 10) // 2
                    mod_str = f"+{mod}" if mod >= 0 else str(mod)

                    save_bonus = saving_throws.get(abbr.lower(), 0)
                    save_total = mod + save_bonus
                    save_str = f"+{save_total}" if save_total >= 0 else str(save_total)

                    if save_bonus != 0:
                        line = f"<b>{abbr}</b> {score} ({mod_str})   <b>Save {save_str}</b>"
                    else:
                        line = f"<b>{abbr}</b> {score} ({mod_str})   Save {save_str}"

                    score_lines.append(line)

                parts.append("<small>" + "<br>".join(score_lines) + "</small>")

        self._safe_append(parts, "Ability Scores", _append_ability_scores)

        # Skills (defensively)
        def _append_skills(parts):
            skills = getattr(m, "skills", {}) or {}
            if skills:
                def fmt(d): return ", ".join(f"{k.upper()} +{v}" for k, v in d.items())
                parts.append(f"<b>Skills:</b> {fmt(skills)}")

        self._safe_append(parts, "Skills", _append_skills)

        # Core combat stats (defensively)
        def _append_combat_stats(parts):
            ac = getattr(m, "armor_class", None)
            hp = getattr(m, "hit_points", None)
            hit_dice = getattr(m, "hit_dice", None)
            speed = getattr(m, "speed", {}) or {}

            combat_stats = []
            if ac is not None:
                combat_stats.append(f"<b>AC</b> {ac}")

            effective_hp = current_hp if current_hp is not None else hp
            effective_max = max_hp if max_hp is not None else hp

            if effective_hp is not None:
                if effective_max is not None and effective_max != effective_hp:
                    hp_line = f"<b>HP</b> {effective_hp} / {effective_max}"
                else:
                    hp_line = f"<b>HP</b> {effective_hp}"

                if hit_dice:
                    hp_line += f" <small>(rolled from {hit_dice})</small>"

                combat_stats.append(hp_line)
            if speed:
                speed_parts = []
                for k, v in speed.items():
                    if k == "walk" and v:
                        speed_parts.append(f"{v} ft.")
                    elif v and k not in ("hover",):
                        speed_parts.append(f"{k} {v} ft.")
                if speed.get("hover"):
                    speed_parts.append("hover")
                if speed_parts:
                    combat_stats.append(f"<b>Speed</b> {', '.join(speed_parts)}")

            if combat_stats:
                parts.append(" | ".join(combat_stats))

        self._safe_append(parts, "Combat Stats", _append_combat_stats)

        # Defenses (wrapped defensively)
        def _append_defenses(parts):
            resists = getattr(m, "damage_resistances", []) or []
            immunes = getattr(m, "damage_immunities", []) or []
            vulns = getattr(m, "damage_vulnerabilities", []) or []
            cond_immune = getattr(m, "condition_immunities", []) or []

            def fmt_list(lst, label):
                if not lst:
                    return ""
                clean = [str(item) for item in lst if item]
                return f"<b>{label}:</b> {', '.join(clean)}" if clean else ""

            def_lines = [
                fmt_list(resists, "Resist"),
                fmt_list(immunes, "Immune"),
                fmt_list(vulns, "Vulnerable"),
                fmt_list(cond_immune, "Condition Immune"),
            ]
            def_lines = [d for d in def_lines if d]
            if def_lines:
                parts.append(" | ".join(def_lines))

        self._safe_append(parts, "Defenses", _append_defenses)

        # Senses + Languages (defensively)
        def _append_senses_languages(parts):
            senses = getattr(m, "senses", {}) or {}
            langs = getattr(m, "languages", []) or []
            sense_parts = [f"{k} {v}" for k, v in senses.items() if v and k != "passive_perception"]
            if senses.get("passive_perception"):
                sense_parts.append(f"passive Perception {senses['passive_perception']}")
            if sense_parts:
                parts.append(f"<b>Senses:</b> {', '.join(sense_parts)}")
            if langs:
                parts.append(f"<b>Languages:</b> {', '.join(langs)}")

        self._safe_append(parts, "Senses + Languages", _append_senses_languages)

        # Traits / Features (defensively)
        self._safe_append(parts, "Traits", lambda p: self._append_list_section(p, getattr(m, "traits", []) or [], "Traits"))

        # Bonus Actions (defensively)
        self._safe_append(parts, "Bonus Actions", lambda p: self._append_list_section(p, getattr(m, "bonus_actions", []) or [], "Bonus Actions"))

        # Actions (defensively)
        self._safe_append(parts, "Actions", lambda p: self._append_actions_section(p, getattr(m, "actions", []) or []))

        # Legendary Actions (defensively)
        self._safe_append(parts, "Legendary Actions", lambda p: self._append_list_section(p, getattr(m, "legendary_actions", []) or [], "Legendary Actions"))

        # Spellcasting (defensively)
        self._safe_append(parts, "Spellcasting", lambda p: self._render_spellcasting(p, m))

        # Reactions (defensively)
        self._safe_append(parts, "Reactions", lambda p: self._append_list_section(p, getattr(m, "reactions", []) or [], "Reactions"))

        return "<br>".join(parts)

    def _safe_append(self, parts: list[str], label: str, func):
        """Render a section defensively. If it fails, we skip it instead of breaking the whole stat block."""
        try:
            func(parts)
        except Exception:
            # In production we'd log this. For now, we silently skip the bad section
            # so the rest of the monster stat block still renders.
            # You can uncomment the next line during debugging:
            # print(f"[RENDERER] Skipped section '{label}' due to error: {e}")
            pass

    def _append_list_section(self, parts: list[str], entries: list, section_title: str) -> None:
        """Generic handler for traits, bonus actions, legendary actions, reactions."""
        if not entries:
            return
        parts.append(f"<b>{section_title}</b>")
        for e in entries:
            name = e.get("name", section_title.rstrip("s")) if isinstance(e, dict) else str(e)
            desc = e.get("description", "") if isinstance(e, dict) else ""
            # Defensive: handle dict descriptions etc.
            name = _clean_display_text(name)
            desc = _clean_display_text(desc)
            parts.append(f"<b>{name}.</b> {desc}")

    def _append_actions_section(self, parts: list[str], actions: list) -> None:
        """Actions with the classic 5e attack formatting logic."""
        if not actions:
            return
        parts.append("<b>Actions</b>")
        for a in actions:
            if not isinstance(a, dict):
                # Extremely defensive
                parts.append(f"<b>Action.</b> {a}")
                continue
            name = a.get("name", "Action")
            desc = a.get("description", "").strip()
            name = _clean_display_text(name)
            desc = _clean_display_text(desc)

            # Smart formatting for attack actions (same logic as before)
            lower_desc = desc.lower()

            if lower_desc.startswith(("ms,rs", "mw,rw", "ms ", "rs ")):
                desc = re.sub(r'^(ms,rs|mw,rw|ms|rs)\s*', 'Melee or Ranged Spell Attack: ', desc, flags=re.IGNORECASE)
                lower_desc = desc.lower()

            if "+ to hit" in lower_desc and "hit:" not in lower_desc:
                if "melee or ranged spell attack" not in lower_desc:
                    desc = "Melee or Ranged Spell Attack: " + desc

                if "hit:" not in lower_desc and any(x in lower_desc for x in ["damage", "force", "necrotic", "radiant"]):
                    hit_match = re.search(r'(\d+\s*\([^)]+\)\s*\w+\s*damage)', desc, re.IGNORECASE)
                    if hit_match:
                        desc = desc[:hit_match.start()] + "Hit: " + hit_match.group(1) + desc[hit_match.end():]
                    else:
                        desc = re.sub(r'(\d+\s*\([^)]+\))', r'Hit: \1', desc, count=1)

            parts.append(f"<b>{name}.</b> {desc}")

    def _render_spellcasting(self, parts: list[str], m: MonsterDefinition) -> None:
        """Render spellcasting section (called earlier in the output for better ordering)."""
        sc = getattr(m, "spellcasting", []) or []
        if not sc:
            return

        parts.append("<b>Spellcasting</b>")
        for entry in sc:
            header = entry.get("header", "")
            if header:
                header = _clean_display_text(header)
                parts.append(f"<i>{header}</i>")

            spells = entry.get("spells", {}) or {}
            if isinstance(spells, dict):
                def _sort_key(k):
                    if k == "at_will":
                        return (0, 0)
                    if k.startswith("daily_"):
                        try:
                            return (1, int(k.split("_", 1)[1]))
                        except Exception:
                            return (1, 99)
                    if k.startswith("level_"):
                        try:
                            return (2, int(k.split("_", 1)[1]))
                        except Exception:
                            return (2, 99)
                    return (3, 0)

                for freq in sorted(spells.keys(), key=_sort_key):
                    val = spells[freq]
                    if freq == "at_will":
                        freq_label = "At will"
                    elif freq.startswith("daily_"):
                        num = freq.split("_", 1)[1]
                        freq_label = f"{num}/day each"
                    elif freq.startswith("level_"):
                        num = freq.split("_", 1)[1]
                        freq_label = f"{num} level"
                    else:
                        freq_label = freq.replace("_", " ").title()

                    if isinstance(val, dict):
                        inner_spells = val.get("spells", [])
                        slots = val.get("slots")
                        spell_text = ", ".join(str(x) for x in inner_spells) if isinstance(inner_spells, list) else str(inner_spells)
                        if slots:
                            parts.append(f"<b>{freq_label} ({slots} slots):</b> {spell_text}")
                        else:
                            parts.append(f"<b>{freq_label}:</b> {spell_text}")
                    elif isinstance(val, list):
                        spell_text = ", ".join(str(x) for x in val)
                        parts.append(f"<b>{freq_label}:</b> {spell_text}")
                    else:
                        parts.append(f"<b>{freq_label}:</b> {val}")
            elif isinstance(spells, list):
                for spell_group in spells:
                    if isinstance(spell_group, dict):
                        for freq, spell_list in spell_group.items():
                            if spell_list:
                                freq_label = freq.replace("_", " ").title()
                                parts.append(f"<b>{freq_label}:</b> {spell_list}")
                    else:
                        parts.append(str(spell_group))
