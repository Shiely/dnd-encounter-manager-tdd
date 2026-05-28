# D&D Encounter Manager (TDD Edition)

**Full implementation of the complete 4-part specification** using Hexagonal Architecture (Ports & Adapters), strict Test-Driven Development, Python 3.12 + PySide6.

This is a collaborative experiment between Shiely and Grok to build the app exactly as designed in the spec documents (Parts 1-4 in Google Drive), following the precise TDD sequence from Part 4.

## Current Status (May 2026)

- ✅ Phases A–F (Core Architecture + Commands + Services): Complete
- ✅ Phase G – UI Migration (UI-1 through UI-5): **Complete**
  - New `MainWindow` + all widgets live in `adapters/inbound/desktop_ui/`
  - 18+ pytest-qt tests green for the new UI
  - Old `ui/` folder deprecated
- ✅ Full 5e SRD + supplements bestiary integrated (~3723 monsters (high-quality version) from 5eTools mirror)
  - Rich data: ability scores, saving throws, skills, resistances, traits, legendary actions, spellcasting, senses, languages
  - SrdMonsterRepository + CompositeMonsterRepository (SRD base + user overrides)
  - StatBlockPanel displays full rich monster details **+ official tokens that download on-demand**
- ✅ Monster token images are now robust and visible (background downloader + preloading + thread-safe)
- ✅ Ruff: Clean
- ✅ mypy: Passing on new code (relaxed globally for now)
- ✅ Self-healing discipline maintained throughout

**Next Phase (active):** "New UI Interaction Polish & Feature Completion"  
Following strict TDD: Keyboard shortcuts first, then context menus, richer StatBlockPanel, etc.

**Goal**: Daily-driver feature parity with the original spec while keeping the architecture pure.

## Recent Major Features

- **Custom Monster Creator** — Create and save your own monsters directly from the Add Monster dialog. All `MonsterDefinition` fields are supported (only Name + HP are required).
- **Rich StatBlockPanel** — Displays full monster data including ability scores, saving throws, skills, resistances, traits, actions, legendary actions, spellcasting, etc. **Plus official-style monster tokens/images**.
- **Monster Token Images (on-demand)** — The app now automatically downloads high-quality tokens from the official 5e.tools site (with underscore + %20 name variants + mirror fallback) the first time you view or add a monster. Robust background downloading with local caching, preloading for the entire encounter, and reliable display even when adding many creatures at once.
- **Improved Remove Button** — Entities are now correctly removed from the initiative list (soft-delete with full Undo support).
- **Full 5e Bestiary** — ~3723 monsters (high-quality version) with rich data loaded from 5eTools.

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

The right-hand **StatBlockPanel** automatically shows official-style monster tokens (140×140) for creatures that have them.

### How it works (now very reliable)

- When you add a monster (or it appears in the encounter), the app checks for a local token.
- If none exists and the monster has `has_token=True` in the bestiary, it starts a **background download** from the official `https://5e.tools/img/...` site (tries both `Ancient_Red_Dragon` and `Ancient%20Red%20Dragon` naming + mirror fallback).
- Images are saved to:
  ```
  data/images/bestiary/tokens/<SOURCE>/<SanitizedName>.webp   (or .png)
  ```
  Example: `data/images/bestiary/tokens/MM/Ancient_Red_Dragon.webp`
- The panel updates **live** as soon as the download finishes (even if you switched selection in the meantime).
- All monsters in the current encounter are preloaded automatically.

### Using the diagnostic tool

If images aren't appearing for a particular monster, use the standalone tester:

```bash
uv run python utilities/test_monster_images.py --name "Ancient Red Dragon" --verbose
# or
uv run python utilities/test_monster_images.py --name "Goblin" -v
```

This uses the exact same logic as the app and tells you exactly which URL succeeded (or failed).

### First-time experience

- The first time you view a new monster, you will briefly see **"Downloading token..."**.
- After 1–4 seconds (depending on your connection) the real token appears.
- Subsequent views are instant (cached locally).
- The app will never download the same monster twice.

**Note**: We deliberately do **not** ship the full token collection (hundreds of MB). Tokens are fetched on-demand only for the monsters you actually use. This keeps the repo small and fast to clone.

Built with Grok — May 2026
## Documentation & Process

- [Development Process](docs/Development_Process.md) — Important lessons about keeping the developer experience consistent with what users get when they clone the repo.
- [Utilities & Data Regeneration](utilities/README.md)
- [Contributing](CONTRIBUTING.md)
