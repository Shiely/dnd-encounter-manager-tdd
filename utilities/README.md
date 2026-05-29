# Utilities

This folder contains helper scripts for development and data management.

**Important:** See [docs/Development_Process.md](../docs/Development_Process.md) for the project's process rules. The core principle is that the developer experience must match the experience of someone cloning the repository.

## Bestiary Data

The file `data/srd/monsters.json` is the **canonical bestiary** used by the application.

- It is committed so that new users and fresh clones get working data immediately.
- Users should **not** need to run these importer scripts just to use the app.
- When the importer pipeline is meaningfully improved, the file should be regenerated and committed.

## Available Scripts

### `import_full_bestiary.py`

The recommended script for generating the full bestiary with MPMM priority.

```bash
uv run python utilities/import_full_bestiary.py
```

This produces `data/srd/monsters.json` with the largest possible set of monsters while preferring MPMM versions where available.

### `import_srd_monsters.py`

Generates a cleaner but smaller bestiary focused on SRD + VGM-style sources.

```bash
uv run python utilities/import_srd_monsters.py
```

### `import_mpmm_monsters.py`

Focused importer for MPMM content.

```bash
uv run python utilities/import_mpmm_monsters.py
```

### `import_combined_monsters.py`

Utility for combining multiple sources.

## Regenerating the Bestiary

1. Ensure you have the 5eTools source data (the scripts will attempt to clone it if missing).
2. Run the desired importer script.
3. Review the output in `data/srd/monsters.json` (especially complex monsters like Abjurer, spellcasters, etc.).
4. Commit the new `monsters.json` with a clear message.

See `docs/Development_Process.md` for guidelines on when to update the committed bestiary.

## Notes

- These scripts are primarily for maintainers.
- The committed `monsters.json` is what most contributors and users will work with.
- Improvements to the importer logic should be committed promptly so that future regenerations benefit everyone.

## Optional: Using `just`

For convenience, a `justfile` is provided with common commands:

```bash
just run          # Run the application
just test         # Run all tests (non-UI)
just test-ui      # Run only GUI tests (headless by default)
just sync         # Sync dependencies
just validate     # Validate bestiary data quality
just check        # Run quick validation checks
```

**Direct equivalents (no `just` needed):**

```powershell
uv run pytest -q                    # Normal tests
uv run pytest tests/unit/ui/ -q     # GUI tests (headless)
```

`just` is **completely optional**. Direct `uv run` commands work on any fresh clone.

To install `just`, see: https://github.com/casey/just#installation
