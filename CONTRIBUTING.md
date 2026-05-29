# Contributing

Thank you for your interest in the D&D Encounter Manager!

## Core Principle

**The developer experience on your machine must match the experience of someone who clones this repository.**

This is the most important rule we've learned. Please read [docs/Development_Process.md](docs/Development_Process.md) before making significant changes.

## Quick Start for Contributors

1. Clone the repo
2. Run `uv sync --dev`
3. Run `uv run python run_ui.py`

The committed `data/srd/monsters.json` is the data you will work with by default.

## Making Changes

- Follow the process documented in [docs/Development_Process.md](docs/Development_Process.md).
- Before pushing or asking someone to test on another machine:
  - Make sure all runtime-affecting changes (especially anything in `utilities/`, the renderer, or data processing) are committed.
  - Verify behavior in a fresh clone when possible.

### Running Tests Locally

GUI tests are configured to run **headless by default** (no windows appear).

```powershell
# Normal tests (fast)
uv run pytest -q

# GUI tests only (headless)
uv run pytest tests/unit/ui/ -q
```

See the main [README.md](README.md) for more details and Windows PowerShell examples.

## Bestiary / Data Changes

See the "Bestiary Data Policy" section in [docs/Development_Process.md](docs/Development_Process.md).

The `monsters.json` file is the canonical data. Improvements to the importer should eventually result in an updated committed JSON.

## Questions?

Feel free to open an issue. We're still evolving the project and welcome feedback on the architecture and process.

## Optional: Using `just`

If you prefer shorter commands, you can optionally install [`just`](https://github.com/casey/just) and use it instead of typing full `uv run` commands.

Example commands:
- `just run` — Run the application
- `just test` — Run all tests (non-UI)
- `just test-ui` — Run only GUI tests (headless)
- `just sync` — Sync dependencies
- `just validate` — Check bestiary data quality
- `just check` — Run quick validation + UI tests

**Note:** `just` is completely optional. You can always use the normal `uv run` commands instead (recommended for new contributors). See the main README for the direct equivalents.
