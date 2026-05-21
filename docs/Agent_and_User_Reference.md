# D&D Encounter Manager - Agent & User Reference

**Consolidated Specification** (Most Important Parts)

This document combines the key information from Parts 1–4 into one compact reference for both AI agents and human developers/users.

---

## 1. Project Overview

**D&D 5e Encounter Manager** is a desktop application for Dungeon Masters to manage combat encounters.

**Core Goals:**
- Fast initiative tracking
- Easy HP and condition management
- Clean, responsive PySide6 UI
- Strict TDD + Hexagonal Architecture
- Long-term maintainability and testability

**Tech Stack:** Python 3.12 + PySide6 + Hexagonal Architecture (Ports & Adapters) + TDD

---

## 2. Core Features

- Add monsters (from SRD or imported JSON)
- Add custom players
- Automatic initiative rolling + 5-step tie-breaking
- Live HP editing with clamping and auto-remove at 0 HP
- Toggle conditions (15 standard D&D conditions)
- Advance turn / next combatant
- Undo stack (last 5 actions)
- Auto-save every 60 seconds
- Clean stat block panel showing live state
- Keyboard-driven workflow (hotkeys)

---

## 3. Domain Model (Key Concepts)

### Entities
- **EncounterEntity**: instance_id, display_name, entity_type (monster/player), initiative, current_hp, max_hp, conditions, is_active
- **Encounter**: list of entities, current_turn_index, round_number
- **MonsterDefinition**: Full stat block data (loaded from JSON)

### Value Objects & Rules
- `Condition` enum (15 conditions)
- `apply_hp_edit()` + `is_auto_remove()`
- `toggle_condition()` (immutable)
- `sort_entities()` with 5-step tie-breaking (Dex → Player priority → CR → PRNG)

**Important Invariant:** Only `EditHpCommand` is allowed to modify `current_hp`.

---

## 4. Architecture (Hexagonal)

**Strict layering enforced by mypy + import-linter:**

- **Domain**: Pure Python. Zero external imports. No side effects.
- **Ports**: `typing.Protocol` definitions only.
- **Application**: Orchestrates via Commands + Services. Returns `EncounterStateDTO`.
- **Adapters**: All I/O and UI lives here.
- **bootstrap.py**: The *only* file allowed to import from both Application and Adapters.

**Key Rule:** Dependency arrows always point inward.

---

## 5. Data Transfer Objects (DTOs)

- `EntityRowDTO`: What the UI sees (live HP + conditions)
- `EncounterStateDTO`: Main object returned by services
- `MonsterSummaryDTO`: Lightweight monster info

UI **never** touches domain entities directly.

---

## 6. UI Components

| Component            | Responsibility                              | Key Behavior                          |
|----------------------|---------------------------------------------|---------------------------------------|
| `SidebarWidget`      | Initiative list                             | Current turn highlight, emits selection |
| `StatBlockPanel`     | Live stat block                             | Shows current HP + conditions         |
| `ConditionPanel`     | Toggle conditions                           | 15 checkboxes, emits toggle signal    |
| `MainWindow`         | Main layout + wiring                        | Connects signals, hotkeys             |
| `HotkeyHandler`      | Keyboard shortcuts                          | Space / Cmd+Z / Cmd+M etc.            |

---

## 7. Hotkeys (Planned)

- **Advance Turn**: `Space` or `Ctrl+Right`
- **Undo**: `Cmd+Z`
- **Add Monster**: `Cmd+M`
- **Add Player**: `Cmd+P`
- **Remove Entity**: `Delete` / `Backspace`
- **Toggle Condition Panel**: `Cmd+K`
- **Import Monsters**: `Cmd+O`

---

## 8. TDD Build Sequence (Critical for Agent)

The agent **must** follow this order strictly:

**Phase A – Domain** (pure, no mocks)
- `test_hp_rules.py`
- `test_condition_rules.py`
- `test_initiative_sorter.py`
- Value objects

**Phase D – Commands**
- `EditHpCommand` first, then others

**Phase E – Services**
- `EncounterService`

**Phase G – UI** (pytest-qt)
- `test_sidebar_widget.py`
- `test_condition_panel.py`
- `test_hotkey_handler.py`

**Rule:** Never create implementation before the corresponding test is red.

---

## 9. Key Design Decisions

- Use **dataclasses** in Domain (no Pydantic)
- `EncounterStateDTO` returned by every service method
- Auto-save timer lives in `bootstrap.py` (not in a service)
- Undo stack limited to depth 5 using `collections.deque(maxlen=5)`
- Atomic file writes (tmp + rename)
- `ImportService` is the only place that imports `jsonschema`

---

## 10. Implementation Checklist (for Agent)

Before considering any task complete, verify:

- [ ] `ruff check` + `ruff format` clean
- [ ] `mypy` passes
- [ ] All tests pass
- [ ] No domain file imports from outer layers
- [ ] `bootstrap.py` is the only cross-layer import point
- [ ] `current_hp` is only modified via `EditHpCommand`

---

## 11. File Structure (High Level)

```
dnd-encounter-manager/
├── src/dnd_encounter/
│   ├── domain/          # Pure logic
│   ├── ports/           # Protocols
│   ├── application/     # Commands + Services + DTOs
│   └── adapters/
│       └── inbound/desktop_ui/   # PySide6 widgets
├── tests/
├── schema/            # encounter-schema-v1.json
└── docs/              # This reference + specs
```

---

*This document was synthesized from Parts 1–4 for agent usability and user reference.*

*Last updated: May 2026*