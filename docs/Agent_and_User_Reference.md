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

**Current UI Status (May 2026):**  
The desktop UI has been successfully migrated to the adapters layer (`adapters/inbound/desktop_ui/`). The new `MainWindow` (with SidebarWidget, StatBlockPanel, ConditionPanel, and signal-driven updates via `EncounterSignals`) is now the active implementation. The legacy `ui/` folder is deprecated (see its README for details).

**Migration complete as of late May 2026.** All new UI development must happen inside `src/dnd_encounter/adapters/inbound/desktop_ui/`.

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

## 8. Current Implementation Status (May 2026)

**Completed:**
- Full Hexagonal Architecture skeleton (Domain → Ports → Application → Adapters)
- Strict command pattern (`EditHpCommand` as the canonical example, `InMemoryUndoStack`)
- `EncounterService` + DTO boundary (`EncounterStateDTO`, `EntityRowDTO`)
- `EncounterSignals` (Qt signals for reactive updates)
- **UI Migration (UI-1 through UI-5)**: New `MainWindow` + migrated dialogs live in `adapters/inbound/desktop_ui/`. Old `ui/` is deprecated.
- 18+ professional UI tests passing for the new architecture (pytest-qt, headless).
- Bootstrap with 60s auto-save timer + platformdirs persistence wiring.
- Ruff + mypy clean on the new code paths.

**Current Gaps (what the next phase must address):**
- Keyboard shortcuts not yet wired in the new `MainWindow`.
- No context menu on the initiative list (right-click remove/rename/edit initiative).
- `StatBlockPanel` is minimal (needs richer monster stat block display when `MonsterDefinition` data is available).
- ConditionPanel integration is basic.
- Full feature parity with the behavioral spec from Parts 1–3 (monster stat blocks, import flow, better HP editing UI).

---

## 9. Next Implementation Phase (Post-Migration)

**Phase Name:** New UI Interaction Polish & Feature Completion (TDD-driven)

**Guiding Principle:** Every new capability must be added using strict TDD:
1. Write a failing test first (red).
2. Implement the minimal code to make it pass (green).
3. Refactor + self-heal (ruff/mypy/tests green).
4. Only then move to the next slice.

**Priority Order for this Phase (small vertical slices):**

1. **Keyboard Shortcuts** (highest immediate value)
   - Space / Ctrl+→ → Advance Turn
   - Delete / Backspace → Remove selected entity
   - Ctrl+Z → Undo
   - Tests first in `test_new_main_window.py` using `qtbot.keyClick`

2. **Context Menu on Sidebar**
   - Right-click → Remove, Rename, Edit Initiative
   - Must update `InitiativeListModel` + `SidebarWidget`

3. **Richer StatBlockPanel**
   - Show more fields from `EntityRowDTO` + future full monster stats
   - Better formatting and live HP display

4. **Robust Condition Flow**
   - Open ConditionPanel for the currently selected entity from sidebar
   - Ensure selection + toggle updates propagate via signals

5. **Deeper Feature Work** (after above)
   - Full monster stat block loading from JSON
   - `ImportService` integration
   - Better error display via `error_occurred` signal

**Rule:** No implementation work on any of the above without a red test first.

---

## 10. How to Run the Application

### Running the Desktop UI (Windows)

From the project root:

```bash
cd encounter-manager/encounter-manager-v2/dnd-encounter-manager-tdd
uv run python -m src.dnd_encounter.main
```

Or if `main.py` is not yet updated for the new bootstrap:

```bash
uv run python -c "
from dnd_encounter.bootstrap import bootstrap
window = bootstrap()
window.show()
from PySide6.QtWidgets import QApplication
QApplication.instance().exec()
"
```

**Running GUI tests (headless by default)**

GUI tests use `pytest-qt` and are configured to run **headless** — no windows pop up:

```powershell
# Recommended (works on fresh clone)
uv run pytest tests/unit/ui/ -q
```

On Windows PowerShell, the explicit form also works:

```powershell
$env:QT_QPA_PLATFORM="offscreen"; uv run pytest tests/unit/ui/ -q
```

### Running the Full Test Suite + Lint

```bash
uv run ruff check && uv run ruff format --check
uv run mypy src
uv run pytest -q
```

---

## 11. TDD Build Sequence (Critical for Agent)

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

## 12. Key Design Decisions

- Use **dataclasses** in Domain (no Pydantic)
- `EncounterStateDTO` returned by every service method
- Auto-save timer lives in `bootstrap.py` (not in a service)
- Undo stack limited to depth 5 using `collections.deque(maxlen=5)`
- Atomic file writes (tmp + rename)
- `ImportService` is the only place that imports `jsonschema`

---

## 13. Implementation Checklist (for Agent)

Before considering any task complete, verify:

- [ ] `ruff check` + `ruff format` clean
- [ ] `mypy` passes
- [ ] All tests pass
- [ ] No domain file imports from outer layers
- [ ] `bootstrap.py` is the only cross-layer import point
- [ ] `current_hp` is only modified via `EditHpCommand`

---

## 14. File Structure (High Level)

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

*Last updated: May 2026 (UI migration complete + Next Phase defined)*