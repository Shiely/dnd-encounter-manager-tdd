# D&D Encounter Manager (TDD Edition)

**Full implementation of the complete 4-part specification** using Hexagonal Architecture (Ports & Adapters), strict Test-Driven Development, Python 3.12 + PySide6.

This is a collaborative experiment between Shiely and Grok to build the app exactly as designed in the spec documents (Parts 1-4 in Google Drive), following the precise TDD sequence from Part 4.

## Current Status (May 2026)

- ✅ Phases A–F (Core Architecture + Commands + Services): Complete
- ✅ Phase G – UI Migration (UI-1 through UI-5): **Complete**
  - New `MainWindow` + all widgets live in `adapters/inbound/desktop_ui/`
  - 18+ pytest-qt tests green for the new UI
  - Old `ui/` folder deprecated
- ✅ Full 5e SRD + supplements bestiary integrated (~4439 monsters from 5eTools mirror)
  - Rich data: ability scores, saving throws, skills, resistances, traits, legendary actions, spellcasting, senses, languages
  - SrdMonsterRepository + CompositeMonsterRepository (SRD base + user overrides)
  - StatBlockPanel now displays full monster details + image/token support foundation
- ✅ Ruff: Clean
- ✅ mypy: Passing on new code (relaxed globally for now)
- ✅ Self-healing discipline maintained throughout

**Next Phase (active):** "New UI Interaction Polish & Feature Completion"  
Following strict TDD: Keyboard shortcuts first, then context menus, richer StatBlockPanel, etc.

**Goal**: Daily-driver feature parity with the original spec while keeping the architecture pure.

## Recent Major Features

- **Custom Monster Creator** — Create and save your own monsters directly from the Add Monster dialog. All `MonsterDefinition` fields are supported (only Name + HP are required).
- **Rich StatBlockPanel** — Displays full monster data including ability scores, saving throws, skills, resistances, traits, actions, legendary actions, spellcasting, etc.
- **Improved Remove Button** — Entities are now correctly removed from the initiative list (soft-delete with full Undo support).
- **On-demand Token Downloading** — Monster images can be fetched automatically from the 5eTools mirror the first time you view a monster (with local caching).
- **Full 5e Bestiary** — ~4400 monsters with rich data loaded from 5eTools.

## Getting Started on Windows (After `git clone`)

This project uses **uv** for Python environment management to guarantee everyone runs the exact same Python version (3.12) and library versions.

### Recommended (Easiest)

1. Open **PowerShell** in the cloned folder.
2. Run the installer:

   ```powershell
   .\utilities\install_windows.ps1
   ```

3. Launch the app:

   ```powershell
   uv run python run_ui.py
   ```

### Manual Steps (if you prefer)

```powershell
# 1. Install uv (if not already installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Pin Python 3.12 and install dependencies
uv python pin 3.12
uv sync --dev

# 3. Run the application
uv run python run_ui.py
```

**Important**: Always run the app with `uv run ...`. This ensures you use the project's locked Python 3.12 environment and exact dependency versions.

## Monster Images & Tokens

The right-hand StatBlockPanel can display official-style monster tokens/portraits.

### How it works

- The app looks for images in these locations (in order):
  - `data/images/bestiary/tokens/<SOURCE>/<Name>.webp` (or .png)
  - `data/images/bestiary/tokens/<Name>.webp`
  - `data/5etools-img/img/bestiary/tokens/<SOURCE>/<Name>.webp` (if you clone the image mirror)

- Filenames should follow 5eTools conventions (spaces → `_`, special characters removed).

### Recommended setup

Run the setup script after installing the project:

```bash
uv run python utilities/setup_monster_images.py
```

This creates the expected folder structure and generates guidance.

**Note**: The full image collection is very large. Most users add tokens on-demand for the monsters they actually use (Option A).

Built with Grok — May 2026