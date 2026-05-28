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

## Bestiary / Data Changes

See the "Bestiary Data Policy" section in [docs/Development_Process.md](docs/Development_Process.md).

The `monsters.json` file is the canonical data. Improvements to the importer should eventually result in an updated committed JSON.

## Questions?

Feel free to open an issue. We're still evolving the project and welcome feedback on the architecture and process.
